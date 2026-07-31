from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from dataclasses import dataclass, field

@dataclass
class ExtractedBlockData:
    block_type: str  # heading, paragraph, list, table, formula, code, image, diagram, note
    raw_content: str
    normalized_content: str
    language: str = "vi"
    page_number: Optional[int] = None
    slide_number: Optional[int] = None
    sequence_number: int = 1
    metadata: Dict[str, Any] = field(default_factory=dict)
    extraction_confidence: float = 1.0
    source_reference: str = ""

class BaseContentExtractor(ABC):
    @abstractmethod
    async def extract_blocks(
        self,
        file_bytes: bytes,
        document_id: str,
        document_version_id: str,
        lesson_id: Optional[str] = None
    ) -> List[ExtractedBlockData]:
        pass
