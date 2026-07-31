from abc import ABC, abstractmethod
from typing import TypeVar, Generic, Optional, List, Any, Dict, Type
from dataclasses import dataclass, field
from pydantic import BaseModel

T = TypeVar("T", bound=BaseModel)

@dataclass
class UsageMetadata:
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    estimated_cost_usd: float = 0.0

@dataclass
class ModelResponse(Generic[T]):
    content: str
    structured_data: Optional[T] = None
    usage: UsageMetadata = field(default_factory=UsageMetadata)
    model_name: str = ""
    provider_name: str = ""
    latency_ms: float = 0.0

class TextModelProvider(ABC):
    @property
    @abstractmethod
    def provider_name(self) -> str:
        pass

    @abstractmethod
    async def generate_text(
        self,
        prompt: str,
        system_instruction: Optional[str] = None,
        model_name: Optional[str] = None,
        temperature: float = 0.2,
        max_tokens: int = 2048,
        timeout_sec: float = 30.0
    ) -> ModelResponse[Any]:
        pass

    @abstractmethod
    async def generate_structured(
        self,
        prompt: str,
        response_schema: Type[T],
        system_instruction: Optional[str] = None,
        model_name: Optional[str] = None,
        temperature: float = 0.2,
        max_tokens: int = 2048,
        timeout_sec: float = 30.0
    ) -> ModelResponse[T]:
        pass

class VisionModelProvider(ABC):
    @property
    @abstractmethod
    def provider_name(self) -> str:
        pass

    @abstractmethod
    async def analyze_image(
        self,
        image_bytes: bytes,
        prompt: str,
        model_name: Optional[str] = None,
        timeout_sec: float = 30.0
    ) -> ModelResponse[Any]:
        pass

class EmbeddingProvider(ABC):
    @property
    @abstractmethod
    def provider_name(self) -> str:
        pass

    @abstractmethod
    async def embed_texts(
        self,
        texts: List[str],
        model_name: Optional[str] = None,
        timeout_sec: float = 30.0
    ) -> List[List[float]]:
        pass

class TranscriptionProvider(ABC):
    @property
    @abstractmethod
    def provider_name(self) -> str:
        pass

    @abstractmethod
    async def transcribe_audio(
        self,
        audio_bytes: bytes,
        language: str = "vi",
        model_name: Optional[str] = None,
        timeout_sec: float = 60.0
    ) -> ModelResponse[Any]:
        pass
