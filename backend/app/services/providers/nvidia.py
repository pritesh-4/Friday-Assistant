"""NVIDIA NIM LLM provider implementation."""

from collections.abc import Sequence
from typing import Any

from app.core.config import settings
from app.services.providers.base import LLMProvider, LLMProviderError, LLMResult


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
            raise LLMProviderError(
                "NVIDIA NIM is not configured (missing NVIDIA_API_KEY)."
            )

        payload = {
            "model": settings.nvidia_model,
            "messages": list(messages),
        }
        headers = {
            "Authorization": f"Bearer {settings.nvidia_api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

        return await self._make_openai_compatible_request(
            url="https://integrate.api.nvidia.com/v1/chat/completions",
            headers=headers,
            payload=payload,
            model=settings.nvidia_model,
            timeout_seconds=settings.llm_request_timeout_seconds,
        )

    async def stream_response(self, messages: Sequence[dict[str, Any]]) -> Any:
        if not self.is_configured:
            raise LLMProviderError(
                "NVIDIA NIM is not configured (missing NVIDIA_API_KEY)."
            )

        payload = {
            "model": settings.nvidia_model,
            "messages": list(messages),
        }
        headers = {
            "Authorization": f"Bearer {settings.nvidia_api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

        async for chunk in self._make_openai_compatible_stream_request(
            url="https://integrate.api.nvidia.com/v1/chat/completions",
            headers=headers,
            payload=payload,
            model=settings.nvidia_model,
            timeout_seconds=settings.llm_request_timeout_seconds,
        ):
            yield chunk
