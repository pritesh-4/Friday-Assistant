"""Abstract base class and models for all LLM providers."""

import time
from abc import ABC, abstractmethod
from typing import Any, Sequence
from dataclasses import dataclass
import httpx

from app.core.logging import get_logger

logger = get_logger(__name__)


class LLMProviderError(RuntimeError):
    """Raised when a configured provider fails to produce a response (timeout, 429, 500, etc.)."""


@dataclass(frozen=True)
class LLMResult:
    """Standardized response from any LLM provider."""
    content: str
    provider: str
    model: str
    latency_ms: int
    finish_reason: str | None = None


class LLMProvider(ABC):
    """
    Abstract Base Class for all LLM providers.
    
    Ensures that every provider implements a common interface for the router/orchestrator.
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """The identifier of the provider (e.g., 'groq', 'gemini')."""
        pass

    @property
    @abstractmethod
    def is_configured(self) -> bool:
        """True if the provider has all necessary configuration (like API keys) to run."""
        pass

    @property
    @abstractmethod
    def supports_vision(self) -> bool:
        """True if the provider model supports multimodal image/vision inputs."""
        pass

    @abstractmethod
    async def generate_response(self, messages: Sequence[dict[str, Any]]) -> LLMResult:
        """
        Generate a text response from the given message history.
        
        Args:
            messages: A sequence of dicts containing 'role' and 'content' keys.
            
        Returns:
            An LLMResult containing the generated content and metadata.
            
        Raises:
            LLMProviderError: If the request fails due to network, auth, or provider errors.
        """
        pass

    def _track_latency(self, start_time: float) -> int:
        """Helper to calculate elapsed time in milliseconds."""
        return int((time.monotonic() - start_time) * 1000)

    async def _make_openai_compatible_request(
        self,
        url: str,
        headers: dict[str, str],
        payload: dict[str, Any],
        model: str,
        timeout_seconds: float,
    ) -> LLMResult:
        """Helper to make a request to any OpenAI-compatible API and parse the response."""
        start_time = time.monotonic()
        timeout = httpx.Timeout(timeout_seconds)

        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                response = await client.post(url, headers=headers, json=payload)
                response.raise_for_status()
        except httpx.HTTPError as exc:
            logger.error("%s provider HTTP error: %s", self.name, exc)
            raise LLMProviderError(f"{self.name} API error: {exc}") from exc

        data = response.json()
        try:
            choice = data["choices"][0]
            content = choice["message"]["content"]
            finish_reason = choice.get("finish_reason")
        except (KeyError, IndexError, TypeError) as exc:
            logger.error("%s response parsing error: %s", self.name, exc)
            raise LLMProviderError(f"Invalid response format from {self.name} API.") from exc

        if not isinstance(content, str) or not content.strip():
            raise LLMProviderError(f"{self.name} returned an empty response.")

        return LLMResult(
            content=content.strip(),
            provider=self.name,
            model=model,
            latency_ms=self._track_latency(start_time),
            finish_reason=finish_reason,
        )
