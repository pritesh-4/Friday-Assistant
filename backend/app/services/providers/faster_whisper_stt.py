"""Faster-Whisper local STT Provider wrapper."""

import logging
from app.ai.whisper.engine import WhisperEngine
from app.services.providers.base_stt import BaseSTTProvider, STTProviderError

logger = logging.getLogger(__name__)


class FasterWhisperProvider(BaseSTTProvider):
    """
    Faster-Whisper local STT Provider.
    """

    def __init__(self) -> None:
        self.engine = WhisperEngine()

    @property
    def name(self) -> str:
        return "faster_whisper"

    @property
    def is_configured(self) -> bool:
        return self.engine.is_loaded or True  # Engine lazy-loads model

    async def transcribe(
        self,
        audio_bytes: bytes,
        filename: str = "audio.webm",
        mime_type: str = "audio/webm",
        language: str | None = None,
    ) -> dict:
        if not audio_bytes:
            raise STTProviderError("Empty audio payload provided.")

        try:
            # If audio_bytes is passed directly, transcribe via temporary file or array
            import tempfile
            import os

            ext = os.path.splitext(filename)[1] or ".webm"
            with tempfile.NamedTemporaryFile(suffix=ext, delete=False) as tmp:
                tmp.write(audio_bytes)
                tmp_path = tmp.name

            try:
                res = await self.engine.transcribe(tmp_path)
                res["provider"] = self.name
                return res
            finally:
                try:
                    os.unlink(tmp_path)
                except Exception:
                    pass

        except Exception as exc:
            logger.error("[STT-FASTER-WHISPER] Local transcription failed: %s", exc)
            raise STTProviderError(f"Faster-Whisper STT failed: {exc}") from exc
