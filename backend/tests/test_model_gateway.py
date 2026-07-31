import pytest
import asyncio
from pydantic import BaseModel
from backend.app.schemas.enums import DeploymentMode
from backend.app.services.model_gateway import (
    ModelGateway, GatewayConfig, ModelTier, LogRedactor,
    MockTextProvider, RateLimitException, CircuitBreakerOpenException
)

class SampleFlashcardSchema(BaseModel):
    question: str
    answer: str
    difficulty_score: float
    is_key_concept: bool

@pytest.mark.asyncio
async def test_text_generation_fast_and_pro_tiers():
    gateway = ModelGateway()
    
    res_fast = await gateway.generate_text(
        prompt="Tóm tắt ngắn bài học",
        tier=ModelTier.FAST_MODEL
    )
    assert res_fast.model_name == "gpt-4o-mini"
    assert "Mock response" in res_fast.content
    assert res_fast.usage.prompt_tokens > 0

    res_pro = await gateway.generate_text(
        prompt="Phân tích chuyên sâu bài học",
        tier=ModelTier.PRO_MODEL
    )
    assert res_pro.model_name == "gpt-4o"

@pytest.mark.asyncio
async def test_structured_output_validation():
    gateway = ModelGateway()

    res = await gateway.generate_structured(
        prompt="Tạo flashcard về Gradient Descent",
        response_schema=SampleFlashcardSchema,
        tier=ModelTier.PRO_MODEL
    )

    assert res.structured_data is not None
    assert isinstance(res.structured_data, SampleFlashcardSchema)
    assert res.structured_data.question.startswith("Mock")
    assert res.structured_data.is_key_concept is True

@pytest.mark.asyncio
async def test_embedding_and_vision_and_transcription():
    gateway = ModelGateway()

    embeddings = await gateway.embed_texts(["Chunk 1", "Chunk 2"])
    assert len(embeddings) == 2
    assert len(embeddings[0]) == 1536

    vision_res = await gateway.analyze_image(image_bytes=b"fake_png", prompt="Mô tả hình")
    assert "Mock vision" in vision_res.content

    audio_res = await gateway.transcribe_audio(audio_bytes=b"fake_mp3", language="vi")
    assert "bóc tách audio" in audio_res.content

def test_log_redacting_security():
    sensitive_prompt = "My API Key is sk-proj1234567890abcdef12345678 and token Bearer mysecrettoken12345"
    redacted = LogRedactor.redact_text(sensitive_prompt)
    assert "sk-proj" not in redacted
    assert "mysecrettoken" not in redacted
    assert "[REDACTED_SECRET]" in redacted

    long_text = "A" * 300
    truncated = LogRedactor.redact_text(long_text, max_chars=100)
    assert len(truncated) < 200
    assert "TRUNCATED" in truncated

@pytest.mark.asyncio
async def test_circuit_breaker_tripping_and_recovery():
    mock_provider = MockTextProvider()
    mock_provider.should_fail_generic = True

    config = GatewayConfig(rate_limit_max_retries=0)
    gateway = ModelGateway(config=config, text_provider=mock_provider)

    # Make 3 failing calls to trip circuit breaker
    for _ in range(3):
        with pytest.raises(RuntimeError):
            await gateway.generate_text("Prompt")

    assert gateway.circuit_breaker.state.value == "OPEN"

    # 4th call should fail immediately with CircuitBreakerOpenException
    with pytest.raises(CircuitBreakerOpenException):
        await gateway.generate_text("Prompt")

@pytest.mark.asyncio
async def test_accumulated_usage_tracking_and_health_check():
    gateway = ModelGateway()
    
    await gateway.generate_text("Test 1")
    await gateway.generate_text("Test 2")

    health = gateway.check_health()
    assert health["status"] == "HEALTHY"
    assert health["deployment_mode"] == DeploymentMode.CLOUD_ENTERPRISE.value
    assert health["zero_data_retention"] is True
    assert health["accumulated_usage"]["total_tokens"] > 0
    assert health["accumulated_usage"]["estimated_cost_usd"] > 0.0
