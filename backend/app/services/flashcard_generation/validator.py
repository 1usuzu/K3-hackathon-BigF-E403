from typing import List, Dict, Tuple
from backend.app.services.flashcard_generation.schemas import FlashcardItemSchema
from backend.app.services.glossary_protection import GlossaryOutputValidator

class FlashcardValidator:
    @staticmethod
    def validate_and_filter(
        cards: List[FlashcardItemSchema],
        protected_glossary: Dict[str, str],
        min_quality_score: float = 0.70
    ) -> List[FlashcardItemSchema]:
        valid_cards: List[FlashcardItemSchema] = []

        for card in cards:
            # 1. Quality Filter Check (Req 13)
            if card.quality_score < min_quality_score:
                continue

            # 2. Source Reference Check (Req 8 & 9)
            if not card.source_references or len(card.source_references) == 0:
                continue

            # 3. Glossary & Identifier Protection Validation (Req 5 & 6)
            combined_text = f"{card.front}\n{card.back}\n{card.explanation}"
            glossary_val = GlossaryOutputValidator.validate_output(combined_text, protected_glossary)
            
            if not glossary_val.is_valid:
                # Card failed glossary protection check (translated forbidden terms or altered code identifier)
                continue

            valid_cards.append(card)

        return valid_cards
