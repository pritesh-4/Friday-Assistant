"""Gemini LLM provider implementation."""

import time
from collections.abc import Sequence

from typing import Any

import httpx

from app.core.config import settings
from app.services.providers.base import LLMProvider, LLMProviderError, LLMResult, logger


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

        start_time = time.monotonic()
        payload = {
            "model": settings.gemini_model,
            "messages": list(messages),
        }
        headers = {
            "Authorization": f"Bearer {settings.gemini_api_key}",
            "Content-Type": "application/json",
        }
        timeout = httpx.Timeout(settings.llm_request_timeout_seconds)

        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                response = await client.post(
                    "https://generativelanguage.googleapis.com/v1beta/openai/chat/completions",
                    headers=headers,
                    json=payload,
                )
                response.raise_for_status()
        except httpx.HTTPError as exc:
            logger.error("Gemini provider HTTP error: %s", exc)
            raise LLMProviderError(f"Gemini API error: {exc}") from exc

        data = response.json()
        try:
            choice = data["choices"][0]
            content = choice["message"]["content"]
            finish_reason = choice.get("finish_reason")
        except (KeyError, IndexError, TypeError) as exc:
            logger.error("Gemini response parsing error: %s", exc)
            raise LLMProviderError("Invalid response format from Gemini API.") from exc

        if not isinstance(content, str) or not content.strip():
            raise LLMProviderError("Gemini returned an empty response.")

        return LLMResult(
            content=content.strip(),
            provider=self.name,
            model=settings.gemini_model,
            latency_ms=self._track_latency(start_time),
            finish_reason=finish_reason,
        )
