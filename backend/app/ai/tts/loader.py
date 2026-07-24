"""
Kokoro TTS model loader and singleton management.

kokoro-onnx is an optional dependency. If it is not installed, all TTS
features are gracefully disabled. The server will still start and all
non-voice endpoints will function normally.

IMPORTANT: Model files are NOT downloaded at server startup. On ephemeral
filesystems (Render free tier), downloading large files at startup would:
  1. Block PORT binding, causing Render to mark the deploy as failed.
  2. Be wiped on every redeploy anyway.

To enable TTS:
  1. Install requirements-voice.txt
  2. Set VOICE_ENABLED=true
  3. Pre-download model files or set KOKORO_MODEL_PATH / KOKORO_VOICES_PATH
     to point to pre-existing files.

To use /tmp for downloaded models, set:
  KOKORO_MODEL_PATH=/tmp/friday/kokoro-v0_19.onnx
  KOKORO_VOICES_PATH=/tmp/friday/voices.json
"""

import os
import threading
from pathlib import Path

from app.core.logging import get_logger

_log = get_logger("tts.loader")

# Attempt to import kokoro-onnx. Degrade gracefully if not installed.
try:
    from kokoro_onnx import Kokoro as _Kokoro
    _KOKORO_AVAILABLE = True
except ImportError:
    _Kokoro = None  # type: ignore[assignment,misc]
    _KOKORO_AVAILABLE = False
    _log.warning(
        "kokoro-onnx is not installed. "
        "Text-to-speech features will be unavailable. "
        "Install requirements-voice.txt and set VOICE_ENABLED=true to enable TTS."
    )

# Global singleton
_tts_engine = None
_tts_lock = threading.Lock()


def is_tts_available() -> bool:
    """Return True if kokoro-onnx is installed."""
    return _KOKORO_AVAILABLE


def get_tts_engine():
    """
    Return the initialized Kokoro TTS engine singleton.
    Initializes the engine lazily in a thread-safe manner if it hasn't been loaded yet.

    Raises:
        RuntimeError: If TTS is not available or initialization fails.
    """
    global _tts_engine

    if not _KOKORO_AVAILABLE:
        raise RuntimeError(
            "TTS is not available. "
            "Ensure VOICE_ENABLED=true and kokoro-onnx is installed via requirements-voice.txt."
        )

    if _tts_engine is None:
        with _tts_lock:
            if _tts_engine is None:
                _log.info("Lazily initializing Kokoro TTS engine on first request...")
                success = initialize_tts_model()
                if not success or _tts_engine is None:
                    raise RuntimeError("Failed to initialize Kokoro TTS engine.")
                    
    return _tts_engine


def initialize_tts_model() -> bool:
    """
    Initialize the Kokoro TTS engine from pre-existing model files.

    Does NOT download model files — they must be available at the configured
    paths before this function is called. This keeps startup fast and
    compatible with ephemeral filesystems.

    Model file paths are resolved in the following order:
      1. KOKORO_MODEL_PATH / KOKORO_VOICES_PATH environment variables.
      2. Default: /tmp/friday/kokoro-v0_19.onnx and /tmp/friday/voices.json

    Returns:
        True if the engine was initialized successfully, False otherwise.
        Never raises.
    """
    global _tts_engine

    if not _KOKORO_AVAILABLE:
        _log.warning("Skipping TTS initialization — kokoro-onnx package not available.")
        return False

    if _tts_engine is not None:
        _log.debug("TTS engine is already initialized — skipping.")
        return True

    # Resolve model paths from env or defaults.
    default_model_dir = Path(os.environ.get("FRIDAY_DATA_DIR", "/tmp/friday"))
    model_path = Path(
        os.environ.get("KOKORO_MODEL_PATH", str(default_model_dir / "kokoro-v0_19.onnx"))
    )
    voices_path = Path(
        os.environ.get("KOKORO_VOICES_PATH", str(default_model_dir / "voices.json"))
    )

    if not model_path.exists():
        _log.warning(
            "Kokoro model file not found at '%s'. "
            "TTS is disabled. Set KOKORO_MODEL_PATH to the correct path.",
            model_path,
        )
        return False

    if not voices_path.exists():
        _log.warning(
            "Kokoro voices file not found at '%s'. "
            "TTS is disabled. Set KOKORO_VOICES_PATH to the correct path.",
            voices_path,
        )
        return False

    _log.info("Initializing Kokoro TTS engine from '%s'...", model_path)
    try:
        _tts_engine = _Kokoro(str(model_path), str(voices_path))
        _log.info("✓ Kokoro TTS engine initialized successfully.")
        return True
    except Exception as exc:
        # Never crash the server over a missing TTS model.
        _log.error(
            "Failed to initialize Kokoro TTS engine: %s — TTS features will be unavailable.",
            exc,
            exc_info=True,
        )
        return False
