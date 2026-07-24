import os
import uuid
from fastapi import UploadFile, HTTPException, status
from app.core.config import settings

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


class VoiceService:
    """
    Service responsible for validating and storing uploaded voice audio files.

    STT (transcription) is handled by TranscriptionService.
    TTS (synthesis) is handled by SpeechService.
    This service solely owns the upload lifecycle.
    """

    def __init__(self):
        self.upload_dir = settings.voice_uploads_directory
        self.upload_dir.mkdir(parents=True, exist_ok=True)

    async def upload_audio(self, file: UploadFile) -> dict:
        """
        Validates and stores an uploaded audio file.
        Returns upload metadata including the filename and MIME type.
        """
        if not file.filename:
            raise HTTPException(status_code=400, detail="Empty filename")

        # 1. MIME Normalization
        # Browsers often send codecs like 'audio/webm;codecs=opus'
        normalized_mime = file.content_type.split(";")[0].strip().lower() if file.content_type else ""

        if normalized_mime not in ALLOWED_MIME_TYPES:
            raise HTTPException(
                status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
                detail=f"Received MIME:\n{file.content_type}\n\nNormalized MIME:\n{normalized_mime}\n\nAllowed:\n{', '.join(sorted(ALLOWED_MIME_TYPES))}",
            )

        # 2. Dual-Layer Validation (Extension Check)
        ext = os.path.splitext(file.filename)[1].lower()
        if not ext:
            ext = ".webm"  # fallback if no extension provided

        if ext not in ALLOWED_EXTENSIONS:
            raise HTTPException(
                status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
                detail=f"Unsupported file extension: {ext}. Allowed: {', '.join(sorted(ALLOWED_EXTENSIONS))}",
            )

        # Check for empty file before saving
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
        ext = os.path.splitext(file.filename)[1].lower()
        if not ext:
            ext = ".webm"  # fallback
        safe_filename = f"{upload_id}{ext}"
        file_path = self.upload_dir / safe_filename

        with open(file_path, "wb") as f:
            f.write(content)

        return {
            "upload_id": upload_id,
            "filename": safe_filename,
            "mime_type": file.content_type,
            "size": file_size,
            "duration": None,
            "status": "completed",
        }

