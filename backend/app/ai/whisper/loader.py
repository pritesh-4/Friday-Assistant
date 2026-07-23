"""
Whisper model loader and singleton management.
"""
from faster_whisper import WhisperModel
from app.core.logging import get_logger

_log = get_logger("whisper.loader")

# The global singleton instance
_model_instance: WhisperModel | None = None

def get_whisper_model() -> WhisperModel:
    """
    Get the loaded WhisperModel singleton instance.
    Raises ValueError if not loaded yet.
    """
    global _model_instance
    if _model_instance is None:
        raise ValueError("Whisper model is not initialized. Call initialize_whisper_model() during startup.")
    return _model_instance

def initialize_whisper_model(model_name: str = "distil-large-v3", device: str = "auto", compute_type: str = "default") -> None:
    """
    Load the Faster-Whisper model.
    This should be called exactly once during the application lifespan startup.
    """
    global _model_instance
    if _model_instance is not None:
        _log.warning("Whisper model is already initialized.")
        return
        
    _log.info("Initializing Faster-Whisper model '%s' on device '%s' (compute: %s)", model_name, device, compute_type)
    try:
        _model_instance = WhisperModel(model_name, device=device, compute_type=compute_type)
        _log.info("Faster-Whisper model loaded successfully.")
    except Exception as e:
        _log.error("Failed to load Faster-Whisper model: %s", e, exc_info=True)
        # Re-raise so the app startup fails fast if STT is a core component.
        raise
