"""LLM Orchestrator: Manages fallback logic across multiple modular AI providers."""


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
    Provider Registry: Maintains configured LLM providers.
    Routing logic is now handled by the RouterAgent.
    """

    def __init__(self) -> None:
        # Instantiate all known providers.
        self._providers: dict[str, LLMProvider] = {
            "groq": GroqProvider(),
            "gemini": GeminiProvider(),
            "openrouter": OpenRouterProvider(),
            "nvidia": NvidiaProvider(),
        }

    @property
    def available_providers(self) -> dict[str, LLMProvider]:
        """Returns the dictionary of providers that have valid configuration keys."""
        return {name: p for name, p in self._providers.items() if p.is_configured}

    def get_provider(self, name: str) -> LLMProvider | None:
        """Get a specific configured provider by name."""
        provider = self._providers.get(name)
        if provider and provider.is_configured:
            return provider
        return None

    def get_fallback_provider(self) -> LLMProvider | None:
        """Get the first available provider from the configured providers if the requested one fails."""
        active = self.available_providers
        if not active:
            return None
        return next(iter(active.values()))

