import hashlib
import re
from typing import List, Set, Optional
from backend.app.services.flashcard_generation.schemas import FlashcardItemSchema

class FlashcardDeduplicator:
    @staticmethod
    def normalize_text(text: str) -> str:
        # Strip punctuation, extra spaces, and lowercase for hash comparison
        cleaned = re.sub(r"[^\w\s]", "", text.lower())
        return " ".join(cleaned.split())

    @staticmethod
    def compute_hash(front_text: str) -> str:
        norm = FlashcardDeduplicator.normalize_text(front_text)
        return hashlib.sha256(norm.encode("utf-8")).hexdigest()

    @classmethod
    def filter_duplicates(
        cls,
        candidate_cards: List[FlashcardItemSchema],
        existing_hashes: Optional[Set[str]] = None
    ) -> List[FlashcardItemSchema]:
        seen_hashes = existing_hashes.copy() if existing_hashes else set()
        unique_cards: List[FlashcardItemSchema] = []

        for card in candidate_cards:
            card_hash = cls.compute_hash(card.front)
            if card_hash in seen_hashes:
                continue
            
            # Substring / overlap check among generated batch
            is_near_duplicate = False
            norm_front = cls.normalize_text(card.front)
            for uc in unique_cards:
                uc_norm = cls.normalize_text(uc.front)
                if norm_front == uc_norm or (len(norm_front) > 20 and norm_front in uc_norm):
                    is_near_duplicate = True
                    break

            if not is_near_duplicate:
                seen_hashes.add(card_hash)
                unique_cards.append(card)

        return unique_cards
