"""Abstract base class and models for all LLM providers."""

import time
from abc import ABC, abstractmethod
from typing import Any, Sequence
from dataclasses import dataclass

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
