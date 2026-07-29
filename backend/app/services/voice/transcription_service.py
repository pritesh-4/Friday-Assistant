import asyncio
import os
import subprocess
import time
import uuid
from pathlib import Path
from typing import Any

from fastapi import HTTPException, UploadFile, status

from app.ai.whisper.engine import WhisperEngine
from app.core.config import settings
from app.core.logging import get_logger

_log = get_logger("transcription_service")

ALLOWED_MIME_TYPES = {
    "audio/webm",
    "audio/ogg",
    "audio/wav",
    "audio/x-wav",
    "audio/mp4",
    "audio/mpeg",
}

ALLOWED_EXTENSIONS = {
    ".webm",
    ".ogg",
    ".wav",
    ".mp4",
    ".m4a",
    ".mp3",
    ".mpeg",
}

MAX_FILE_SIZE = settings.max_upload_size_bytes

class TranscriptionService:
    """
    Service for handling the entire transcription lifecycle:
    receiving an UploadFile, validating, decoding via FFmpeg,
    running WhisperEngine, and cleaning up temporary files.
    """
    def __init__(self):
        self.engine = WhisperEngine()
        self.upload_dir = settings.voice_uploads_directory
        self.upload_dir.mkdir(parents=True, exist_ok=True)

    async def _process_upload(self, file: UploadFile) -> Path:
        """
        Validates the upload and converts it to a 16kHz WAV file.
        Returns the path to the converted WAV file.
        Raises HTTPException on validation or conversion failure.
        """
        if not file.filename:
            raise HTTPException(status_code=400, detail="Empty filename")

        normalized_mime = file.content_type.split(";")[0].strip().lower() if file.content_type else ""

        if normalized_mime not in ALLOWED_MIME_TYPES:
            raise HTTPException(
                status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
                detail=f"Unsupported MIME type: {normalized_mime}",
            )

        ext = os.path.splitext(file.filename)[1].lower() or ".webm"

        if ext not in ALLOWED_EXTENSIONS:
            raise HTTPException(
                status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
                detail=f"Unsupported file extension: {ext}",
            )

        content = await file.read()
        if not content:
            raise HTTPException(status_code=400, detail="Empty file upload")

        file_size = len(content)
        if file_size > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail="File is too large",
            )
            
        upload_id = str(uuid.uuid4())
        raw_filename = f"{upload_id}_raw{ext}"
        raw_file_path = self.upload_dir / raw_filename

        with open(raw_file_path, "wb") as f:
            f.write(content)

        wav_filename = f"{upload_id}.wav"
        wav_file_path = self.upload_dir / wav_filename
        
        try:
            ffmpeg_cmd = [
                "ffmpeg",
                "-y",
                "-i", str(raw_file_path),
                "-ar", "16000",
                "-ac", "1",
                "-filter:a", "dynaudnorm",
                "-c:a", "pcm_s16le",
                str(wav_file_path)
            ]
            await asyncio.to_thread(
                subprocess.run,
                ffmpeg_cmd,
                capture_output=True,
                text=True,
                check=True,
            )
        except subprocess.CalledProcessError as e:
            _log.error(f"[VOICE] FFmpeg conversion failed: {e.stderr}")
            if raw_file_path.exists():
                raw_file_path.unlink()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Audio conversion failed: {e.stderr}",
            )
        except Exception as e:
            _log.error(f"[VOICE] FFmpeg execution failed: {e}")
            if raw_file_path.exists():
                raw_file_path.unlink()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Audio decoding failed: {str(e)}",
            )
        finally:
            if raw_file_path.exists():
                raw_file_path.unlink(missing_ok=True)

        return wav_file_path


    async def transcribe(self, file: UploadFile) -> dict[str, Any]:
        """
        Orchestrates the validation, conversion, and transcription of an audio file.
        Ensures strict cleanup of temporary resources.
        
        Args:
            file: The UploadFile object received from the route.
        
        Returns:
            Dictionary matching the TranscriptionResult schema.
        """
        _log.info(f"[VOICE] STT Engine Started processing upload: {file.filename}")
        start_time = time.time()
        
        wav_path = await self._process_upload(file)
        
        try:
            result = await self.engine.transcribe(str(wav_path))
        except HTTPException:
            raise
        except Exception as e:
            import traceback
            _log.error(f"[VOICE] FAILURE: Transcription failed: {e}", exc_info=True)
            tb_str = traceback.format_exc()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail={
                    "message": "Failed to transcribe audio file due to an internal error.",
                    "exception_type": type(e).__name__,
                    "failing_module": __name__,
                    "failing_function": "transcribe",
                    "stack_trace": tb_str,
                    "execution_stage": "STT Inference"
                }
            )
        finally:
            if wav_path.exists():
                wav_path.unlink(missing_ok=True)
            
        processing_time = time.time() - start_time
        _log.info(f"[VOICE] STT Engine Completed transcription in {processing_time:.2f}s")
        
        if not result["segments"] or not result["transcript"].strip():
            _log.warning(f"[VOICE] No speech detected in audio file: {file.filename}")
            
        _log.info("[VOICE] Returning transcript")
        
        return {
            "transcript": result["transcript"],
            "detected_language": result["detected_language"],
            "confidence": result["confidence"],
            "duration": result["duration"],
            "processing_time": processing_time,
            "segments": result["segments"],
            "metadata": result["metadata"]
        }
