from typing import Dict, Any
from sqlalchemy.orm import Session

from backend.app.models.document import ContentChunk
from backend.app.services.job_processing.worker import BaseChunkWorker
from backend.app.services.flashcard_generation.generator_service import FlashcardGeneratorService
from backend.app.services.flashcard_generation.repository import FlashcardRepository

class FlashcardWorkerHandler(BaseChunkWorker):
    def __init__(
        self,
        db: Session,
        generator_service: FlashcardGeneratorService
    ):
        self.db = db
        self.generator_service = generator_service
        self.repository = FlashcardRepository(db)

    async def process_chunk(self, chunk: ContentChunk) -> Dict[str, Any]:
        # 1. Generate Flashcards for Chunk (Single chunk per worker task execution)
        cards_schema = await self.generator_service.generate_flashcards_for_chunk(chunk)

        # 2. Persist Flashcards in Database
        saved_db_cards = self.repository.save_flashcards_for_chunk(chunk, cards_schema)

        return {
            "chunk_id": chunk.id,
            "flashcards_generated_count": len(saved_db_cards),
            "flashcard_ids": [fc.id for fc in saved_db_cards]
        }
