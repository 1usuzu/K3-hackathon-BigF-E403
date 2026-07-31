from typing import List, Optional
from sqlalchemy.orm import Session
from backend.app.models.flashcard import Flashcard
from backend.app.models.document import ContentChunk, DocumentVersion, LearningDocument
from backend.app.services.flashcard_generation.schemas import FlashcardItemSchema

class FlashcardRepository:
    def __init__(self, db: Session):
        self.db = db

    def save_flashcards_for_chunk(
        self,
        chunk: ContentChunk,
        cards: List[FlashcardItemSchema],
        course_id: Optional[str] = None,
        lesson_id: Optional[str] = None
    ) -> List[Flashcard]:
        db_flashcards: List[Flashcard] = []

        chunk_meta = chunk.metadata_json or {}
        target_lesson_id = lesson_id or chunk_meta.get("lesson_id")
        target_course_id = course_id or chunk_meta.get("course_id")

        if not target_course_id:
            # Query Document to get course_id if not present in metadata
            doc_ver = self.db.query(DocumentVersion).filter(DocumentVersion.id == chunk.document_version_id).first()
            if doc_ver:
                doc = self.db.query(LearningDocument).filter(LearningDocument.id == doc_ver.document_id).first()
                if doc:
                    target_course_id = doc.course_id

        if not target_course_id:
            target_course_id = "default-course"

        for cschema in cards:
            fc = Flashcard(
                course_id=target_course_id,
                lesson_id=target_lesson_id,
                content_chunk_id=chunk.id,
                question=cschema.front,
                answer=cschema.back,
                difficulty=cschema.difficulty,
                options_json={
                    "type": cschema.type,
                    "explanation": cschema.explanation,
                    "blooms_level": cschema.blooms_level,
                    "source_references": cschema.source_references,
                    "quality_score": cschema.quality_score,
                    "glossary_terms": cschema.glossary_terms
                },
                tags_json={"tags": cschema.tags}
            )
            db_flashcards.append(fc)

        self.db.add_all(db_flashcards)
        self.db.commit()

        for fc in db_flashcards:
            self.db.refresh(fc)

        return db_flashcards
