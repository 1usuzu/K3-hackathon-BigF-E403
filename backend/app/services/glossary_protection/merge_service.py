from typing import Dict, List, Optional
from sqlalchemy.orm import Session
from backend.app.models.document import GlossaryTerm
from backend.app.services.glossary_protection.default_terms import DEFAULT_SYSTEM_GLOSSARY
from backend.app.services.glossary_protection.extraction_service import GlossaryExtractionService

class GlossaryMergeService:
    @staticmethod
    def get_merged_glossary_for_course(
        course_id: Optional[str] = None,
        db: Optional[Session] = None,
        document_text: str = ""
    ) -> Dict[str, str]:
        """
        Merges glossary terms from 3 sources with Conflict Resolution Priority:
        1. Course DB Terms (Highest Priority)
        2. Document-Extracted Terms
        3. Default System Glossary (Base Priority)
        """
        # Start with Default System Glossary (Base Tier)
        merged: Dict[str, str] = dict(DEFAULT_SYSTEM_GLOSSARY)

        # Merge Document-Extracted Terms (Tier 2 - overrides default if newly extracted)
        if document_text:
            extracted_terms = GlossaryExtractionService.extract_candidate_terms(document_text)
            for term, defn in extracted_terms.items():
                if term not in merged:
                    merged[term] = defn

        # Merge Course-Specific DB Terms (Tier 1 - Highest Priority overrides previous)
        if db and course_id:
            course_terms = db.query(GlossaryTerm).filter(GlossaryTerm.course_id == course_id).all()
            for ct in course_terms:
                merged[ct.term] = ct.definition or f"Thuật ngữ khóa học '{ct.term}'"

        return merged
