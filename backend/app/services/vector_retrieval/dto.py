from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any

@dataclass
class VectorDocumentPayload:
    id: str
    entity_type: str  # ContentChunk, MindmapNode, Flashcard, GlossaryTerm, Formula, Code
    entity_id: str
    text_content: str
    vector: List[float]
    embedding_model_version: str
    course_id: str
    lesson_id: Optional[str] = None
    document_id: Optional[str] = None
    document_version_id: Optional[str] = None
    content_type: str = "text"
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class SearchResultItem:
    entity_type: str
    entity_id: str
    content: str
    relevance_score: float
    semantic_score: float
    keyword_score: float
    rerank_score: float
    metadata: Dict[str, Any] = field(default_factory=dict)
