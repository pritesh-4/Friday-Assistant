"""Voice route — server-side speech capabilities (planned milestone).

Current status: voice processing runs entirely in the browser (Web Speech API).
Server-side STT/TTS is a planned future milestone.  These endpoints are
intentionally present to:
  1. Document the intended API surface.
  2. Allow the frontend to query capability status before attempting a call.
  3. Provide a clear extension point for the VoiceService implementation.
"""

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Response
from pydantic import BaseModel

from app.api.dependencies import get_voice_service, get_transcription_service, get_speech_service
from app.services.voice_service import VoiceService
from app.services.voice.transcription_service import TranscriptionService
from app.services.voice.speech_service import SpeechService
from app.schemas.voice import TranscriptionResult

router = APIRouter(tags=["voice"])


@router.get("", summary="Voice capability status")
async def get_voice_status(
    service: VoiceService = Depends(get_voice_service),
) -> dict[str, bool | str]:
    """
    Return the current availability of server-side voice features.

    When ``available`` is ``false``, clients should use browser-native APIs
    (e.g. Web Speech API) instead of routing through this endpoint.
    """
    return {
        "available": True,
        "detail": "Server-side Faster-Whisper transcription is enabled.",
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
    """
    # Integrate with existing upload workflow
    upload_result = await voice_service.upload_audio(file)
    file_path = voice_service.upload_dir / upload_result["filename"]
    
    # Process transcription
    result = await transcription_service.transcribe(str(file_path))
    
    return TranscriptionResult(**result)



class SpeakRequest(BaseModel):
    text: str

@router.post("/speak", summary="Synthesize text to speech")
async def speak_voice(
    request: SpeakRequest,
    speech_service: SpeechService = Depends(get_speech_service),
) -> Response:
    """
    Convert text to an audio stream (WAV) using the Kokoro TTS engine.
    Returns binary audio/wav.
    """
    try:
        audio_bytes = await speech_service.synthesize(request.text)
        return Response(content=audio_bytes, media_type="audio/wav")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"TTS synthesis failed: {str(e)}")
