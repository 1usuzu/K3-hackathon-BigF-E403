from typing import List, Optional, Dict, Any, Tuple
from sqlalchemy.orm import Session

from backend.app.models.mindmap import MindmapNode
from backend.app.models.flashcard import Flashcard
from backend.app.models.document import ContentChunk
from backend.app.services.vector_retrieval import HybridRetrievalService, SearchResultItem

class ContextBuilder:
    def __init__(self, db: Session, retrieval_service: HybridRetrievalService):
        self.db = db
        self.retrieval_service = retrieval_service

    async def build_prioritized_context(
        self,
        query: str,
        user_id: str,
        course_id: str,
        selected_node_id: Optional[str] = None,
        selected_lesson_id: Optional[str] = None,
        current_flashcard_id: Optional[str] = None
    ) -> Tuple[str, List[SearchResultItem]]:
        """
        Builds context string adhering strictly to the 5-level retrieval priority order:
        1. Selected MindmapNode
        2. Chunks directly linked to selected node
        3. Selected Lesson
        4. Chapter / Section
        5. Entire Course (via Hybrid Search)
        """
        context_parts: List[str] = []
        retrieved_items: List[SearchResultItem] = []

        # Priority 1: Selected MindmapNode
        if selected_node_id:
            node = self.db.query(MindmapNode).filter(MindmapNode.id == selected_node_id).first()
            if node:
                context_parts.append(f"[PRIORITY 1 - Selected Mindmap Node]: {node.label} (Ref: {node.slide_reference or node.page_number or 'N/A'})")
                
                # Priority 2: Chunks directly linked to selected node
                node_meta = node.metadata_json or {}
                chunk_ids = node_meta.get("content_chunk_ids", [])
                if chunk_ids:
                    chunks = self.db.query(ContentChunk).filter(ContentChunk.id.in_(chunk_ids)).all()
                    for chk in chunks:
                        context_parts.append(f"[PRIORITY 2 - Linked Node Chunk]: {chk.text_content}")

        # Flashcard Context if present
        if current_flashcard_id:
            fc = self.db.query(Flashcard).filter(Flashcard.id == current_flashcard_id).first()
            if fc:
                context_parts.append(f"[CURRENT FLASHCARD]: Q: {fc.question} | A: {fc.answer}")

        # Priority 3, 4, 5: Hybrid RAG Search (Filtered strictly by user_id and course_id!)
        search_results = await self.retrieval_service.search(
            query=query,
            user_id=user_id,
            course_id=course_id,
            lesson_id=selected_lesson_id,
            top_k=5
        )

        for res in search_results:
            context_parts.append(f"[PRIORITY 5 - Course RAG Search]: {res.content}")
            retrieved_items.append(res)

        full_context_str = "\n\n".join(context_parts)
        return full_context_str, retrieved_items
