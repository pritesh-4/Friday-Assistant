"""OpenRouter LLM provider implementation."""

import time
from collections.abc import Sequence
from typing import Any

import httpx

from app.core.config import settings
from app.services.providers.base import LLMProvider, LLMProviderError, LLMResult, logger


class OpenRouterProvider(LLMProvider):
    """
    OpenRouter Provider.
    
    Serves as an aggregator for multiple models, supporting a unified API.
    """

    @property
    def name(self) -> str:
        return "openrouter"

    @property
    def is_configured(self) -> bool:
        return bool(settings.openrouter_api_key)

    @property
    def supports_vision(self) -> bool:
        return True

    async def generate_response(self, messages: Sequence[dict[str, Any]]) -> LLMResult:
        if not self.is_configured:
            raise LLMProviderError("OpenRouter is not configured (missing OPENROUTER_API_KEY).")

        payload = {
            "model": settings.openrouter_model,
            "messages": list(messages),
        }
        headers = {
            "Authorization": f"Bearer {settings.openrouter_api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": settings.frontend_url,
            "X-Title": settings.app_name,
        }

        return await self._make_openai_compatible_request(
            url="https://openrouter.ai/api/v1/chat/completions",
            headers=headers,
            payload=payload,
            model=settings.openrouter_model,
            timeout_seconds=settings.llm_request_timeout_seconds,
        )
