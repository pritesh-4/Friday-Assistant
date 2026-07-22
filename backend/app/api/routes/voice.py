"""Voice route — server-side speech capabilities (planned milestone).

Current status: voice processing runs entirely in the browser (Web Speech API).
Server-side STT/TTS is a planned future milestone.  These endpoints are
intentionally present to:
  1. Document the intended API surface.
  2. Allow the frontend to query capability status before attempting a call.
  3. Provide a clear extension point for the VoiceService implementation.
"""

from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File

from app.api.dependencies import get_voice_service
from app.services.voice_service import VoiceService

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
        "available": False,
        "detail": "Server-side voice is planned for a future milestone.",
        "browser_fallback": True,
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


@router.post("/transcribe", summary="Transcribe audio to text")
async def transcribe_voice(
    service: VoiceService = Depends(get_voice_service),
) -> None:
    """
    Transcribe an audio file to text using the configured STT provider.

    **Not yet implemented.** Browser-side Web Speech API is the current
    transcription mechanism.
    """
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Server-side speech transcription is not implemented yet.",
    )


@router.post("/synthesize", summary="Synthesize text to speech")
async def synthesize_voice(
    service: VoiceService = Depends(get_voice_service),
) -> None:
    """
    Convert text to an audio stream using the configured TTS provider.

    **Not yet implemented.** Browser-side SpeechSynthesis API is the current
    TTS mechanism.
    """
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Server-side speech synthesis is not implemented yet.",
    )
