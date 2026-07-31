from abc import ABC, abstractmethod
from typing import List
from backend.app.services.vector_retrieval.dto import SearchResultItem

class BaseReranker(ABC):
    @abstractmethod
    def rerank(
        self,
        query: str,
        candidates: List[SearchResultItem]
    ) -> List[SearchResultItem]:
        pass

class SimpleScoreReranker(BaseReranker):
    def __init__(self, semantic_weight: float = 0.6, keyword_weight: float = 0.4):
        self.semantic_weight = semantic_weight
        self.keyword_weight = keyword_weight

    def rerank(
        self,
        query: str,
        candidates: List[SearchResultItem]
    ) -> List[SearchResultItem]:
        if not candidates:
            return []

        for item in candidates:
            item.rerank_score = round(
                item.semantic_score * self.semantic_weight + item.keyword_score * self.keyword_weight,
                3
            )
            item.relevance_score = item.rerank_score

        # Sort candidates descending by rerank score
        candidates.sort(key=lambda x: x.rerank_score, reverse=True)
        return candidates
