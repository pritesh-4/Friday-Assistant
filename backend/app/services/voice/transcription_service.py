import time
from typing import Any

from fastapi import HTTPException, UploadFile, status

from app.core.config import settings
from app.core.logging import get_logger
from app.services.providers.stt_manager import STTProviderManager

_log = get_logger("transcription_service")

ALLOWED_MIME_TYPES = {
    "audio/webm",
    "audio/ogg",
    "audio/wav",
    "audio/x-wav",
    "audio/mp4",
    "audio/mpeg",
    "audio/flac",
}

ALLOWED_EXTENSIONS = {
    ".webm",
    ".ogg",
    ".wav",
    ".mp4",
    ".m4a",
    ".mp3",
    ".mpeg",
    ".flac",
}

MAX_FILE_SIZE = settings.max_upload_size_bytes


class TranscriptionService:
    """
    Service for handling the transcription lifecycle using STTProviderManager
    (Primary: OpenRouter Whisper Turbo, Fallback: Faster-Whisper local engine).
    """

    def __init__(self):
        self.stt_manager = STTProviderManager()
        self.upload_dir = settings.voice_uploads_directory
        self.upload_dir.mkdir(parents=True, exist_ok=True)

    @property
    def engine(self):
        """Backward compatibility helper returning local Faster-Whisper engine."""
        return self.stt_manager.faster_whisper_provider.engine

    async def transcribe(self, file: UploadFile) -> dict[str, Any]:
        """
        Orchestrates validation and transcription of an uploaded audio file.
        """
        _log.info(f"[VOICE] STT Service processing upload: {file.filename}")
        start_time = time.time()

        if not file.filename:
            raise HTTPException(status_code=400, detail="Empty filename")

        normalized_mime = (
            file.content_type.split(";")[0].strip().lower() if file.content_type else ""
        )

        if normalized_mime and normalized_mime not in ALLOWED_MIME_TYPES:
            raise HTTPException(
                status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
                detail=f"Unsupported MIME type: {normalized_mime}",
            )

        content = await file.read()
        if not content:
            raise HTTPException(status_code=400, detail="Empty file upload")

        if len(content) > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail="File is too large",
            )

        try:
            result = await self.stt_manager.transcribe(
                audio_bytes=content,
                filename=file.filename,
                mime_type=file.content_type or "audio/webm",
            )
        except HTTPException:
            raise
        except Exception as e:
            import traceback

            _log.error(f"[VOICE] FAILURE: STT transcription failed: {e}", exc_info=True)
            tb_str = traceback.format_exc()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail={
                    "message": "Failed to transcribe audio file due to an internal error.",
                    "exception_type": type(e).__name__,
                    "failing_module": __name__,
                    "failing_function": "transcribe",
                    "stack_trace": tb_str,
                    "execution_stage": "STT Inference",
                },
            )

        processing_time = time.time() - start_time
        _log.info(
            f"[VOICE] STT Service completed transcription in {processing_time:.2f}s via provider [{result.get('provider')}]"
        )

        return {
            "transcript": result.get("transcript", ""),
            "detected_language": result.get("detected_language", "en"),
            "confidence": result.get("confidence", 0.99),
            "duration": result.get("duration", 0.0),
            "processing_time": processing_time,
            "segments": result.get("segments", []),
            "metadata": result.get("metadata", {}),
            "provider": result.get("provider", "unknown"),
        }

    async def transcribe_array(self, samples: Any) -> dict[str, Any]:
        """
        Transcribe a 1D float32 numpy array directly from memory.
        """
        _log.info("[VOICE] STT Service processing audio array in memory")
        start_time = time.time()

        result = await self.stt_manager.transcribe_array(samples)

        processing_time = time.time() - start_time
        _log.info(
            f"[VOICE] STT Service completed array transcription in {processing_time:.2f}s"
        )

        return {
            "transcript": result["transcript"],
            "detected_language": result["detected_language"],
            "confidence": result["confidence"],
            "duration": result["duration"],
            "processing_time": processing_time,
            "segments": result["segments"],
            "metadata": result["metadata"],
        }
