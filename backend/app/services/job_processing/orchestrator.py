import asyncio
import logging
from typing import List, Optional, Dict, Any, Tuple
from sqlalchemy.orm import Session

from backend.app.models.job import ProcessingJob, ProcessingTask
from backend.app.models.document import DocumentVersion, ContentChunk
from backend.app.schemas.enums import JobStatus, TaskStatus
from backend.app.services.model_gateway.security import LogRedactor
from backend.app.services.job_processing.events import ProgressEvent, global_event_publisher
from backend.app.services.job_processing.worker import BaseChunkWorker, MockChunkWorker
from backend.app.services.content_extraction.pipeline import ContentExtractionPipeline
from backend.app.services.semantic_chunking.pipeline import SemanticChunkingPipeline

logger = logging.getLogger("JobOrchestrator")

class JobCancelledException(Exception):
    pass

class JobOrchestrator:
    def __init__(
        self,
        db: Session,
        worker: Optional[BaseChunkWorker] = None,
        storage: Optional[Any] = None,
        max_concurrency: int = 4,
        max_retries: int = 3,
        task_timeout_sec: float = 5.0,
        retry_backoff_base_sec: float = 0.1
    ):
        self.db = db
        self.worker = worker or MockChunkWorker()
        self.storage = storage
        self.max_concurrency = max_concurrency
        self.max_retries = max_retries
        self.task_timeout_sec = task_timeout_sec
        self.retry_backoff_base_sec = retry_backoff_base_sec
        self._cancelled_jobs: set = set()

    def cancel_job(self, job_id: str):
        self._cancelled_jobs.add(job_id)
        job = self.db.query(ProcessingJob).filter(ProcessingJob.id == job_id).first()
        if job:
            job.status = JobStatus.CANCELLED.value
            self.db.commit()
            self._notify_progress(job, "Job was cancelled by request.")

    def _notify_progress(self, job: ProcessingJob, message: str = "", completed: int = 0, total: int = 0):
        event = ProgressEvent(
            job_id=job.id,
            status=JobStatus(job.status),
            progress_percentage=job.progress_percentage,
            completed_tasks=completed,
            total_tasks=total,
            message=LogRedactor.redact_text(message)
        )
        global_event_publisher.publish(event)

    async def run_pipeline_for_job(self, job_id: str) -> ProcessingJob:
        job = self.db.query(ProcessingJob).filter(ProcessingJob.id == job_id).first()
        if not job:
            raise ValueError(f"ProcessingJob '{job_id}' not found.")

        if job_id in self._cancelled_jobs or job.status == JobStatus.CANCELLED.value:
            job.status = JobStatus.CANCELLED.value
            self.db.commit()
            return job

        doc_ver_id = job.document_version_id
        if not doc_ver_id:
            job.status = JobStatus.FAILED.value
            job.error_message = "No document_version_id associated with job."
            self.db.commit()
            return job

        try:
            # Phase 1: EXTRACTING
            if job.status in [JobStatus.PENDING.value, JobStatus.EXTRACTING.value]:
                job.status = JobStatus.EXTRACTING.value
                job.progress_percentage = 15
                self.db.commit()
                self._notify_progress(job, "Extracting content blocks...")

                extraction_pipeline = ContentExtractionPipeline(db=self.db, storage=self.storage)
                await extraction_pipeline.execute_for_version(doc_ver_id)

            if job_id in self._cancelled_jobs:
                raise JobCancelledException("Cancelled during extraction")

            # Phase 2: CHUNKING
            if job.status in [JobStatus.EXTRACTING.value, JobStatus.CHUNKING.value]:
                job.status = JobStatus.CHUNKING.value
                job.progress_percentage = 35
                self.db.commit()
                self._notify_progress(job, "Creating semantic chunks...")

                chunking_pipeline = SemanticChunkingPipeline(db=self.db)
                await chunking_pipeline.execute_for_version(doc_ver_id)

            if job_id in self._cancelled_jobs:
                raise JobCancelledException("Cancelled during chunking")

            # Phase 3: PROCESSING (Chunk Worker Queue with Concurrency Limit & Retry)
            job.status = JobStatus.PROCESSING.value
            job.progress_percentage = 50
            self.db.commit()
            self._notify_progress(job, "Processing chunks in parallel worker queue...")

            chunks = self.db.query(ContentChunk).filter(
                ContentChunk.document_version_id == doc_ver_id
            ).order_by(ContentChunk.chunk_index.asc()).all()

            if not chunks:
                job.status = JobStatus.COMPLETED.value
                job.progress_percentage = 100
                self.db.commit()
                return job

            # Execute parallel task queue with concurrency semaphore
            completed_count, failed_count, skipped_count = await self._process_chunks_parallel(job, chunks)

            if job_id in self._cancelled_jobs:
                raise JobCancelledException("Cancelled during processing")

            # Phase 4: MERGING
            job.status = JobStatus.MERGING.value
            job.progress_percentage = 90
            self.db.commit()
            self._notify_progress(job, "Merging processing results...", completed_count, len(chunks))

            # Phase 5: Final Job Status Decision (Partial Completion Support - Req 1 & 2)
            total_chunks = len(chunks)
            if failed_count == 0:
                job.status = JobStatus.COMPLETED.value
                job.progress_percentage = 100
            elif completed_count > 0 or skipped_count > 0:
                job.status = JobStatus.PARTIALLY_COMPLETED.value
                job.progress_percentage = 100
            else:
                job.status = JobStatus.FAILED.value
                job.progress_percentage = 0

            job.checkpoint_data = {
                "total_chunks": total_chunks,
                "completed_chunks": completed_count,
                "failed_chunks": failed_count,
                "skipped_chunks": skipped_count
            }
            self.db.commit()
            self._notify_progress(job, f"Job finished with status: {job.status}", completed_count, total_chunks)
            return job

        except JobCancelledException:
            job.status = JobStatus.CANCELLED.value
            self.db.commit()
            self._notify_progress(job, "Job execution cancelled.")
            return job
        except Exception as e:
            job.status = JobStatus.FAILED.value
            job.error_message = LogRedactor.redact_text(str(e))
            self.db.commit()
            self._notify_progress(job, f"Job execution failed: {job.error_message}")
            return job

    async def _process_chunks_parallel(
        self,
        job: ProcessingJob,
        chunks: List[ContentChunk]
    ) -> Tuple[int, int, int]:
        semaphore = asyncio.Semaphore(self.max_concurrency)
        total_chunks = len(chunks)
        completed_counter = 0
        failed_counter = 0
        skipped_counter = 0

        async def worker_task_wrapper(chunk: ContentChunk):
            nonlocal completed_counter, failed_counter, skipped_counter
            async with semaphore:
                if job.id in self._cancelled_jobs:
                    return

                # Check Idempotency: Skip already completed tasks if chunk checksum is unchanged
                existing_task = self.db.query(ProcessingTask).filter(
                    ProcessingTask.job_id == job.id,
                    ProcessingTask.step_order == chunk.chunk_index
                ).first()

                chunk_meta = chunk.metadata_json or {}
                chunk_checksum = chunk_meta.get("checksum", "")

                if existing_task and existing_task.status == TaskStatus.COMPLETED.value:
                    task_meta = existing_task.output_result or {}
                    if task_meta.get("checksum") == chunk_checksum:
                        existing_task.status = TaskStatus.SKIPPED.value
                        self.db.commit()
                        skipped_counter += 1
                        return

                if not existing_task:
                    task = ProcessingTask(
                        job_id=job.id,
                        task_name=f"process_chunk_{chunk.chunk_index}",
                        status=TaskStatus.PENDING.value,
                        step_order=chunk.chunk_index,
                        input_payload={"chunk_id": chunk.id, "checksum": chunk_checksum}
                    )
                    self.db.add(task)
                    self.db.commit()
                    self.db.refresh(task)
                else:
                    task = existing_task

                # Task execution loop with Exponential Backoff Retries & Timeout
                success = False
                task.status = TaskStatus.RUNNING.value
                self.db.commit()

                for attempt in range(1 + self.max_retries):
                    if job.id in self._cancelled_jobs:
                        return

                    try:
                        # Enforce Task Timeout (Req 8)
                        result = await asyncio.wait_for(
                            self.worker.process_chunk(chunk),
                            timeout=self.task_timeout_sec
                        )
                        task.status = TaskStatus.COMPLETED.value
                        task.output_result = {**result, "checksum": chunk_checksum}
                        self.db.commit()
                        completed_counter += 1
                        success = True
                        break
                    except (asyncio.TimeoutError, Exception) as err:
                        logger.warning(f"Task {task.id} (chunk {chunk.chunk_index}) attempt {attempt+1} failed: {type(err).__name__}")
                        task.error_details = LogRedactor.redact_text(str(err))
                        
                        if attempt < self.max_retries:
                            task.status = TaskStatus.RETRYING.value
                            self.db.commit()
                            await asyncio.sleep(self.retry_backoff_base_sec * (2 ** attempt))
                        else:
                            # Dead-Letter State after max_retries (Req 3)
                            task.status = TaskStatus.FAILED.value
                            self.db.commit()
                            failed_counter += 1

                # Update job progress percentage incrementally
                done_tasks = completed_counter + failed_counter + skipped_counter
                job.progress_percentage = 50 + int((done_tasks / total_chunks) * 40)
                self.db.commit()
                self._notify_progress(job, f"Processed chunk {chunk.chunk_index}/{total_chunks}", done_tasks, total_chunks)

        tasks = [worker_task_wrapper(c) for c in chunks]
        await asyncio.gather(*tasks, return_exceptions=True)

        return completed_counter, failed_counter, skipped_counter

    async def resume_job(self, job_id: str) -> ProcessingJob:
        job = self.db.query(ProcessingJob).filter(ProcessingJob.id == job_id).first()
        if not job:
            raise ValueError(f"Job '{job_id}' not found.")

        if job.id in self._cancelled_jobs:
            self._cancelled_jobs.remove(job.id)

        job.status = JobStatus.PENDING.value
        job.error_message = None
        self.db.commit()

        return await self.run_pipeline_for_job(job_id)
