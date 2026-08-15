"""STT Provider Manager with automatic multi-provider fallback."""

from app.core.logging import get_logger
from app.services.providers.base_stt import BaseSTTProvider, STTProviderError
from app.services.providers.faster_whisper_stt import FasterWhisperProvider
from app.services.providers.openrouter_stt import OpenRouterWhisperTurbo

logger = get_logger(__name__)


class STTProviderManager:
    """
    Manages STT providers for speech-to-text transcription.

    Primary: OpenRouter Whisper Turbo (openai/whisper-large-v3-turbo)
    Fallback: Faster-Whisper local engine
    """

    def __init__(self) -> None:
        self.openrouter_provider = OpenRouterWhisperTurbo()
        self.faster_whisper_provider = FasterWhisperProvider()

    def _get_providers(self) -> list[BaseSTTProvider]:
        """Return ordered list of STT providers (primary first, then fallback)."""
        return [self.openrouter_provider, self.faster_whisper_provider]

    async def transcribe(
        self,
        audio_bytes: bytes,
        filename: str = "audio.webm",
        mime_type: str = "audio/webm",
        language: str | None = None,
    ) -> dict:
        """
        Transcribe audio using the primary STT provider, falling back to backup on failure.
        """
        providers = self._get_providers()
        errors = []

        for provider in providers:
            if not provider.is_configured:
                logger.debug("Skipping unconfigured STT provider: %s", provider.name)
                continue

            try:
                logger.info(
                    "[STT-MANAGER] Attempting transcription via provider '%s'...",
                    provider.name,
                )
                res = await provider.transcribe(
                    audio_bytes=audio_bytes,
                    filename=filename,
                    mime_type=mime_type,
                    language=language,
                )
                logger.info(
                    "[STT-MANAGER] Transcription SUCCESS via '%s': '%s'",
                    provider.name,
                    res.get("transcript", "")[:50],
                )
                return res
            except Exception as exc:
                logger.warning(
                    "[STT-MANAGER] Provider '%s' failed transcription: %s. Trying fallback...",
                    provider.name,
                    exc,
                )
                errors.append(f"{provider.name}: {exc}")

        error_msg = f"All STT providers failed. Details: {'; '.join(errors)}"
        logger.error("[STT-MANAGER] %s", error_msg)
        raise STTProviderError(error_msg)

    async def transcribe_array(self, float32_samples) -> dict:
        """
        Transcribe a 16kHz float32 numpy array directly via Faster-Whisper.
        """
        return await self.faster_whisper_provider.engine.transcribe_array(
            float32_samples
        )
