from typing import List, Tuple
from backend.app.services.tutor_agent.schemas import CitationSchema
from backend.app.services.vector_retrieval.dto import SearchResultItem
from backend.app.services.guardrails.classifier import SecurityEventPublisher, SecurityEvent

class GuardrailCitationValidator:
    @staticmethod
    def validate_citations_against_context(
        citations: List[CitationSchema],
        retrieved_items: List[SearchResultItem]
    ) -> Tuple[List[CitationSchema], int]:
        """
        Verifies that returned citations actually exist in retrieved context.
        Rejects fake citations and emits security event if fake citations detected.
        """
        valid_chunk_ids = {item.entity_id for item in retrieved_items}
        valid_citations: List[CitationSchema] = []
        fake_citations_count = 0

        for cit in citations:
            # If citation claims a chunk_id, verify it exists in valid_chunk_ids
            if cit.chunk_id and cit.chunk_id not in valid_chunk_ids:
                fake_citations_count += 1
                continue
            
            valid_citations.append(cit)

        if fake_citations_count > 0:
            SecurityEventPublisher.publish(
                SecurityEvent(
                    event_type="FAKE_CITATION",
                    source="guardrail_citation_validator",
                    details=f"Detected and rejected {fake_citations_count} fake citations."
                )
            )

        return valid_citations, fake_citations_count
