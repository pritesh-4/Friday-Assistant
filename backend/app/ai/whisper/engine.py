"""
Whisper inference engine wrapper.

Provides non-blocking async speech-to-text transcription.
Implemented as a thread-safe Singleton to ensure the model
is loaded exactly once across the application lifecycle.
"""

import asyncio
import threading
import traceback
import sys
from typing import Any

from app.core.config import settings
from app.core.logging import get_logger

_log = get_logger("whisper.engine")


class WhisperEngine:
    """
    Wrapper around Faster-Whisper for Speech-to-Text inference.
    Implemented as a thread-safe Singleton.
    """
    
    _instance = None
    _lock = threading.Lock()

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            with cls._lock:
                if not cls._instance:
                    cls._instance = super(WhisperEngine, cls).__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self, model_name: str = "small", device: str = "auto", compute_type: str = "default"):
        if self._initialized:
            return
            
        self.model_name = model_name
        self.device = device
        self.compute_type = compute_type
        self.model = None
        self._model_lock = threading.Lock()
        self._initialized = True

    @property
    def is_loaded(self) -> bool:
        return self.model is not None

    def load_model(self) -> None:
        """
        Lazily initialize the Faster-Whisper model in a thread-safe manner.
        """
        if self.model is not None:
            return

        with self._model_lock:
            # Double-checked locking
            if self.model is not None:
                return
                
            _log.info("[VOICE] Lazily initializing Faster-Whisper model on first request...")
            _log.info("Loading Whisper...")
            _log.info(
                "Loading Model... (model='%s', device='%s', compute='%s')",
                self.model_name,
                self.device,
                self.compute_type,
            )
            
            try:
                from faster_whisper import WhisperModel
                
                _log.info("Downloading...")
                _log.info("Initializing...")
                self.model = WhisperModel(
                    self.model_name, 
                    device=self.device, 
                    compute_type=self.compute_type
                )
                _log.info("SUCCESS")
            except Exception as exc:
                exc_type, exc_value, exc_traceback = sys.exc_info()
                tb = traceback.extract_tb(exc_traceback)
                last_call = tb[-1] if tb else None
                
                _log.error(
                    "[VOICE] FAILED\n"
                    f"Exception type: {exc_type.__name__ if exc_type else 'Unknown'}\n"
                    f"Message: {exc}\n"
                    f"Stack trace: {traceback.format_exc()}\n"
                    f"Failing package: {last_call.filename if last_call else 'Unknown'}\n"
                    f"Failing file: {last_call.filename if last_call else 'Unknown'}\n"
                    f"Failing line: {last_call.lineno if last_call else 'Unknown'}"
                )
                raise RuntimeError(f"Failed to initialize Faster-Whisper model: {exc}") from exc

    async def transcribe(self, audio_path: str) -> dict[str, Any]:
        """
        Transcribe an audio file using Faster-Whisper.

        Args:
            audio_path: Path to the audio file on disk.

        Returns:
            A dictionary containing transcript, detected_language, confidence,
            duration, segments, and metadata.
        """
        if not settings.voice_enabled:
            raise RuntimeError("Voice is disabled but transcription was requested.")

        # Ensure the model is loaded before inferencing
        self.load_model()

        # Run CPU/GPU-bound transcription in a thread to avoid blocking the event loop.
        loop = asyncio.get_running_loop()
        
        _log.info("[VOICE] Decoding audio...")
        try:
            segments_generator, info = await loop.run_in_executor(
                None,
                lambda: self.model.transcribe(audio_path, beam_size=5),
            )
        except Exception as exc:
            _log.error("[VOICE] Failed during audio decoding or model inference", exc_info=True)
            raise RuntimeError(f"Audio decoding failed: {exc}") from exc
            
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
            raise RuntimeError(f"Segment extraction failed: {exc}") from exc
            
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
