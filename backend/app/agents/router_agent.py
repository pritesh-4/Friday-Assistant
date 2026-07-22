from app.core.config import settings
from app.core.logging import get_logger
from app.services.llm_service import LLMService
from app.services.providers.base import LLMProviderError, LLMResult

logger = get_logger(__name__)

class RouterAgent:
    """Routes the incoming request to the appropriate LLM provider based on configuration."""

    def __init__(self) -> None:
        self.llm_service = LLMService()

    async def route_and_execute(self, messages: list[dict[str, str]]) -> LLMResult:
        """
        Selects a provider from the fallback chain and executes it.
        Falls back to the next provider if one fails.
        """
        # Start with configured fallback chain, dropping duplicates
        chain = []
        for p in settings.fallback_chain:
            if p not in chain:
                chain.append(p)

        active_providers = self.llm_service.available_providers
        if not active_providers:
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

        # Try providers in the configured order
        for provider_name in chain:
            provider = self.llm_service.get_provider(provider_name)
            if not provider:
                continue

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
        
        # If the configured chain fails, try any other active provider
        for provider_name, provider in active_providers.items():
            if provider_name in chain:
                continue
            
            try:
                logger.debug("Attempting inference with fallback provider: %s", provider.name)
                return await provider.generate_response(messages)
            except Exception as exc:
                errors.append(f"{provider.name}: {str(exc)}")

        error_summary = " | ".join(errors)
        raise LLMProviderError(f"All configured LLM providers failed. Details: {error_summary}")
