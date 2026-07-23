import asyncio
import io
import soundfile as sf
import logging
from app.ai.tts.loader import get_tts_engine

logger = logging.getLogger(__name__)

class TTSEngine:
    """
    Wraps the Kokoro TTS engine to provide non-blocking asynchronous audio generation.
    """
    
    async def generate_audio(self, text: str, voice: str = "af_sarah", speed: float = 1.0) -> bytes:
        """
        Synthesizes text into a WAV audio payload.
        Runs in a separate thread pool executor to prevent blocking the asyncio event loop.
        """
        engine = get_tts_engine()
        if not engine:
            logger.error("TTS Engine is not initialized.")
            raise RuntimeError("TTS Engine is not initialized or failed to load.")
            
        def _sync_generate():
            # Create audio stream (numpy array)
            samples, sample_rate = engine.create(text, voice=voice, speed=speed, lang="en-us")
            
            # Write out to in-memory bytes buffer as WAV
            out_buffer = io.BytesIO()
            sf.write(out_buffer, samples, sample_rate, format='wav')
            
            return out_buffer.getvalue()
            
        loop = asyncio.get_running_loop()
        # Run inference in a background thread
        audio_bytes = await loop.run_in_executor(None, _sync_generate)
        return audio_bytes
