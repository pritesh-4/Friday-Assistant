"""Groq LLM provider implementation."""

from collections.abc import Sequence

from typing import Any

from app.core.config import settings
from app.services.providers.base import LLMProvider, LLMProviderError, LLMResult


class GroqProvider(LLMProvider):
    """
    Groq Provider.
    
    Known for extremely low-latency inference. Standard OpenAI-compatible API structure.
    """

    @property
    def name(self) -> str:
        return "groq"

    @property
    def is_configured(self) -> bool:
        return bool(settings.groq_api_key)

    @property
    def supports_vision(self) -> bool:
        return False

    async def generate_response(self, messages: Sequence[dict[str, Any]]) -> LLMResult:
        if not self.is_configured:
            raise LLMProviderError("Groq is not configured (missing GROQ_API_KEY).")

        payload = {
            "model": settings.groq_model,
            "messages": list(messages),
        }
        headers = {
            "Authorization": f"Bearer {settings.groq_api_key}",
            "Content-Type": "application/json",
        }

        return await self._make_openai_compatible_request(
            url="https://api.groq.com/openai/v1/chat/completions",
            headers=headers,
            payload=payload,
            model=settings.groq_model,
            timeout_seconds=settings.llm_request_timeout_seconds,
        )

    async def stream_response(self, messages: Sequence[dict[str, Any]]) -> Any:
        if not self.is_configured:
            raise LLMProviderError("Groq is not configured (missing GROQ_API_KEY).")

        payload = {
            "model": settings.groq_model,
            "messages": list(messages),
        }
        headers = {
            "Authorization": f"Bearer {settings.groq_api_key}",
            "Content-Type": "application/json",
        }

        async for chunk in self._make_openai_compatible_stream_request(
            url="https://api.groq.com/openai/v1/chat/completions",
            headers=headers,
            payload=payload,
            model=settings.groq_model,
            timeout_seconds=settings.llm_request_timeout_seconds,
        ):
            yield chunk
