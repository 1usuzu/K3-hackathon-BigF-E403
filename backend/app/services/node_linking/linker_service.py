import re
from typing import List, Dict, Optional, Set
from backend.app.models.flashcard import Flashcard
from backend.app.models.mindmap import MindmapNode
from backend.app.services.node_linking.dto import NodeLinkMatch

class FlashcardNodeLinkerService:
    def __init__(self, min_confidence_threshold: float = 0.60):
        self.min_confidence_threshold = min_confidence_threshold

    def calculate_link_confidence(
        self,
        flashcard: Flashcard,
        node: MindmapNode
    ) -> NodeLinkMatch:
        score = 0.0
        reasons: List[str] = []

        node_meta = node.metadata_json or {}
        fc_opts = flashcard.options_json or {}
        fc_tags = (flashcard.tags_json or {}).get("tags", [])

        # 1. Same Chunk Check (+0.40)
        node_chunk_ids = node_meta.get("content_chunk_ids", [])
        if node_meta.get("content_chunk_id"):
            node_chunk_ids.append(node_meta.get("content_chunk_id"))

        if flashcard.content_chunk_id and flashcard.content_chunk_id in node_chunk_ids:
            score += 0.40
            reasons.append("same_chunk")

        # 2. Same Lesson Check (+0.15)
        if flashcard.lesson_id and (flashcard.lesson_id == node_meta.get("lesson_id")):
            score += 0.15
            reasons.append("same_lesson")

        # 3. Source Reference Matching (+0.25)
        fc_sources = fc_opts.get("source_references", [])
        node_ref = node.slide_reference or (f"Page {node.page_number}" if node.page_number else "")
        
        if node_ref and any(node_ref.lower() in src.lower() for src in fc_sources):
            score += 0.25
            reasons.append("source_reference_match")

        # 4. Shared Concept / Glossary Terms / Tags (+0.20)
        node_glossary = set(node_meta.get("glossary_terms", []))
        fc_glossary = set(fc_opts.get("glossary_terms", []))
        shared_glossary = node_glossary.intersection(fc_glossary)

        node_tags = set(node_meta.get("tags", []))
        fc_tags_set = set(fc_tags)
        shared_tags = node_tags.intersection(fc_tags_set)

        if shared_glossary or shared_tags:
            score += 0.20
            reasons.append(f"shared_concept:{','.join(shared_glossary or shared_tags)}")

        # 5. Semantic / Keyword Match (+0.10)
        node_label_lower = node.label.lower()
        fc_question_lower = flashcard.question.lower()
        fc_answer_lower = flashcard.answer.lower()

        # Extract words longer than 3 characters from node label
        words = [w for w in re.findall(r"\w+", node_label_lower) if len(w) > 3]
        if any(w in fc_question_lower or w in fc_answer_lower for w in words):
            score += 0.10
            reasons.append("keyword_similarity")

        final_score = round(min(score, 1.0), 2)
        return NodeLinkMatch(
            node_id=node.id,
            node_stable_id=node.node_stable_id,
            confidence_score=final_score,
            match_reasons=reasons
        )

    def find_matching_nodes(
        self,
        flashcard: Flashcard,
        candidate_nodes: List[MindmapNode]
    ) -> List[NodeLinkMatch]:
        matches: List[NodeLinkMatch] = []

        for node in candidate_nodes:
            match = self.calculate_link_confidence(flashcard, node)
            if match.confidence_score >= self.min_confidence_threshold:
                matches.append(match)

        # Sort matches by confidence score descending
        matches.sort(key=lambda m: m.confidence_score, reverse=True)
        return matches
