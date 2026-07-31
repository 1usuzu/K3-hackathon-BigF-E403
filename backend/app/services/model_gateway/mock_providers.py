import asyncio
import time
import json
from typing import Optional, List, Type, Any
from pydantic import BaseModel
from backend.app.services.model_gateway.interfaces import (
    TextModelProvider, VisionModelProvider, EmbeddingProvider, TranscriptionProvider,
    ModelResponse, UsageMetadata
)

class RateLimitException(Exception):
    pass

class ProviderTimeoutException(Exception):
    pass

class MockTextProvider(TextModelProvider):
    def __init__(self, provider_name: str = "MockAI", custom_structured_response: Optional[Any] = None):
        self._provider_name = provider_name
        self.custom_structured_response = custom_structured_response
        self.should_fail_rate_limit = False
        self.should_timeout = False
        self.should_fail_generic = False

    @property
    def provider_name(self) -> str:
        return self._provider_name

    async def generate_text(
        self,
        prompt: str,
        system_instruction: Optional[str] = None,
        model_name: Optional[str] = None,
        temperature: float = 0.2,
        max_tokens: int = 2048,
        timeout_sec: float = 30.0
    ) -> ModelResponse[Any]:
        start = time.time()
        
        if self.should_timeout:
            await asyncio.sleep(timeout_sec + 0.1)
            raise ProviderTimeoutException("Mock request timed out")
        
        if self.should_fail_rate_limit:
            raise RateLimitException("429 Rate Limit Exceeded")

        if self.should_fail_generic:
            raise RuntimeError("500 Internal Provider Error")

        latency = (time.time() - start) * 1000
        content = f"Mock response for prompt: {prompt[:30]}"
        usage = UsageMetadata(
            prompt_tokens=len(prompt) // 4,
            completion_tokens=len(content) // 4,
            total_tokens=(len(prompt) + len(content)) // 4,
            estimated_cost_usd=0.0001
        )
        return ModelResponse(
            content=content,
            structured_data=None,
            usage=usage,
            model_name=model_name or "mock-text-v1",
            provider_name=self.provider_name,
            latency_ms=latency
        )

    async def generate_structured(
        self,
        prompt: str,
        response_schema: Type[BaseModel],
        system_instruction: Optional[str] = None,
        model_name: Optional[str] = None,
        temperature: float = 0.2,
        max_tokens: int = 2048,
        timeout_sec: float = 30.0
    ) -> ModelResponse[Any]:
        start = time.time()

        if self.should_timeout:
            await asyncio.sleep(timeout_sec + 0.1)
            raise ProviderTimeoutException("Mock request timed out")

        if self.should_fail_rate_limit:
            raise RateLimitException("429 Rate Limit Exceeded")

        if self.should_fail_generic:
            raise RuntimeError("500 Internal Provider Error")

        # Mock structured response instantiation
        # If model class has fields, attempt dummy instantiation
        field_defaults = {}
        for fname, field_info in response_schema.model_fields.items():
            annotation = field_info.annotation
            if annotation == str or getattr(annotation, "__name__", "") == "str":
                field_defaults[fname] = f"Mock {fname}"
            elif annotation == int or getattr(annotation, "__name__", "") == "int":
                field_defaults[fname] = 1
            elif annotation == float or getattr(annotation, "__name__", "") == "float":
                field_defaults[fname] = 0.95
            elif annotation == bool or getattr(annotation, "__name__", "") == "bool":
                field_defaults[fname] = True
            elif getattr(annotation, "__origin__", None) == list:
                field_defaults[fname] = []
            else:
                field_defaults[fname] = None

        if self.custom_structured_response is not None:
            structured_obj = self.custom_structured_response
        else:
            structured_obj = response_schema(**field_defaults)
        content_str = json.dumps(field_defaults)
        latency = (time.time() - start) * 1000
        usage = UsageMetadata(
            prompt_tokens=len(prompt) // 4,
            completion_tokens=len(content_str) // 4,
            total_tokens=(len(prompt) + len(content_str)) // 4,
            estimated_cost_usd=0.0002
        )

        return ModelResponse(
            content=content_str,
            structured_data=structured_obj,
            usage=usage,
            model_name=model_name or "mock-structured-v1",
            provider_name=self.provider_name,
            latency_ms=latency
        )

class MockVisionProvider(VisionModelProvider):
    @property
    def provider_name(self) -> str:
        return "MockVisionAI"

    async def analyze_image(
        self,
        image_bytes: bytes,
        prompt: str,
        model_name: Optional[str] = None,
        timeout_sec: float = 30.0
    ) -> ModelResponse[Any]:
        return ModelResponse(
            content=f"Mock vision analysis for image size {len(image_bytes)} bytes",
            usage=UsageMetadata(prompt_tokens=100, completion_tokens=50, total_tokens=150, estimated_cost_usd=0.0005),
            model_name=model_name or "mock-vision-v1",
            provider_name=self.provider_name
        )

class MockEmbeddingProvider(EmbeddingProvider):
    @property
    def provider_name(self) -> str:
        return "MockEmbeddingAI"

    async def embed_texts(
        self,
        texts: List[str],
        model_name: Optional[str] = None,
        timeout_sec: float = 30.0
    ) -> List[List[float]]:
        # Return dummy 1536-dim vector per text
        return [[0.01 * (i + 1)] * 1536 for i in range(len(texts))]

class MockTranscriptionProvider(TranscriptionProvider):
    @property
    def provider_name(self) -> str:
        return "MockAudioAI"

    async def transcribe_audio(
        self,
        audio_bytes: bytes,
        language: str = "vi",
        model_name: Optional[str] = None,
        timeout_sec: float = 60.0
    ) -> ModelResponse[Any]:
        return ModelResponse(
            content="Mô phỏng bóc tách audio bài giảng sang text.",
            usage=UsageMetadata(prompt_tokens=50, completion_tokens=30, total_tokens=80, estimated_cost_usd=0.0003),
            model_name=model_name or "mock-whisper-v1",
            provider_name=self.provider_name
        )
