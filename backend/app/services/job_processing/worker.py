import asyncio
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from backend.app.models.document import ContentChunk

class WorkerCrashException(Exception):
    pass

class BaseChunkWorker(ABC):
    @abstractmethod
    async def process_chunk(self, chunk: ContentChunk) -> Dict[str, Any]:
        pass

class MockChunkWorker(BaseChunkWorker):
    def __init__(self):
        self.should_crash = False
        self.should_timeout = False
        self.simulated_delay_sec = 0.01

    async def process_chunk(self, chunk: ContentChunk) -> Dict[str, Any]:
        if self.should_timeout:
            await asyncio.sleep(60.0)  # Trigger timeout
            
        if self.should_crash:
            raise WorkerCrashException(f"Worker crashed intentionally on chunk '{chunk.id}'")

        if self.simulated_delay_sec > 0:
            await asyncio.sleep(self.simulated_delay_sec)

        return {
            "chunk_id": chunk.id,
            "processed": True,
            "has_code": chunk.has_code,
            "has_formulas": chunk.has_formulas,
            "chunk_index": chunk.chunk_index
        }
