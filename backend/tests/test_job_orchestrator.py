import pytest
import os
import shutil
import asyncio
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from backend.app.core.database import Base
from backend.app.models.user import User
from backend.app.models.course import Course
from backend.app.models.document import LearningDocument, DocumentVersion, ContentChunk
from backend.app.models.job import ProcessingJob, ProcessingTask
from backend.app.schemas.enums import JobStatus, TaskStatus
from backend.app.services.storage.local_storage import LocalStorageProvider
from backend.app.services.job_processing import (
    JobOrchestrator, MockChunkWorker, ProgressEvent, global_event_publisher
)

TEST_DB_URL = "sqlite:///:memory:"
TEST_UPLOAD_DIR = "./test_orchestrator_storage"

engine = create_engine(
    TEST_DB_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(autouse=True)
def setup_test_environment():
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()

    course = Course(id="c-orch", code="COMP2010", title="AI Orchestration")
    doc = LearningDocument(id="doc-orch", course_id="c-orch", title="slide.md", file_type="text/markdown", file_path="slide.md")
    doc_ver = DocumentVersion(id="docver-orch", document_id="doc-orch", version_number=1, file_path="slide.md")
    job = ProcessingJob(id="job-orch", course_id="c-orch", document_version_id="docver-orch", status=JobStatus.PENDING.value)

    db.add_all([course, doc, doc_ver, job])
    db.commit()

    # Save mock file for extraction
    storage = LocalStorageProvider(base_dir=TEST_UPLOAD_DIR)
    asyncio.run(storage.save_file("# Day 01 Lecture Notes\n\nSample content for orchestrator test.".encode("utf-8"), "slide.md"))

    db.close()
    yield
    Base.metadata.drop_all(bind=engine)
    if os.path.exists(TEST_UPLOAD_DIR):
        shutil.rmtree(TEST_UPLOAD_DIR)

@pytest.mark.asyncio
async def test_full_job_pipeline_execution_and_events():
    db = TestingSessionLocal()
    events_received = []

    def on_event(ev: ProgressEvent):
        events_received.append(ev)

    global_event_publisher.subscribe(on_event)

    storage = LocalStorageProvider(base_dir=TEST_UPLOAD_DIR)
    orchestrator = JobOrchestrator(db=db, storage=storage, max_concurrency=2)
    job = await orchestrator.run_pipeline_for_job("job-orch")

    print("JOB ERROR:", job.error_message)
    assert job.status == JobStatus.COMPLETED.value
    assert job.progress_percentage == 100
    assert len(events_received) > 0
    db.close()

@pytest.mark.asyncio
async def test_single_chunk_failure_partial_completion():
    db = TestingSessionLocal()
    
    # Pre-insert chunks
    chunk1 = ContentChunk(id="chk-1", document_version_id="docver-orch", chunk_index=1, text_content="Chunk 1", metadata_json={"checksum": "c1"})
    chunk2 = ContentChunk(id="chk-2", document_version_id="docver-orch", chunk_index=2, text_content="Chunk 2", metadata_json={"checksum": "c2"})
    db.add_all([chunk1, chunk2])
    db.commit()

    # Custom worker where chunk 2 fails
    class SelectiveFailureWorker(MockChunkWorker):
        async def process_chunk(self, chunk: ContentChunk):
            if chunk.id == "chk-2":
                raise RuntimeError("Simulated failure for chunk 2")
            return await super().process_chunk(chunk)

    worker = SelectiveFailureWorker()
    orchestrator = JobOrchestrator(db=db, worker=worker, max_retries=1, retry_backoff_base_sec=0.01)
    
    # Set job status to PROCESSING to test worker queue directly
    job_db = db.query(ProcessingJob).filter(ProcessingJob.id == "job-orch").first()
    job_db.status = JobStatus.PROCESSING.value
    db.commit()

    job = await orchestrator.run_pipeline_for_job("job-orch")

    # Partial completion verification (Req 1 & 2: single chunk failure results in PARTIALLY_COMPLETED)
    assert job.status == JobStatus.PARTIALLY_COMPLETED.value
    assert job.checkpoint_data["completed_chunks"] == 1
    assert job.checkpoint_data["failed_chunks"] == 1
    db.close()

@pytest.mark.asyncio
async def test_worker_crash_and_max_retries():
    db = TestingSessionLocal()
    
    chunk = ContentChunk(id="chk-crash", document_version_id="docver-orch", chunk_index=1, text_content="Crash Chunk", metadata_json={"checksum": "cc"})
    db.add(chunk)
    db.commit()

    worker = MockChunkWorker()
    worker.should_crash = True  # Worker crash simulation (Req 7)

    orchestrator = JobOrchestrator(db=db, worker=worker, max_retries=2, retry_backoff_base_sec=0.01)

    job_db = db.query(ProcessingJob).filter(ProcessingJob.id == "job-orch").first()
    job_db.status = JobStatus.PROCESSING.value
    db.commit()

    job = await orchestrator.run_pipeline_for_job("job-orch")

    assert job.status == JobStatus.FAILED.value
    
    # Verify task retried max_retries times and ended in TaskStatus.FAILED (Dead-letter state - Req 3)
    task = db.query(ProcessingTask).filter(ProcessingTask.job_id == "job-orch").first()
    assert task.status == TaskStatus.FAILED.value
    assert "Worker crashed" in task.error_details
    db.close()

@pytest.mark.asyncio
async def test_task_timeout():
    db = TestingSessionLocal()

    chunk = ContentChunk(id="chk-timeout", document_version_id="docver-orch", chunk_index=1, text_content="Timeout Chunk", metadata_json={"checksum": "ct"})
    db.add(chunk)
    db.commit()

    worker = MockChunkWorker()
    worker.should_timeout = True  # Timeout simulation (Req 8)

    orchestrator = JobOrchestrator(db=db, worker=worker, max_retries=0, task_timeout_sec=0.05)

    job_db = db.query(ProcessingJob).filter(ProcessingJob.id == "job-orch").first()
    job_db.status = JobStatus.PROCESSING.value
    db.commit()

    job = await orchestrator.run_pipeline_for_job("job-orch")

    assert job.status == JobStatus.FAILED.value
    task = db.query(ProcessingTask).filter(ProcessingTask.job_id == "job-orch").first()
    assert task.status == TaskStatus.FAILED.value
    db.close()

@pytest.mark.asyncio
async def test_job_cancellation():
    db = TestingSessionLocal()
    orchestrator = JobOrchestrator(db=db)

    orchestrator.cancel_job("job-orch")

    job = db.query(ProcessingJob).filter(ProcessingJob.id == "job-orch").first()
    assert job.status == JobStatus.CANCELLED.value
    db.close()

@pytest.mark.asyncio
async def test_job_resume_and_duplicate_task_idempotency():
    db = TestingSessionLocal()

    chunk = ContentChunk(id="chk-idempotent", document_version_id="docver-orch", chunk_index=1, text_content="Idempotent Chunk", metadata_json={"checksum": "chksum-123"})
    db.add(chunk)
    db.commit()

    # Pre-create completed task with SAME checksum (Req 10)
    prev_task = ProcessingTask(
        job_id="job-orch",
        task_name="process_chunk_1",
        status=TaskStatus.COMPLETED.value,
        step_order=1,
        output_result={"checksum": "chksum-123", "processed": True}
    )
    db.add(prev_task)
    db.commit()

    orchestrator = JobOrchestrator(db=db)

    # Set job status to PROCESSING to test worker queue resume directly
    job_db = db.query(ProcessingJob).filter(ProcessingJob.id == "job-orch").first()
    job_db.status = JobStatus.PROCESSING.value
    db.commit()

    # Resume Job (Req 9)
    job = await orchestrator.run_pipeline_for_job("job-orch")

    # Task with unchanged checksum should be SKIPPED
    db.refresh(prev_task)
    assert prev_task.status == TaskStatus.SKIPPED.value
    assert job.status == JobStatus.COMPLETED.value
    assert job.checkpoint_data["skipped_chunks"] == 1
    db.close()
