"""Abstract base class and exceptions for STT providers."""

from abc import ABC, abstractmethod


class STTProviderError(RuntimeError):
    """Raised when an STT provider fails to transcribe audio."""


class BaseSTTProvider(ABC):
    """
    Abstract Base Class for all Speech-to-Text (STT) providers.
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Identifier of the STT provider (e.g., 'openrouter_whisper', 'faster_whisper')."""

    @property
    @abstractmethod
    def is_configured(self) -> bool:
        """Return True if provider credentials/models are ready."""

    @abstractmethod
    async def transcribe(
        self,
        audio_bytes: bytes,
        filename: str = "audio.webm",
        mime_type: str = "audio/webm",
        language: str | None = None,
    ) -> dict:
        """
        Transcribe audio bytes to text.

        Returns:
            Dict containing transcript and metadata:
            {
                "transcript": str,
                "detected_language": str,
                "confidence": float,
                "duration": float,
                "provider": str
            }
        """
