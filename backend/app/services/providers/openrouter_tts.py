"""OpenRouter Text-to-Speech (TTS) Provider implementation."""

from typing import AsyncGenerator

from app.core.config import settings
from app.services.providers.base_tts import BaseTTSProvider, TTSProviderError
from app.services.providers.openrouter_client import (
    OpenRouterAudioClient,
    OpenRouterAudioError,
)


class OpenRouterTTSProvider(BaseTTSProvider):
    """
    OpenRouter TTS Provider.

    Encapsulates authentication, model selection, voice selection, audio format,
    request construction, streaming, and error handling for OpenRouter TTS.
    """

    def __init__(self) -> None:
        self.client = OpenRouterAudioClient()

    @property
    def name(self) -> str:
        return "openrouter"

    @property
    def is_configured(self) -> bool:
        return bool(settings.openrouter_api_key)

    async def synthesize(
        self,
        text: str,
        voice: str | None = None,
        response_format: str | None = None,
    ) -> bytes:
        if not self.is_configured:
            raise TTSProviderError(
                "OpenRouter TTS is not configured (missing OPENROUTER_API_KEY)."
            )

        clean_text = text.strip()
        if not clean_text:
            raise TTSProviderError("Empty or blank text provided for TTS synthesis.")

        target_model = settings.friday_tts_model
        target_voice = voice or settings.friday_tts_voice
        target_format = response_format or settings.friday_tts_format

        try:
            return await self.client.synthesize_speech(
                text=clean_text,
                voice=target_voice,
                response_format=target_format,
                model=target_model,
            )
        except OpenRouterAudioError as exc:
            raise TTSProviderError(str(exc)) from exc

    async def stream_synthesize(
        self,
        text: str,
        voice: str | None = None,
        response_format: str | None = None,
    ) -> AsyncGenerator[bytes, None]:
        if not self.is_configured:
            raise TTSProviderError(
                "OpenRouter TTS is not configured (missing OPENROUTER_API_KEY)."
            )

        clean_text = text.strip()
        if not clean_text:
            raise TTSProviderError("Empty or blank text provided for TTS synthesis.")

        target_model = settings.friday_tts_model
        target_voice = voice or settings.friday_tts_voice
        target_format = response_format or settings.friday_tts_format

        try:
            async for chunk in self.client.stream_speech(
                text=clean_text,
                voice=target_voice,
                response_format=target_format,
                model=target_model,
            ):
                yield chunk
        except OpenRouterAudioError as exc:
            raise TTSProviderError(str(exc)) from exc
