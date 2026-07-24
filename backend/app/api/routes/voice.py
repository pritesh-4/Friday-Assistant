"""Voice routes — server-side speech-to-text and text-to-speech.

Endpoints:
  GET  /voice          — Capability status probe.
  POST /voice/upload   — Upload raw audio blob to temporary storage.
  POST /voice/transcribe — Transcribe audio using Faster-Whisper STT.
  POST /voice/speak    — Synthesize text to WAV audio using Kokoro TTS.

All endpoints check VOICE_ENABLED at runtime and return 503 with a clear
message if voice features are disabled. This prevents confusing 500 errors
when faster-whisper / kokoro-onnx are not installed.
"""

import logging
from pathlib import Path
from typing import Any

from fastapi import (
    APIRouter,
    Depends,
    File,
    HTTPException,
    Response,
    UploadFile,
    status,
)
from pydantic import BaseModel, field_validator

from app.api.dependencies import (
    get_speech_service,
    get_transcription_service,
    get_voice_service,
)
from app.core.config import settings
from app.schemas.voice import TranscriptionResult
from app.services.voice.speech_service import SpeechService
from app.services.voice.transcription_service import TranscriptionService
from app.services.voice_service import VoiceService

_log = logging.getLogger(__name__)
router = APIRouter(tags=["voice"])

# Maximum characters allowed for TTS synthesis.
_TTS_MAX_CHARS = 3_000

_VOICE_DISABLED_DETAIL = (
    "Voice features are disabled on this deployment. "
    "Set VOICE_ENABLED=true and install requirements-voice.txt to enable STT and TTS."
)


def _require_voice() -> None:
    """Raise HTTP 503 if VOICE_ENABLED is false."""
    if not settings.voice_enabled:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=_VOICE_DISABLED_DETAIL,
        )


@router.get("", summary="Voice capability status")
async def get_voice_status() -> dict[str, Any]:
    """
    Return the current availability of server-side voice features.
    This endpoint always responds — it does not raise 503 even when voice is disabled,
    so the frontend can check capability without error handling.
    """
    if not settings.voice_enabled:
        return {
            "available": False,
            "stt": None,
            "tts": None,
            "detail": _VOICE_DISABLED_DETAIL,
            "browser_fallback": True,
        }

    from app.ai.tts.loader import is_tts_available
    from app.ai.whisper.loader import is_whisper_available

    return {
        "available": True,
        "stt": "faster-whisper" if is_whisper_available() else "unavailable",
        "tts": "kokoro-onnx" if is_tts_available() else "unavailable",
        "detail": "Server-side STT and TTS status reported above.",
        "browser_fallback": not (is_whisper_available() and is_tts_available()),
    }

@router.get("/diagnostics", summary="Detailed Voice Diagnostics")
async def get_voice_diagnostics() -> dict[str, Any]:
    """
    Returns detailed system readiness for the voice subsystem.
    Matches the schema specifically requested for full observability.
    """
    import shutil
    ffmpeg_installed = shutil.which("ffmpeg") is not None
    
    from app.ai.whisper.loader import is_whisper_available, _model_instance, _whisper_import_error, _whisper_init_error
    whisper_installed = is_whisper_available()
    
    ctranslate2_installed = False
    try:
        import ctranslate2  # noqa: F401
        ctranslate2_installed = True
    except ImportError:
        pass
        
    model_loaded = _model_instance is not None
    ready = settings.voice_enabled and whisper_installed and ffmpeg_installed
    
    response = {
        "voice_enabled": settings.voice_enabled,
        "dependencies": {
            "faster_whisper": whisper_installed,
            "ctranslate2": ctranslate2_installed,
            "ffmpeg": ffmpeg_installed
        },
        "model": {
            "loaded": model_loaded,
            "name": "small",
            "cache": "data/models/whisper",
            "device": "cpu"
        },
        "ready": ready
    }
    
    if _whisper_import_error:
        response["import_error"] = _whisper_import_error
    if _whisper_init_error:
        response["init_error"] = _whisper_init_error
        
    return response


@router.post("/upload", summary="Upload a voice recording")
async def upload_voice(
    file: UploadFile = File(...),
    service: VoiceService = Depends(get_voice_service),
) -> dict:
    """
    Upload a voice recording to the temporary storage directory.
    Validates MIME type, file size, and handles saving securely.
    """
    _require_voice()
    return await service.upload_audio(file)


@router.post("/transcribe", summary="Transcribe audio to text", response_model=TranscriptionResult)
async def transcribe_voice(
    file: UploadFile = File(...),
    voice_service: VoiceService = Depends(get_voice_service),
    transcription_service: TranscriptionService = Depends(get_transcription_service),
) -> TranscriptionResult:
    """
    Transcribe an audio file to text using the Faster-Whisper STT provider.
    The uploaded audio file is deleted from disk after transcription.
    """
    _require_voice()

    import time
    start_time = time.time()
    _log.info("[VOICE] START POST /voice/transcribe")

    upload_result = await voice_service.upload_audio(file)
    file_path = voice_service.upload_dir / upload_result["filename"]
    _log.info(f"[VOICE] Upload complete: {file_path}")

    try:
        result = await transcription_service.transcribe(str(file_path))
    finally:
        try:
            Path(file_path).unlink(missing_ok=True)
        except Exception as exc:
            _log.warning("Failed to delete temporary audio file %s: %s", file_path, exc)

    elapsed = time.time() - start_time
    _log.info(f"[VOICE] SUCCESS POST /voice/transcribe in {elapsed:.2f}s")
    return TranscriptionResult(**result)


class SpeakRequest(BaseModel):
    text: str

    @field_validator("text")
    @classmethod
    def text_must_not_be_too_long(cls, v: str) -> str:
        if len(v) > _TTS_MAX_CHARS:
            raise ValueError(
                f"Text too long for TTS synthesis ({len(v)} chars). "
                f"Maximum is {_TTS_MAX_CHARS} characters."
            )
        return v


@router.post("/speak", summary="Synthesize text to speech")
async def speak_voice(
    request: SpeakRequest,
    speech_service: SpeechService = Depends(get_speech_service),
) -> Response:
    """
    Convert text to a WAV audio stream using the Kokoro TTS engine.
    Returns binary audio/wav. Maximum input is 3,000 characters.
    """
    _require_voice()
    
    import time
    start_time = time.time()
    _log.info("[VOICE] START POST /voice/speak")
    
    try:
        audio_bytes = await speech_service.synthesize(request.text)
        elapsed = time.time() - start_time
        _log.info(f"[VOICE] SUCCESS POST /voice/speak in {elapsed:.2f}s")
        return Response(content=audio_bytes, media_type="audio/wav")
    except ValueError as exc:
        _log.error(f"[VOICE] FAILURE POST /voice/speak - ValueError: {exc}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    except RuntimeError as exc:
        _log.error(f"[VOICE] FAILURE POST /voice/speak - RuntimeError: {exc}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)
        )
    except Exception as exc:
        _log.error(f"[VOICE] FAILURE POST /voice/speak - Exception: {exc}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"TTS synthesis failed: {exc!s}",
        )
