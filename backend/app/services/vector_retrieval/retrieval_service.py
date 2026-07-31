from typing import List, Optional
from sqlalchemy.orm import Session

from backend.app.models.user import User
from backend.app.services.vector_retrieval.dto import SearchResultItem, VectorDocumentPayload
from backend.app.services.vector_retrieval.embedding_service import VectorEmbeddingService
from backend.app.services.vector_retrieval.vector_store import InProcessVectorStore
from backend.app.services.vector_retrieval.reranker import BaseReranker, SimpleScoreReranker

class AccessDeniedException(Exception):
    pass

class HybridRetrievalService:
    def __init__(
        self,
        db: Session,
        embedding_service: VectorEmbeddingService,
        vector_store: Optional[InProcessVectorStore] = None,
        reranker: Optional[BaseReranker] = None,
        min_relevance_threshold: float = 0.60
    ):
        self.db = db
        self.embedding_service = embedding_service
        self.vector_store = vector_store or InProcessVectorStore()
        self.reranker = reranker or SimpleScoreReranker()
        self.min_relevance_threshold = min_relevance_threshold

    def verify_user_course_access(self, user_id: str, course_id: str):
        """
        Strict Tenant / Access Control Check (Req 7 & 13)
        """
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            raise AccessDeniedException(f"User '{user_id}' not found.")

        # If user has specific access scope, check if course_id is permitted
        if user.access_scope and user.access_scope != "ALL":
            allowed_courses = [c.strip() for c in user.access_scope.split(",")]
            if course_id not in allowed_courses:
                raise AccessDeniedException(f"User '{user_id}' does not have access to course '{course_id}'.")

    async def index_document_payload(self, payload: VectorDocumentPayload):
        self.vector_store.upsert(payload)

    async def search(
        self,
        query: str,
        user_id: str,
        course_id: str,
        lesson_id: Optional[str] = None,
        document_id: Optional[str] = None,
        document_version_id: Optional[str] = None,
        content_type: Optional[str] = None,
        top_k: int = 5
    ) -> List[SearchResultItem]:
        # 1. Verify User Access Control (Req 7 & 13)
        self.verify_user_course_access(user_id, course_id)

        # 2. Embed Query string using Model Gateway
        query_embeddings = await self.embedding_service.generate_embeddings_batch([query])
        query_vector = query_embeddings[0] if query_embeddings else [0.0] * 128

        # 3. Vector Store Search with Metadata Filtering (Req 6 & 8)
        candidates = self.vector_store.search_hybrid(
            query=query,
            query_vector=query_vector,
            embedding_model_version=self.embedding_service.model_version,
            course_id=course_id,
            lesson_id=lesson_id,
            document_id=document_id,
            document_version_id=document_version_id,
            content_type=content_type,
            top_k=top_k * 2
        )

        if not candidates:
            return []

        # 4. Rerank Candidates (Req 9)
        reranked = self.reranker.rerank(query, candidates)

        # 5. Filter by Minimum Relevance Threshold (Req 10, 11 & 12)
        valid_results = [
            item for item in reranked if item.relevance_score >= self.min_relevance_threshold
        ]

        return valid_results[:top_k]
