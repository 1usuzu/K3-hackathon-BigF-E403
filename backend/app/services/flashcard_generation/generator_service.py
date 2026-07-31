from typing import List, Dict, Optional
from sqlalchemy.orm import Session

from backend.app.models.document import ContentChunk, LearningDocument, DocumentVersion
from backend.app.services.model_gateway import ModelGateway, ModelTier
from backend.app.services.glossary_protection import GlossaryMergeService
from backend.app.services.flashcard_generation.schemas import FlashcardListSchema, FlashcardItemSchema
from backend.app.services.flashcard_generation.prompt_template import FlashcardPromptTemplate
from backend.app.services.flashcard_generation.validator import FlashcardValidator
from backend.app.services.flashcard_generation.deduplication import FlashcardDeduplicator

class FlashcardGeneratorService:
    def __init__(
        self,
        gateway: ModelGateway,
        db: Optional[Session] = None,
        max_retries: int = 2
    ):
        self.gateway = gateway
        self.db = db
        self.max_retries = max_retries

    async def generate_flashcards_for_chunk(
        self,
        chunk: ContentChunk,
        course_id: Optional[str] = None
    ) -> List[FlashcardItemSchema]:
        # 1. Obtain Protected Glossary Terms
        protected_glossary = GlossaryMergeService.get_merged_glossary_for_course(
            course_id=course_id,
            db=self.db,
            document_text=chunk.text_content
        )

        # 2. Build Prompt Template
        prompt = FlashcardPromptTemplate.build_prompt(chunk, protected_glossary)

        # 3. Call Model Gateway with Structured Output (Req 10 & 11)
        raw_response = await self.gateway.generate_structured(
            prompt=prompt,
            response_schema=FlashcardListSchema,
            tier=ModelTier.PRO_MODEL
        )

        parsed_obj: Optional[FlashcardListSchema] = raw_response.structured_data
        cards: List[FlashcardItemSchema] = parsed_obj.flashcards if parsed_obj else []

        # 4. Validate & Quality Filter (Req 13, 8 & 9)
        valid_cards = FlashcardValidator.validate_and_filter(
            cards=cards,
            protected_glossary=protected_glossary,
            min_quality_score=0.70
        )

        # 5. Deduplicate Cards (Req 4 & 12)
        unique_cards = FlashcardDeduplicator.filter_duplicates(valid_cards)

        return unique_cards
