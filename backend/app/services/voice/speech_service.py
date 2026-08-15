import logging
import re
import time
from typing import AsyncGenerator

from app.services.providers.tts_manager import TTSProviderManager

logger = logging.getLogger(__name__)


class SpeechService:
    """
    Business logic layer for handling Text-to-Speech requests.
    Validates, cleans text, delegates synthesis to the TTS Provider Manager,
    and emits structured timing logs for observability.
    """

    def __init__(self):
        self.manager = TTSProviderManager()

    async def synthesize(self, text: str) -> bytes:
        """
        Takes raw text from the AI response, cleans out markdown syntax,
        and generates an audio payload via the active TTS provider.

        Returns:
            Raw audio bytes (audio/mpeg or audio/wav).
        """
        audio_bytes, _, _ = await self.synthesize_with_metadata(text)
        return audio_bytes

    async def synthesize_with_metadata(self, text: str) -> tuple[bytes, str, str]:
        """
        Takes raw text, cleans markdown syntax, synthesizes audio via TTS Provider Manager,
        and returns (audio_bytes, media_type, provider_name).
        """
        clean_text = re.sub(r"[*_~`#>\-\[\]()]", " ", text)
        clean_text = re.sub(r"\s+", " ", clean_text).strip()

        if not clean_text:
            logger.warning("[TTS] Synthesis requested for empty/fully-cleaned text.")
            raise ValueError("Text contains no speakable content.")

        logger.info(
            "[TTS] START: Synthesizing speech for %d characters.", len(clean_text)
        )
        start_time = time.time()

        audio_bytes, media_type, provider_name = await self.manager.synthesize(
            clean_text
        )

        elapsed = time.time() - start_time
        logger.info(
            "[TTS] COMPLETE [%s]: %d chars synthesized in %.2fs → %d bytes audio (%s).",
            provider_name,
            len(clean_text),
            elapsed,
            len(audio_bytes),
            media_type,
        )

        return audio_bytes, media_type, provider_name

    async def stream_synthesize(
        self, text: str
    ) -> tuple[AsyncGenerator[bytes, None], str, str]:
        """
        Clean text and return an asynchronous audio chunk generator and media type.
        """
        clean_text = re.sub(r"[*_~`#>\-\[\]()]", " ", text)
        clean_text = re.sub(r"\s+", " ", clean_text).strip()

        if not clean_text:
            raise ValueError("Text contains no speakable content.")

        return await self.manager.stream_synthesize(clean_text)
