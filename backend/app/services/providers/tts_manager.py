"""TTS Provider Manager for managing Text-to-Speech synthesis."""

from typing import AsyncGenerator

from app.core.config import settings
from app.core.logging import get_logger
from app.services.providers.base_tts import BaseTTSProvider, TTSProviderError
from app.services.providers.openrouter_tts import OpenRouterTTSProvider

logger = get_logger(__name__)


class TTSProviderManager:
    """
    Manages TTS providers for speech synthesis.

    Primary Provider: OpenRouter TTS (Fish Audio S2.1 Pro Free)
    """

    def __init__(self) -> None:
        self.openrouter_provider = OpenRouterTTSProvider()

    def get_active_provider_info(self) -> dict[str, str | bool]:
        """Return diagnostic readiness of configured TTS providers."""
        if self.openrouter_provider.is_configured:
            return {
                "active_provider": "openrouter",
                "model": settings.friday_tts_model,
                "voice": settings.friday_tts_voice,
                "format": settings.friday_tts_format,
                "available": True,
            }
        else:
            return {
                "active_provider": "none",
                "model": "none",
                "voice": "none",
                "format": "none",
                "available": False,
            }

    def _get_providers(self) -> list[BaseTTSProvider]:
        """Resolve list of active providers."""
        return [self.openrouter_provider]

    async def synthesize(
        self,
        text: str,
        voice: str | None = None,
        response_format: str | None = None,
    ) -> tuple[bytes, str, str]:
        """
        Synthesize speech from text using the configured TTS provider.

        Returns:
            Tuple of (audio_bytes, media_type, provider_name)
        """
        target_format = response_format or settings.friday_tts_format
        providers = self._get_providers()
        errors = []

        for provider in providers:
            if not provider.is_configured:
                logger.debug("Skipping unconfigured TTS provider: %s", provider.name)
                continue

            try:
                logger.info(
                    "[TTS-MANAGER] Attempting synthesis via provider '%s'...",
                    provider.name,
                )
                audio_bytes = await provider.synthesize(
                    text, voice=voice, response_format=target_format
                )
                media_type = "audio/mpeg" if target_format == "mp3" else "audio/wav"
                logger.info(
                    "[TTS-MANAGER] Synthesis SUCCESS via provider '%s' (%d bytes, %s).",
                    provider.name,
                    len(audio_bytes),
                    media_type,
                )
                return audio_bytes, media_type, provider.name
            except Exception as exc:
                logger.warning(
                    "[TTS-MANAGER] Provider '%s' failed synthesis: %s.",
                    provider.name,
                    exc,
                )
                errors.append(f"{provider.name}: {exc}")

        error_msg = f"All TTS providers failed. Details: {'; '.join(errors)}"
        logger.error("[TTS-MANAGER] %s", error_msg)
        raise TTSProviderError(error_msg)

    async def stream_synthesize(
        self,
        text: str,
        voice: str | None = None,
        response_format: str | None = None,
    ) -> tuple[AsyncGenerator[bytes, None], str, str]:
        """
        Stream audio bytes from configured TTS provider.

        Returns:
            Tuple of (audio_bytes_generator, media_type, provider_name)
        """
        target_format = response_format or settings.friday_tts_format
        providers = self._get_providers()
        errors = []

        for provider in providers:
            if not provider.is_configured:
                continue

            try:
                gen = provider.stream_synthesize(
                    text, voice=voice, response_format=target_format
                )
                media_type = "audio/mpeg" if target_format == "mp3" else "audio/wav"
                return gen, media_type, provider.name
            except Exception as exc:
                logger.warning(
                    "[TTS-MANAGER] Provider '%s' failed to initialize stream: %s.",
                    provider.name,
                    exc,
                )
                errors.append(f"{provider.name}: {exc}")

        error_msg = f"All TTS providers failed streaming. Details: {'; '.join(errors)}"
        raise TTSProviderError(error_msg)
