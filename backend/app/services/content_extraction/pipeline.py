import os
from typing import List, Optional
from sqlalchemy.orm import Session

from backend.app.models.document import LearningDocument, DocumentVersion, ContentBlock
from backend.app.models.job import ProcessingJob
from backend.app.schemas.enums import JobStatus
from backend.app.services.storage import StorageProvider, LocalStorageProvider
from backend.app.services.content_extraction.extractors.pdf_extractor import PDFContentExtractor
from backend.app.services.content_extraction.extractors.pptx_extractor import PPTXContentExtractor
from backend.app.services.content_extraction.extractors.txt_md_extractor import TextMarkdownContentExtractor

class ContentExtractionPipeline:
    def __init__(self, db: Session, storage: Optional[StorageProvider] = None):
        self.db = db
        self.storage = storage or LocalStorageProvider()
        self.pdf_extractor = PDFContentExtractor()
        self.pptx_extractor = PPTXContentExtractor()
        self.txt_md_extractor = TextMarkdownContentExtractor()

    async def execute_for_version(self, document_version_id: str) -> List[ContentBlock]:
        # 1. Fetch Document Version & Document
        doc_ver = self.db.query(DocumentVersion).filter(DocumentVersion.id == document_version_id).first()
        if not doc_ver:
            raise ValueError(f"DocumentVersion '{document_version_id}' not found.")

        doc = self.db.query(LearningDocument).filter(LearningDocument.id == doc_ver.document_id).first()
        if not doc:
            raise ValueError(f"LearningDocument for version '{document_version_id}' not found.")

        # 2. Fetch associated ProcessingJob
        job = self.db.query(ProcessingJob).filter(
            ProcessingJob.document_version_id == document_version_id
        ).first()

        if job:
            job.status = JobStatus.EXTRACTING.value
            job.progress_percentage = 20
            job.last_completed_step = "started_content_extraction"
            self.db.commit()

        try:
            # 3. Read file bytes from storage
            file_bytes = await self.storage.get_file(doc.file_path)

            # 4. Select Extractor based on MIME type or file extension
            mime = doc.file_type.lower()
            if "pdf" in mime or doc.file_path.endswith(".pdf"):
                extracted_data = await self.pdf_extractor.extract_blocks(file_bytes, doc.id, doc_ver.id, doc.lesson_id)
            elif "presentation" in mime or "powerpoint" in mime or doc.file_path.endswith((".pptx", ".ppt")):
                extracted_data = await self.pptx_extractor.extract_blocks(file_bytes, doc.id, doc_ver.id, doc.lesson_id)
            else:
                extracted_data = await self.txt_md_extractor.extract_blocks(file_bytes, doc.id, doc_ver.id, doc.lesson_id)

            # 5. IDEMPOTENCY Check: Remove existing ContentBlocks for this version before inserting
            self.db.query(ContentBlock).filter(ContentBlock.document_version_id == document_version_id).delete()
            self.db.commit()

            # 6. Save new ContentBlock records to DB
            db_blocks: List[ContentBlock] = []
            for block_item in extracted_data:
                cb = ContentBlock(
                    document_id=doc.id,
                    document_version_id=doc_ver.id,
                    lesson_id=doc.lesson_id,
                    block_type=block_item.block_type,
                    raw_content=block_item.raw_content,
                    normalized_content=block_item.normalized_content,
                    language=block_item.language,
                    page_number=block_item.page_number,
                    slide_number=block_item.slide_number,
                    sequence_number=block_item.sequence_number,
                    extraction_confidence=block_item.extraction_confidence,
                    source_reference=block_item.source_reference,
                    metadata_json=block_item.metadata
                )
                db_blocks.append(cb)

            self.db.add_all(db_blocks)
            self.db.commit()

            # 7. Update ProcessingJob step
            if job:
                job.status = JobStatus.CHUNKING.value
                job.progress_percentage = 35
                job.last_completed_step = "content_extraction"
                job.checkpoint_data = {
                    "extracted_blocks_count": len(db_blocks),
                    "document_id": doc.id,
                    "document_version_id": doc_ver.id
                }
                self.db.commit()

            return db_blocks
        except Exception as e:
            if job:
                job.status = JobStatus.FAILED.value
                job.error_message = str(e)
                self.db.commit()
            raise e
