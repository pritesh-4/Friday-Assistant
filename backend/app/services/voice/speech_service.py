import logging
import re
import time

from app.ai.tts.engine import TTSEngine

logger = logging.getLogger(__name__)


class SpeechService:
    """
    Business logic layer for handling Text-to-Speech requests.
    Validates, cleans text, delegates synthesis to the TTS Engine,
    and emits structured timing logs for observability.
    """

    def __init__(self):
        self.engine = TTSEngine()

    async def synthesize(self, text: str) -> bytes:
        """
        Takes raw text from the AI response, cleans out markdown syntax,
        and generates a WAV audio payload via the Kokoro TTS engine.

        Logs:
            [TTS] START  — when synthesis begins.
            [TTS] COMPLETE — when synthesis finishes, with duration and byte count.
        """
        # Remove markdown syntax (bold, italics, code, etc.) and structural chars.
        clean_text = re.sub(r"[*_~`#>\-\[\]()]", " ", text)
        clean_text = re.sub(r"\s+", " ", clean_text).strip()

        if not clean_text:
            logger.warning("[TTS] Synthesis requested for empty/fully-cleaned text.")
            raise ValueError("Text contains no speakable content.")

        logger.info(
            "[TTS] START: Synthesizing speech for %d characters.", len(clean_text)
        )
        start_time = time.time()

        audio_bytes = await self.engine.generate_audio(
            clean_text, voice="af_sarah", speed=1.0
        )

        elapsed = time.time() - start_time
        logger.info(
            "[TTS] COMPLETE: %d chars synthesized in %.2fs → %d bytes audio.",
            len(clean_text),
            elapsed,
            len(audio_bytes),
        )

        return audio_bytes
