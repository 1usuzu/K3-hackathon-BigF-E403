from typing import List, Optional
from sqlalchemy.orm import Session

from backend.app.models.document import LearningDocument, DocumentVersion, ContentBlock, ContentChunk, GlossaryTerm
from backend.app.models.job import ProcessingJob
from backend.app.schemas.enums import JobStatus
from backend.app.services.semantic_chunking.chunk_dto import SemanticChunkData
from backend.app.services.semantic_chunking.chunker import SemanticChunker

class SemanticChunkingPipeline:
    def __init__(self, db: Session, chunker: Optional[SemanticChunker] = None):
        self.db = db
        self.chunker = chunker or SemanticChunker()

    async def execute_for_version(self, document_version_id: str) -> List[ContentChunk]:
        # 1. Fetch Document Version & Document
        doc_ver = self.db.query(DocumentVersion).filter(DocumentVersion.id == document_version_id).first()
        if not doc_ver:
            raise ValueError(f"DocumentVersion '{document_version_id}' not found.")

        doc = self.db.query(LearningDocument).filter(LearningDocument.id == doc_ver.document_id).first()
        if not doc:
            raise ValueError(f"LearningDocument for version '{document_version_id}' not found.")

        # 2. Fetch Content Blocks sorted by sequence_number
        blocks = self.db.query(ContentBlock).filter(
            ContentBlock.document_version_id == document_version_id
        ).order_by(ContentBlock.sequence_number.asc()).all()

        # 3. Fetch Glossary Terms for Course
        glossary_terms_db = self.db.query(GlossaryTerm).filter(
            GlossaryTerm.course_id == doc.course_id
        ).all()
        known_glossary = [gt.term for gt in glossary_terms_db]

        # 4. Generate Semantic Chunks DTO
        chunks_data = self.chunker.chunk_blocks(
            blocks=blocks,
            document_id=doc.id,
            document_version_id=doc_ver.id,
            known_glossary_terms=known_glossary
        )

        # 5. IDEMPOTENCY Check: Delete existing ContentChunks for this version
        self.db.query(ContentChunk).filter(ContentChunk.document_version_id == document_version_id).delete()
        self.db.commit()

        # 6. Save ContentChunk records to DB
        db_chunks: List[ContentChunk] = []
        for cdata in chunks_data:
            has_form = "formula" in cdata.content_types
            has_cd = "code" in cdata.content_types
            
            c_db = ContentChunk(
                document_version_id=doc_ver.id,
                chunk_index=cdata.sequence_number,
                text_content=cdata.content,
                has_formulas=has_form,
                has_code=has_cd,
                metadata_json={
                    "title": cdata.title,
                    "lesson_id": cdata.lesson_id,
                    "content_block_ids": cdata.content_block_ids,
                    "content_types": cdata.content_types,
                    "token_estimate": cdata.token_estimate,
                    "overlap_summary": cdata.overlap_summary,
                    "glossary_terms": cdata.glossary_terms,
                    "source_references": cdata.source_references,
                    "checksum": cdata.checksum
                }
            )
            db_chunks.append(c_db)

        self.db.add_all(db_chunks)
        self.db.commit()

        # 7. Update ProcessingJob progress
        job = self.db.query(ProcessingJob).filter(
            ProcessingJob.document_version_id == document_version_id
        ).first()

        if job:
            job.status = JobStatus.PROCESSING.value
            job.progress_percentage = 50
            job.last_completed_step = "semantic_chunking"
            if job.checkpoint_data:
                job.checkpoint_data["chunks_count"] = len(db_chunks)
            else:
                job.checkpoint_data = {"chunks_count": len(db_chunks)}
            self.db.commit()

        return db_chunks
