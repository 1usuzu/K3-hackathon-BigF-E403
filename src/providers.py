from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Any

import requests
from dotenv import load_dotenv

load_dotenv()


# ---------------------------------------------------------------------------
# Data classes (mirrors DAY04 Provider protocol)
# ---------------------------------------------------------------------------

@dataclass
class ToolCall:
    name: str
    args: dict[str, Any]


@dataclass
class ModelResponse:
    text: str | None = None
    tool_calls: list[ToolCall] = field(default_factory=list)
    raw: Any | None = None


# ---------------------------------------------------------------------------
# OpenRouter provider
# ---------------------------------------------------------------------------

class OpenRouterProvider:
    default_model = "openai/gpt-4o-mini"

    def __init__(self) -> None:
        self.api_key = os.getenv("OPENROUTER_API_KEY")
        self.base_url = "https://openrouter.ai/api/v1/chat/completions"

    def complete(
        self,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]] | None = None,
        *,
        model: str | None = None,
        temperature: float = 0.0,
        tool_choice: Any | None = None,
    ) -> ModelResponse:
        if not self.api_key:
            raise ValueError("OPENROUTER_API_KEY is missing in .env")

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        payload: dict[str, Any] = {
            "model": model or self.default_model,
            "messages": messages,
            "temperature": temperature,
        }

        if tools:
            payload["tools"] = tools
            if tool_choice is not None:
                payload["tool_choice"] = tool_choice
            else:
                payload["tool_choice"] = "auto"

        response = requests.post(self.base_url, headers=headers, json=payload, timeout=60)
        response.raise_for_status()

        data = response.json()
        message = data["choices"][0]["message"]

        # Parse tool calls into typed ToolCall objects
        raw_calls = message.get("tool_calls") or []
        tool_calls: list[ToolCall] = []
        for raw in raw_calls:
            fn = raw.get("function", {})
            name = fn.get("name", "")
            try:
                import json
                args = json.loads(fn.get("arguments", "{}"))
            except Exception:
                args = {}
            tool_calls.append(ToolCall(name=name, args=args))

        return ModelResponse(
            text=message.get("content"),
            tool_calls=tool_calls,
            raw=data,
        )

    # ------------------------------------------------------------------
    # Backward-compat shim: old code calls provider.generate(messages, tools=...)
    # and expects a raw dict back.  Keep this so app.py / existing routes
    # still work without changes.
    # ------------------------------------------------------------------
    def generate(
        self,
        messages: list[dict[str, Any]],
        model: str | None = None,
        tools: list[dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        response = self.complete(messages, tools, model=model, temperature=0.0)
        # Reconstruct the raw-dict shape the old agent.py expected
        raw_calls = []
        for tc in response.tool_calls:
            import json
            raw_calls.append({
                "function": {
                    "name": tc.name,
                    "arguments": json.dumps(tc.args, ensure_ascii=False),
                }
            })
        result: dict[str, Any] = {"content": response.text}
        if raw_calls:
            result["tool_calls"] = raw_calls
        return result


class GeminiProvider(OpenRouterProvider):
    default_model = "gemini-2.0-flash"

    def __init__(self) -> None:
        self.api_key = os.getenv("GEMINI_API_KEY")
        self.base_url = "https://generativelanguage.googleapis.com/v1beta/openai/chat/completions"

    def complete(self, *args, **kwargs):
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY is missing in .env")
        return super().complete(*args, **kwargs)


class NvidiaProvider(OpenRouterProvider):
    default_model = "meta/llama-3.1-70b-instruct"

    def __init__(self) -> None:
        self.api_key = os.getenv("NVIDIA_API_KEY")
        self.base_url = "https://integrate.api.nvidia.com/v1/chat/completions"

    def complete(self, *args, **kwargs):
        if not self.api_key:
            raise ValueError("NVIDIA_API_KEY is missing in .env")
        return super().complete(*args, **kwargs)


class OpenAIProvider(OpenRouterProvider):
    default_model = "gpt-4o-mini"

    def __init__(self) -> None:
        self.api_key = os.getenv("OPENAI_API_KEY")
        self.base_url = "https://api.openai.com/v1/chat/completions"

    def complete(self, *args, **kwargs):
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY is missing in .env")
        return super().complete(*args, **kwargs)


def get_llm_provider():
    if os.getenv("OPENAI_API_KEY"):
        return OpenAIProvider()
    if os.getenv("NVIDIA_API_KEY"):
        return NvidiaProvider()
    if os.getenv("GEMINI_API_KEY"):
        return GeminiProvider()
    return OpenRouterProvider()
