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

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Response, status
from pydantic import BaseModel, field_validator

from app.api.dependencies import get_voice_service, get_transcription_service, get_speech_service
from app.core.config import settings
from app.services.voice_service import VoiceService
from app.services.voice.transcription_service import TranscriptionService
from app.services.voice.speech_service import SpeechService
from app.schemas.voice import TranscriptionResult

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
    from app.ai.whisper.loader import is_whisper_available
    from app.ai.tts.loader import is_tts_available

    if not settings.voice_enabled:
        return {
            "available": False,
            "stt": None,
            "tts": None,
            "detail": _VOICE_DISABLED_DETAIL,
            "browser_fallback": True,
        }

    return {
        "available": True,
        "stt": "faster-whisper" if is_whisper_available() else "unavailable",
        "tts": "kokoro-onnx" if is_tts_available() else "unavailable",
        "detail": "Server-side STT and TTS status reported above.",
        "browser_fallback": not (is_whisper_available() and is_tts_available()),
    }


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

    upload_result = await voice_service.upload_audio(file)
    file_path = voice_service.upload_dir / upload_result["filename"]

    try:
        result = await transcription_service.transcribe(str(file_path))
    finally:
        try:
            Path(file_path).unlink(missing_ok=True)
        except Exception as exc:
            _log.warning("Failed to delete temporary audio file %s: %s", file_path, exc)

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
    try:
        audio_bytes = await speech_service.synthesize(request.text)
        return Response(content=audio_bytes, media_type="audio/wav")
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    except RuntimeError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"TTS synthesis failed: {str(exc)}",
        )
