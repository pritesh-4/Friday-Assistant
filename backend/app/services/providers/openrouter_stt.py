"""OpenRouter Whisper Turbo STT Provider implementation."""

import logging
from app.core.config import settings
from app.services.providers.base_stt import BaseSTTProvider, STTProviderError
from app.services.providers.openrouter_client import (
    OpenRouterAudioClient,
    OpenRouterAudioError,
)

logger = logging.getLogger(__name__)

ALLOWED_STT_MIME_TYPES = {
    "audio/webm",
    "audio/ogg",
    "audio/wav",
    "audio/x-wav",
    "audio/mp4",
    "audio/mpeg",
    "audio/flac",
}


class OpenRouterWhisperTurbo(BaseSTTProvider):
    """
    OpenRouter STT Provider using openai/whisper-large-v3-turbo.
    """

    def __init__(self) -> None:
        self.client = OpenRouterAudioClient()

    @property
    def name(self) -> str:
        return "openrouter_whisper"

    @property
    def is_configured(self) -> bool:
        return bool(settings.openrouter_api_key)

    def validate_audio(self, audio_bytes: bytes, mime_type: str = "audio/webm") -> None:
        """
        Validate audio payload before sending to STT API.
        """
        if not audio_bytes or len(audio_bytes) < 100:
            raise STTProviderError("Audio payload is empty or too small to transcribe.")

        if len(audio_bytes) > settings.max_upload_size_bytes:
            raise STTProviderError(
                f"Audio payload exceeds maximum size ({len(audio_bytes)} > {settings.max_upload_size_bytes} bytes)."
            )

        clean_mime = mime_type.split(";")[0].strip().lower()
        if clean_mime not in ALLOWED_STT_MIME_TYPES:
            raise STTProviderError(
                f"Unsupported audio MIME type for STT: '{mime_type}'."
            )

    async def transcribe(
        self,
        audio_bytes: bytes,
        filename: str = "audio.webm",
        mime_type: str = "audio/webm",
        language: str | None = None,
    ) -> dict:
        if not self.is_configured:
            raise STTProviderError(
                "OpenRouter STT is not configured (missing OPENROUTER_API_KEY)."
            )

        self.validate_audio(audio_bytes, mime_type=mime_type)

        model_name = "openai/whisper-large-v3-turbo"

        try:
            res_data = await self.client.transcribe_audio(
                audio_bytes=audio_bytes,
                filename=filename,
                mime_type=mime_type.split(";")[0].strip().lower(),
                model=model_name,
            )

            text = res_data.get("text", "") or res_data.get("transcript", "")
            return {
                "transcript": text.strip(),
                "detected_language": res_data.get("language", "en"),
                "confidence": 0.99,
                "duration": 0.0,
                "provider": self.name,
                "model": model_name,
            }

        except OpenRouterAudioError as exc:
            logger.warning("[STT-OPENROUTER] Transcription failed: %s", exc)
            raise STTProviderError(str(exc)) from exc
