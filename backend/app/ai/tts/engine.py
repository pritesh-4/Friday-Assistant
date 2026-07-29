"""
Kokoro TTS inference engine wrapper.

Provides non-blocking async audio generation. Requires soundfile for WAV
encoding — which is also an optional dependency bundled in requirements-voice.txt.
"""

import asyncio
import io
import logging

from app.ai.tts.loader import get_tts_engine

logger = logging.getLogger(__name__)

# soundfile is bundled with requirements-voice.txt — guard the import.
try:
    import soundfile as sf

    _SOUNDFILE_AVAILABLE = True
except ImportError:
    sf = None  # type: ignore[assignment]
    _SOUNDFILE_AVAILABLE = False


class TTSEngine:
    """
    Wraps the Kokoro TTS engine to provide non-blocking asynchronous audio generation.
    """

    async def generate_audio(
        self, text: str, voice: str = "af_sarah", speed: float = 1.0
    ) -> bytes:
        """
        Synthesize text into a WAV audio payload.

        Runs in a thread pool executor to prevent blocking the asyncio event loop.

        Raises:
            RuntimeError: If the TTS engine or soundfile is not available.
        """
        engine = get_tts_engine()
        if engine is None:
            raise RuntimeError(
                "TTS engine is not available. "
                "Ensure VOICE_ENABLED=true and requirements-voice.txt is installed."
            )

        if not _SOUNDFILE_AVAILABLE:
            raise RuntimeError(
                "soundfile is not installed. "
                "Install requirements-voice.txt to enable audio encoding."
            )

        def _sync_generate() -> bytes:
            # Create audio stream (numpy array)
            samples, sample_rate = engine.create(
                text, voice=voice, speed=speed, lang="en-us"
            )

            # Write to in-memory bytes buffer as WAV
            out_buffer = io.BytesIO()
            sf.write(out_buffer, samples, sample_rate, format="wav")
            return out_buffer.getvalue()

        loop = asyncio.get_running_loop()
        audio_bytes = await loop.run_in_executor(None, _sync_generate)
        return audio_bytes
