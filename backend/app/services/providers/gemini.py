"""Gemini LLM provider implementation."""

from collections.abc import Sequence
from typing import Any

from app.core.config import settings
from app.services.providers.base import LLMProvider, LLMProviderError, LLMResult


class GeminiProvider(LLMProvider):
    """
    Google Gemini Provider.

    Uses Gemini's official OpenAI-compatible endpoint for ease of message formatting.
    """

    @property
    def name(self) -> str:
        return "gemini"

    @property
    def is_configured(self) -> bool:
        return bool(settings.gemini_api_key)

    @property
    def supports_vision(self) -> bool:
        return True

    async def generate_response(self, messages: Sequence[dict[str, Any]]) -> LLMResult:
        if not self.is_configured:
            raise LLMProviderError("Gemini is not configured (missing GEMINI_API_KEY).")

        payload = {
            "model": settings.gemini_model,
            "messages": list(messages),
        }
        headers = {
            "Authorization": f"Bearer {settings.gemini_api_key}",
            "Content-Type": "application/json",
        }

        return await self._make_openai_compatible_request(
            url="https://generativelanguage.googleapis.com/v1beta/openai/chat/completions",
            headers=headers,
            payload=payload,
            model=settings.gemini_model,
            timeout_seconds=settings.llm_request_timeout_seconds,
        )

    async def stream_response(self, messages: Sequence[dict[str, Any]]) -> Any:
        if not self.is_configured:
            raise LLMProviderError("Gemini is not configured (missing GEMINI_API_KEY).")

        payload = {
            "model": settings.gemini_model,
            "messages": list(messages),
        }
        headers = {
            "Authorization": f"Bearer {settings.gemini_api_key}",
            "Content-Type": "application/json",
        }

        async for chunk in self._make_openai_compatible_stream_request(
            url="https://generativelanguage.googleapis.com/v1beta/openai/chat/completions",
            headers=headers,
            payload=payload,
            model=settings.gemini_model,
            timeout_seconds=settings.llm_request_timeout_seconds,
        ):
            yield chunk
