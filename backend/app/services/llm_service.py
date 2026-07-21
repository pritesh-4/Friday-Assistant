"""LLM Orchestrator: Manages fallback logic across multiple modular AI providers."""

from collections.abc import Sequence

from app.core.logging import get_logger
from app.services.providers.base import LLMProvider, LLMProviderError, LLMResult
from app.services.providers.gemini import GeminiProvider
from app.services.providers.groq import GroqProvider
from app.services.providers.nvidia import NvidiaProvider
from app.services.providers.openrouter import OpenRouterProvider

logger = get_logger(__name__)

# Expose these so chat_service doesn't break its imports.
__all__ = ["LLMProviderError", "LLMResult", "LLMService"]


class LLMService:
    """
    Orchestrate chat generation across multiple configured providers.
    
    Implements a resilient fallback chain. Prioritizes providers based on a
    hardcoded order designed to maximize free-tier capabilities, speed, and context.
    """

    def __init__(self) -> None:
        # Instantiate providers. They check their own `is_configured` property.
        self._providers: list[LLMProvider] = [
            GroqProvider(),       # Primary: Extremely low latency, capable Llama 3
            GeminiProvider(),     # Secondary: Highly reliable, huge context
            OpenRouterProvider(), # Tertiary: Standard API, access to diverse free tier
            NvidiaProvider(),     # Quaternary: NVIDIA's stable NIM endpoint
        ]

    @property
    def available_providers(self) -> list[LLMProvider]:
        """Returns the list of providers that have valid configuration keys."""
        return [p for p in self._providers if p.is_configured]

    async def generate_response(self, messages: Sequence[dict[str, str]]) -> LLMResult:
        """
        Generate a response using the first available provider.
        
        If a provider fails (e.g. rate limit, timeout), it gracefully logs the error
        and falls back to the next configured provider in the chain.
        """
        active = self.available_providers

        if not active:
            # The offline fallback is triggered when no keys are provided.
            return LLMResult(
                content=(
                    "I saved your message to this conversation. Configure at least one "
                    "provider (GROQ_API_KEY, GEMINI_API_KEY, OPENROUTER_API_KEY, or NVIDIA_API_KEY) "
                    "in backend/.env to enable AI-generated replies."
                ),
                provider="local-fallback",
                model="offline-storage",
                latency_ms=0,
                finish_reason="offline",
            )

        errors: list[str] = []

        for provider in active:
            try:
                logger.debug("Attempting inference with provider: %s", provider.name)
                return await provider.generate_response(messages)
            except LLMProviderError as exc:
                logger.warning(
                    "Provider '%s' failed. Falling back to next in chain. Error: %s",
                    provider.name,
                    str(exc),
                )
                errors.append(f"{provider.name}: {str(exc)}")
            except Exception as exc:
                logger.error(
                    "Unexpected error in provider '%s'. Falling back. Error: %s",
                    provider.name,
                    str(exc),
                    exc_info=True,
                )
                errors.append(f"{provider.name}: {str(exc)}")

        # If we exhausted the chain without a successful return, raise an aggregated error.
        error_summary = " | ".join(errors)
        raise LLMProviderError(f"All configured LLM providers failed. Details: {error_summary}")
