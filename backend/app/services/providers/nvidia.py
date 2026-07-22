"""NVIDIA NIM LLM provider implementation."""

import time
from collections.abc import Sequence
from typing import Any

import httpx

from app.core.config import settings
from app.services.providers.base import LLMProvider, LLMProviderError, LLMResult, logger


class NvidiaProvider(LLMProvider):
    """
    NVIDIA NIM Provider.
    
    Uses NVIDIA's high-performance inference microservices (OpenAI-compatible).
    """

    @property
    def name(self) -> str:
        return "nvidia"

    @property
    def is_configured(self) -> bool:
        return bool(settings.nvidia_api_key)

    @property
    def supports_vision(self) -> bool:
        return False

    async def generate_response(self, messages: Sequence[dict[str, Any]]) -> LLMResult:
        if not self.is_configured:
            raise LLMProviderError("NVIDIA NIM is not configured (missing NVIDIA_API_KEY).")

        start_time = time.monotonic()
        payload = {
            "model": settings.nvidia_model,
            "messages": list(messages),
        }
        headers = {
            "Authorization": f"Bearer {settings.nvidia_api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
        timeout = httpx.Timeout(settings.llm_request_timeout_seconds)

        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                response = await client.post(
                    "https://integrate.api.nvidia.com/v1/chat/completions",
                    headers=headers,
                    json=payload,
                )
                response.raise_for_status()
        except httpx.HTTPError as exc:
            logger.error("NVIDIA provider HTTP error: %s", exc)
            raise LLMProviderError(f"NVIDIA API error: {exc}") from exc

        data = response.json()
        try:
            choice = data["choices"][0]
            content = choice["message"]["content"]
            finish_reason = choice.get("finish_reason")
        except (KeyError, IndexError, TypeError) as exc:
            logger.error("NVIDIA response parsing error: %s", exc)
            raise LLMProviderError("Invalid response format from NVIDIA API.") from exc

        if not isinstance(content, str) or not content.strip():
            raise LLMProviderError("NVIDIA returned an empty response.")

        return LLMResult(
            content=content.strip(),
            provider=self.name,
            model=settings.nvidia_model,
            latency_ms=self._track_latency(start_time),
            finish_reason=finish_reason,
        )
