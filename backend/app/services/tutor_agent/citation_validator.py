from typing import List
from backend.app.services.tutor_agent.schemas import CitationSchema
from backend.app.services.vector_retrieval.dto import SearchResultItem

class CitationValidator:
    @staticmethod
    def validate_and_enrich_citations(
        citations: List[CitationSchema],
        retrieved_items: List[SearchResultItem]
    ) -> List[CitationSchema]:
        if not citations:
            # Generate automatic citations from retrieved items if available
            auto_citations: List[CitationSchema] = []
            for item in retrieved_items:
                meta = item.metadata or {}
                cit = CitationSchema(
                    document_id=meta.get("document_id"),
                    document_version_id=meta.get("document_version_id"),
                    chunk_id=item.entity_id,
                    page_number=meta.get("page_number"),
                    slide_number=meta.get("slide_number"),
                    source_excerpt=item.content[:200]
                )
                auto_citations.append(cit)
            return auto_citations

        valid_citations: List[CitationSchema] = []
        for cit in citations:
            # Ensure source excerpt is non-empty
            if not cit.source_excerpt or len(cit.source_excerpt.strip()) == 0:
                continue
            valid_citations.append(cit)

        return valid_citations
