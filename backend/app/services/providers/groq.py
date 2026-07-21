"""Groq LLM provider implementation."""

import time
from collections.abc import Sequence

import httpx

from app.core.config import settings
from app.services.providers.base import LLMProvider, LLMProviderError, LLMResult, logger


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

    async def generate_response(self, messages: Sequence[dict[str, str]]) -> LLMResult:
        if not self.is_configured:
            raise LLMProviderError("Groq is not configured (missing GROQ_API_KEY).")

        start_time = time.monotonic()
        payload = {
            "model": settings.groq_model,
            "messages": list(messages),
        }
        headers = {
            "Authorization": f"Bearer {settings.groq_api_key}",
            "Content-Type": "application/json",
        }
        timeout = httpx.Timeout(settings.llm_request_timeout_seconds)

        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                response = await client.post(
                    "https://api.groq.com/openai/v1/chat/completions",
                    headers=headers,
                    json=payload,
                )
                response.raise_for_status()
        except httpx.HTTPError as exc:
            logger.error("Groq provider HTTP error: %s", exc)
            raise LLMProviderError(f"Groq API error: {exc}") from exc

        data = response.json()
        try:
            choice = data["choices"][0]
            content = choice["message"]["content"]
            finish_reason = choice.get("finish_reason")
        except (KeyError, IndexError, TypeError) as exc:
            logger.error("Groq response parsing error: %s", exc)
            raise LLMProviderError("Invalid response format from Groq API.") from exc

        if not isinstance(content, str) or not content.strip():
            raise LLMProviderError("Groq returned an empty response.")

        return LLMResult(
            content=content.strip(),
            provider=self.name,
            model=settings.groq_model,
            latency_ms=self._track_latency(start_time),
            finish_reason=finish_reason,
        )
