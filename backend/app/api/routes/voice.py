"""Voice routes — server-side speech-to-text and text-to-speech.

Endpoints:
  GET  /voice          — Capability status probe.
  POST /voice/upload   — Upload raw audio blob to temporary storage.
  POST /voice/transcribe — Transcribe audio using Faster-Whisper STT.
  POST /voice/speak    — Synthesize text to WAV audio using Kokoro TTS.
"""

import logging
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Response
from pydantic import BaseModel, field_validator

from app.api.dependencies import get_voice_service, get_transcription_service, get_speech_service
from app.services.voice_service import VoiceService
from app.services.voice.transcription_service import TranscriptionService
from app.services.voice.speech_service import SpeechService
from app.schemas.voice import TranscriptionResult

_log = logging.getLogger(__name__)
router = APIRouter(tags=["voice"])

# Maximum characters allowed for TTS synthesis.
# Long text causes the thread-pool executor to run for seconds and starves other requests.
_TTS_MAX_CHARS = 3_000


@router.get("", summary="Voice capability status")
async def get_voice_status(
    service: VoiceService = Depends(get_voice_service),
) -> dict[str, bool | str]:
    """
    Return the current availability of server-side voice features.
    Both STT (Faster-Whisper) and TTS (Kokoro) are active when the models
    were loaded successfully during application startup.
    """
    return {
        "available": True,
        "stt": "faster-whisper",
        "tts": "kokoro-onnx",
        "detail": "Server-side STT and TTS are enabled.",
        "browser_fallback": False,
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
    # Save the uploaded file
    upload_result = await voice_service.upload_audio(file)
    file_path = voice_service.upload_dir / upload_result["filename"]

    try:
        result = await transcription_service.transcribe(str(file_path))
    finally:
        # Always clean up the temporary audio file after transcription.
        # This prevents unbounded disk growth on every voice message.
        try:
            Path(file_path).unlink(missing_ok=True)
        except Exception as e:
            _log.warning("Failed to delete temporary audio file %s: %s", file_path, e)

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
    try:
        audio_bytes = await speech_service.synthesize(request.text)
        return Response(content=audio_bytes, media_type="audio/wav")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"TTS synthesis failed: {str(e)}")

