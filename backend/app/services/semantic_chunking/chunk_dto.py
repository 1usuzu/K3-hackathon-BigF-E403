import hashlib
import uuid
from typing import List, Optional, Dict, Any
from dataclasses import dataclass, field

@dataclass
class SemanticChunkData:
    document_id: str
    document_version_id: str
    sequence_number: int
    content: str
    title: str = ""
    lesson_id: Optional[str] = None
    parent_section_id: Optional[str] = None
    content_block_ids: List[str] = field(default_factory=list)
    content_types: List[str] = field(default_factory=list)
    token_estimate: int = 0
    overlap_summary: str = ""
    glossary_terms: List[str] = field(default_factory=list)
    source_references: List[str] = field(default_factory=list)
    checksum: str = ""
    chunk_id: str = field(default_factory=lambda: str(uuid.uuid4()))

    def compute_checksum(self) -> str:
        payload = f"{self.document_version_id}:{self.lesson_id}:{self.sequence_number}:{self.title}:{self.content}"
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()
