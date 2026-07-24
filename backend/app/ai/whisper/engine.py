"""
Whisper inference engine wrapper.

Provides non-blocking async speech-to-text transcription. Requires
faster-whisper — which is an optional dependency in requirements-voice.txt.
"""

import asyncio
from typing import Any

from app.ai.whisper.loader import get_whisper_model, is_whisper_available
from app.core.logging import get_logger

_log = get_logger("whisper.engine")


class WhisperEngine:
    """
    Wrapper around Faster-Whisper for Speech-to-Text inference.
    The model singleton is managed by the loader module.
    """

    async def transcribe(self, audio_path: str) -> dict[str, Any]:
        """
        Transcribe an audio file using Faster-Whisper.

        Args:
            audio_path: Path to the audio file on disk.

        Returns:
            A dictionary containing transcript, detected_language, confidence,
            duration, segments, and metadata.

        Raises:
            RuntimeError: If faster-whisper is not installed or model not loaded.
        """
        if not is_whisper_available():
            raise RuntimeError(
                "Whisper model is not available. "
                "Ensure VOICE_ENABLED=true and requirements-voice.txt is installed."
            )

        model = get_whisper_model()

        # Run CPU/GPU-bound transcription in a thread to avoid blocking the event loop.
        loop = asyncio.get_running_loop()
        
        _log.info("[VOICE] Decoding audio...")
        try:
            segments_generator, info = await loop.run_in_executor(
                None,
                lambda: model.transcribe(audio_path, beam_size=5),
            )
        except Exception as exc:
            _log.error("[VOICE] Failed during audio decoding or model initialization", exc_info=True)
            raise
            
        _log.info("[VOICE] Audio decoded. Detected language '%s' with probability %.2f", info.language, info.language_probability)
        _log.info("[VOICE] Running inference...")

        # Collect the lazy generator — must be done in the same thread context.
        def collect_segments() -> tuple[list[dict[str, Any]], str]:
            collected: list[dict[str, Any]] = []
            full_text = ""
            for segment in segments_generator:
                collected.append(
                    {
                        "id": segment.id,
                        "start": segment.start,
                        "end": segment.end,
                        "text": segment.text.strip(),
                    }
                )
                full_text += segment.text
            return collected, full_text.strip()

        try:
            segments, transcript = await loop.run_in_executor(None, collect_segments)
        except Exception as exc:
            _log.error("[VOICE] Failed during inference or segment extraction", exc_info=True)
            raise
            
        _log.info("[VOICE] Inference complete")

        return {
            "transcript": transcript,
            "detected_language": info.language,
            "confidence": info.language_probability,
            "duration": info.duration,
            "segments": segments,
            "metadata": {
                "all_language_probs": (
                    info.all_language_probs if hasattr(info, "all_language_probs") else None
                )
            },
        }
