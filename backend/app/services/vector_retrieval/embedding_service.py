import asyncio
import logging
from typing import List, Dict, Optional, Any
from backend.app.services.model_gateway import ModelGateway
from backend.app.services.vector_retrieval.dto import VectorDocumentPayload

logger = logging.getLogger("VectorEmbeddingService")

class VectorEmbeddingService:
    def __init__(
        self,
        gateway: ModelGateway,
        model_version: str = "text-embedding-v1",
        batch_size: int = 16,
        max_retries: int = 3
    ):
        self.gateway = gateway
        self.model_version = model_version
        self.batch_size = batch_size
        self.max_retries = max_retries

    async def generate_embeddings_batch(
        self,
        texts: List[str]
    ) -> List[List[float]]:
        if not texts:
            return []

        all_embeddings: List[List[float]] = []

        # Batching processing (Req 2)
        for i in range(0, len(texts), self.batch_size):
            batch = texts[i : i + self.batch_size]
            
            # Retry with exponential backoff (Req 3)
            embeddings = None
            for attempt in range(self.max_retries):
                try:
                    embeddings = await self.gateway.embed_texts(batch)
                    break
                except Exception as err:
                    logger.warning(f"Embedding attempt {attempt+1} failed: {err}")
                    if attempt < self.max_retries - 1:
                        await asyncio.sleep(0.1 * (2 ** attempt))
                    else:
                        raise err

            if embeddings:
                all_embeddings.extend(embeddings)

        return all_embeddings

    async def build_payload_for_entity(
        self,
        entity_type: str,
        entity_id: str,
        text_content: str,
        course_id: str,
        lesson_id: Optional[str] = None,
        document_id: Optional[str] = None,
        document_version_id: Optional[str] = None,
        content_type: str = "text",
        extra_metadata: Optional[Dict[str, Any]] = None
    ) -> VectorDocumentPayload:
        embeddings = await self.generate_embeddings_batch([text_content])
        vector = embeddings[0] if embeddings else [0.0] * 128

        return VectorDocumentPayload(
            id=f"{entity_type.lower()}_{entity_id}",
            entity_type=entity_type,
            entity_id=entity_id,
            text_content=text_content,
            vector=vector,
            embedding_model_version=self.model_version,
            course_id=course_id,
            lesson_id=lesson_id,
            document_id=document_id,
            document_version_id=document_version_id,
            content_type=content_type,
            metadata=extra_metadata or {}
        )
