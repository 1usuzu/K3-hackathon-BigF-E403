import math
import re
from typing import List, Dict, Optional, Any
from backend.app.services.vector_retrieval.dto import VectorDocumentPayload, SearchResultItem

def cosine_similarity(v1: List[float], v2: List[float]) -> float:
    if not v1 or not v2 or len(v1) != len(v2):
        return 0.0
    dot = sum(a * b for a, b in zip(v1, v2))
    norm_v1 = math.sqrt(sum(a * a for a in v1))
    norm_v2 = math.sqrt(sum(b * b for b in v2))
    if norm_v1 == 0.0 or norm_v2 == 0.0:
        return 0.0
    return dot / (norm_v1 * norm_v2)

def compute_keyword_score(query: str, text: str) -> float:
    q_words = set(re.findall(r"\w+", query.lower()))
    t_words = set(re.findall(r"\w+", text.lower()))
    if not q_words:
        return 0.0
    intersection = q_words.intersection(t_words)
    return len(intersection) / len(q_words)

class InProcessVectorStore:
    def __init__(self):
        self._documents: Dict[str, VectorDocumentPayload] = {}

    def upsert(self, payload: VectorDocumentPayload):
        # Versioning Protection: Store payload cleanly
        self._documents[payload.id] = payload

    def search_hybrid(
        self,
        query: str,
        query_vector: List[float],
        embedding_model_version: str,
        course_id: str,
        lesson_id: Optional[str] = None,
        document_id: Optional[str] = None,
        document_version_id: Optional[str] = None,
        content_type: Optional[str] = None,
        top_k: int = 10
    ) -> List[SearchResultItem]:
        candidates: List[SearchResultItem] = []

        for doc in self._documents.values():
            # 1. Mandatory Version Check (Req 4 & 5: Do not mix embedding versions!)
            if doc.embedding_model_version != embedding_model_version:
                continue

            # 2. Strict Metadata Filter (Req 6 & 7: Mandatory course_id & access check!)
            if doc.course_id != course_id:
                continue

            if lesson_id and doc.lesson_id != lesson_id:
                continue

            if document_id and doc.document_id != document_id:
                continue

            if document_version_id and doc.document_version_id != document_version_id:
                continue

            if content_type and doc.content_type != content_type:
                continue

            # 3. Hybrid scoring: Semantic + Keyword
            sem_score = cosine_similarity(query_vector, doc.vector)
            kw_score = compute_keyword_score(query, doc.text_content)

            item = SearchResultItem(
                entity_type=doc.entity_type,
                entity_id=doc.entity_id,
                content=doc.text_content,
                relevance_score=sem_score,
                semantic_score=sem_score,
                keyword_score=kw_score,
                rerank_score=sem_score,
                metadata=doc.metadata
            )
            candidates.append(item)

        return candidates
