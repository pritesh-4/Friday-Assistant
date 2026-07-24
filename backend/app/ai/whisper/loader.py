"""
Whisper model loader and singleton management.

faster-whisper is an optional dependency. If it is not installed (e.g. on
Render free tier where native binaries may be absent), all STT features are
gracefully disabled. The server will still start and all non-voice endpoints
will function normally.

To enable: install requirements-voice.txt and set VOICE_ENABLED=true.
"""

import threading
from app.core.logging import get_logger

_log = get_logger("whisper.loader")

# Attempt to import faster-whisper. If native libraries (ctranslate2, etc.)
# are not present, we degrade gracefully instead of crashing the server.
try:
    from faster_whisper import WhisperModel as _WhisperModel
    _FASTER_WHISPER_AVAILABLE = True
except ImportError:
    _WhisperModel = None  # type: ignore[assignment,misc]
    _FASTER_WHISPER_AVAILABLE = False
    _log.warning(
        "faster-whisper is not installed or its native libraries are missing. "
        "Speech-to-text features will be unavailable. "
        "Install requirements-voice.txt and set VOICE_ENABLED=true to enable STT."
    )


# The global singleton instance — None until successfully initialized.
_model_instance = None
_model_lock = threading.Lock()


def is_whisper_available() -> bool:
    """Return True if faster-whisper is installed."""
    return _FASTER_WHISPER_AVAILABLE


def get_whisper_model():
    """
    Return the loaded WhisperModel singleton instance.
    Initializes the model lazily in a thread-safe manner if it hasn't been loaded yet.

    Raises:
        RuntimeError: If faster-whisper is not installed or initialization fails.
    """
    global _model_instance

    if not _FASTER_WHISPER_AVAILABLE:
        raise RuntimeError(
            "Whisper model is not available. "
            "Ensure VOICE_ENABLED=true and faster-whisper is installed via requirements-voice.txt."
        )

    if _model_instance is None:
        with _model_lock:
            # Double-checked locking
            if _model_instance is None:
                _log.info("Lazily initializing Faster-Whisper model on first request...")
                success = initialize_whisper_model()
                if not success or _model_instance is None:
                    raise RuntimeError("Failed to initialize Faster-Whisper model.")
                    
    return _model_instance


def initialize_whisper_model(
    model_name: str = "distil-large-v3",
    device: str = "auto",
    compute_type: str = "default",
) -> bool:
    """
    Load the Faster-Whisper model.

    Returns:
        True if the model was loaded successfully, False otherwise.
    """
    global _model_instance

    if not _FASTER_WHISPER_AVAILABLE:
        _log.warning(
            "Skipping Whisper initialization — faster-whisper package not available."
        )
        return False

    if _model_instance is not None:
        _log.debug("Whisper model is already initialized — skipping.")
        return True

    _log.info(
        "Initializing Faster-Whisper model '%s' on device '%s' (compute: %s)",
        model_name,
        device,
        compute_type,
    )
    try:
        _model_instance = _WhisperModel(model_name, device=device, compute_type=compute_type)
        _log.info("✓ Faster-Whisper model loaded successfully.")
        return True
    except Exception as exc:
        # Log the full traceback for diagnostics, but do NOT re-raise.
        # A missing STT model must never crash the entire API server.
        _log.error(
            "Failed to load Faster-Whisper model: %s — STT features will be unavailable.",
            exc,
            exc_info=True,
        )
        return False
