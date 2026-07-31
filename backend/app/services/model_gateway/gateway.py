import asyncio
import logging
from typing import Optional, List, Type, Any, Dict
from pydantic import BaseModel

from backend.app.services.model_gateway.interfaces import (
    TextModelProvider, VisionModelProvider, EmbeddingProvider, TranscriptionProvider,
    ModelResponse, UsageMetadata
)
from backend.app.services.model_gateway.config import GatewayConfig, ModelTier
from backend.app.services.model_gateway.circuit_breaker import CircuitBreaker, CircuitBreakerOpenException
from backend.app.services.model_gateway.security import LogRedactor
from backend.app.services.model_gateway.mock_providers import (
    MockTextProvider, MockVisionProvider, MockEmbeddingProvider, MockTranscriptionProvider,
    RateLimitException, ProviderTimeoutException
)

logger = logging.getLogger("ModelGateway")

class ModelGateway:
    def __init__(
        self,
        config: Optional[GatewayConfig] = None,
        text_provider: Optional[TextModelProvider] = None,
        vision_provider: Optional[VisionModelProvider] = None,
        embedding_provider: Optional[EmbeddingProvider] = None,
        transcription_provider: Optional[TranscriptionProvider] = None
    ):
        self.config = config or GatewayConfig()
        self.text_provider = text_provider or MockTextProvider()
        self.vision_provider = vision_provider or MockVisionProvider()
        self.embedding_provider = embedding_provider or MockEmbeddingProvider()
        self.transcription_provider = transcription_provider or MockTranscriptionProvider()

        self.circuit_breaker = CircuitBreaker(
            provider_name=self.text_provider.provider_name,
            failure_threshold=3,
            recovery_timeout_sec=2.0
        )

        self.total_prompt_tokens = 0
        self.total_completion_tokens = 0
        self.total_cost_usd = 0.0

    def get_model_name_for_tier(self, tier: ModelTier) -> str:
        if tier == ModelTier.FAST_MODEL:
            return self.config.fast_model_name
        return self.config.pro_model_name

    async def generate_text(
        self,
        prompt: str,
        system_instruction: Optional[str] = None,
        tier: ModelTier = ModelTier.FAST_MODEL,
        temperature: float = 0.2,
        max_tokens: Optional[int] = None
    ) -> ModelResponse[Any]:
        if not self.circuit_breaker.can_execute():
            raise CircuitBreakerOpenException(self.text_provider.provider_name)

        model_name = self.get_model_name_for_tier(tier)
        effective_max_tokens = min(max_tokens or self.config.max_token_limit, self.config.max_token_limit)
        
        redacted_prompt_log = LogRedactor.redact_text(prompt)
        logger.info(f"Generating text via tier={tier.value}, model={model_name}, prompt_snippet='{redacted_prompt_log}'")

        last_exception = None
        for attempt in range(1 + self.config.rate_limit_max_retries):
            try:
                response = await self.text_provider.generate_text(
                    prompt=prompt,
                    system_instruction=system_instruction,
                    model_name=model_name,
                    temperature=temperature,
                    max_tokens=effective_max_tokens,
                    timeout_sec=self.config.default_timeout_sec
                )
                self.circuit_breaker.record_success()
                self._track_usage(response.usage)
                return response
            except (RateLimitException, ProviderTimeoutException) as e:
                last_exception = e
                logger.warning(f"Attempt {attempt + 1} failed with {type(e).__name__}. Retrying...")
                if attempt < self.config.rate_limit_max_retries:
                    await asyncio.sleep(self.config.retry_backoff_base_sec * (2 ** attempt))
            except Exception as e:
                self.circuit_breaker.record_failure()
                logger.error(f"Provider call failed: {type(e).__name__}")
                raise e

        self.circuit_breaker.record_failure()
        raise last_exception or RuntimeError("Failed to generate text after retries")

    async def generate_structured(
        self,
        prompt: str,
        response_schema: Type[BaseModel],
        system_instruction: Optional[str] = None,
        tier: ModelTier = ModelTier.PRO_MODEL,
        temperature: float = 0.2,
        max_tokens: Optional[int] = None
    ) -> ModelResponse[Any]:
        if not self.circuit_breaker.can_execute():
            raise CircuitBreakerOpenException(self.text_provider.provider_name)

        model_name = self.get_model_name_for_tier(tier)
        effective_max_tokens = min(max_tokens or self.config.max_token_limit, self.config.max_token_limit)

        redacted_prompt_log = LogRedactor.redact_text(prompt)
        logger.info(f"Generating structured output for schema={response_schema.__name__}, prompt_snippet='{redacted_prompt_log}'")

        last_exception = None
        for attempt in range(1 + self.config.rate_limit_max_retries):
            try:
                response = await self.text_provider.generate_structured(
                    prompt=prompt,
                    response_schema=response_schema,
                    system_instruction=system_instruction,
                    model_name=model_name,
                    temperature=temperature,
                    max_tokens=effective_max_tokens,
                    timeout_sec=self.config.default_timeout_sec
                )
                self.circuit_breaker.record_success()
                self._track_usage(response.usage)
                return response
            except (RateLimitException, ProviderTimeoutException) as e:
                last_exception = e
                if attempt < self.config.rate_limit_max_retries:
                    await asyncio.sleep(self.config.retry_backoff_base_sec * (2 ** attempt))
            except Exception as e:
                self.circuit_breaker.record_failure()
                raise e

        self.circuit_breaker.record_failure()
        raise last_exception or RuntimeError("Failed to generate structured response after retries")

    async def embed_texts(self, texts: List[str]) -> List[List[float]]:
        logger.info(f"Embedding {len(texts)} text chunks")
        return await self.embedding_provider.embed_texts(
            texts=texts,
            model_name=self.config.embedding_model_name,
            timeout_sec=self.config.default_timeout_sec
        )

    async def analyze_image(self, image_bytes: bytes, prompt: str) -> ModelResponse[Any]:
        response = await self.vision_provider.analyze_image(
            image_bytes=image_bytes,
            prompt=prompt,
            model_name=self.config.fast_model_name,
            timeout_sec=self.config.default_timeout_sec
        )
        self._track_usage(response.usage)
        return response

    async def transcribe_audio(self, audio_bytes: bytes, language: str = "vi") -> ModelResponse[Any]:
        response = await self.transcription_provider.transcribe_audio(
            audio_bytes=audio_bytes,
            language=language,
            timeout_sec=60.0
        )
        self._track_usage(response.usage)
        return response

    def _track_usage(self, usage: UsageMetadata):
        self.total_prompt_tokens += usage.prompt_tokens
        self.total_completion_tokens += usage.completion_tokens
        self.total_cost_usd += usage.estimated_cost_usd

    def check_health(self) -> Dict[str, Any]:
        return {
            "status": "HEALTHY" if self.circuit_breaker.state.value != "OPEN" else "DEGRADED",
            "deployment_mode": self.config.deployment_mode.value,
            "zero_data_retention": self.config.zero_data_retention,
            "circuit_breaker_state": self.circuit_breaker.state.value,
            "text_provider": self.text_provider.provider_name,
            "vision_provider": self.vision_provider.provider_name,
            "embedding_provider": self.embedding_provider.provider_name,
            "transcription_provider": self.transcription_provider.provider_name,
            "accumulated_usage": {
                "prompt_tokens": self.total_prompt_tokens,
                "completion_tokens": self.total_completion_tokens,
                "total_tokens": self.total_prompt_tokens + self.total_completion_tokens,
                "estimated_cost_usd": round(self.total_cost_usd, 6)
            }
        }
