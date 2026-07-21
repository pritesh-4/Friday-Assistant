"""OpenRouter LLM provider implementation."""

import time
from collections.abc import Sequence

import httpx

from app.core.config import settings
from app.services.providers.base import LLMProvider, LLMProviderError, LLMResult, logger


class OpenRouterProvider(LLMProvider):
    """
    OpenRouter Provider.
    
    A unified API to access various models. Prioritizing free models in this configuration.
    """

    @property
    def name(self) -> str:
        return "openrouter"

    @property
    def is_configured(self) -> bool:
        return bool(settings.openrouter_api_key)

    async def generate_response(self, messages: Sequence[dict[str, str]]) -> LLMResult:
        if not self.is_configured:
            raise LLMProviderError("OpenRouter is not configured (missing OPENROUTER_API_KEY).")

        start_time = time.monotonic()
        payload = {
            "model": settings.openrouter_model,
            "messages": list(messages),
        }
        headers = {
            "Authorization": f"Bearer {settings.openrouter_api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": settings.frontend_url,  # Required by OpenRouter for ranking
            "X-Title": settings.app_name,           # Required by OpenRouter for ranking
        }
        timeout = httpx.Timeout(settings.llm_request_timeout_seconds)

        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                response = await client.post(
                    "https://openrouter.ai/api/v1/chat/completions",
                    headers=headers,
                    json=payload,
                )
                response.raise_for_status()
        except httpx.HTTPError as exc:
            logger.error("OpenRouter provider HTTP error: %s", exc)
            raise LLMProviderError(f"OpenRouter API error: {exc}") from exc

        data = response.json()
        try:
            choice = data["choices"][0]
            content = choice["message"]["content"]
            finish_reason = choice.get("finish_reason")
        except (KeyError, IndexError, TypeError) as exc:
            logger.error("OpenRouter response parsing error: %s", exc)
            raise LLMProviderError("Invalid response format from OpenRouter API.") from exc

        if not isinstance(content, str) or not content.strip():
            raise LLMProviderError("OpenRouter returned an empty response.")

        return LLMResult(
            content=content.strip(),
            provider=self.name,
            model=settings.openrouter_model,
            latency_ms=self._track_latency(start_time),
            finish_reason=finish_reason,
        )
