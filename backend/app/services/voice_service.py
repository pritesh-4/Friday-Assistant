import os
import uuid
from fastapi import UploadFile, HTTPException, status
from app.core.config import settings

ALLOWED_MIME_TYPES = {"audio/webm", "audio/wav", "audio/ogg", "audio/mp4"}
MAX_FILE_SIZE = settings.max_upload_size_bytes

class VoiceService:
    """
    Service responsible for handling speech-to-text (STT) and text-to-speech (TTS) services,
    and voice file uploads.
    """
    
    def __init__(self):
        self.upload_dir = settings.voice_uploads_directory
        self.upload_dir.mkdir(parents=True, exist_ok=True)

    async def upload_audio(self, file: UploadFile) -> dict:
        """
        Validates and stores an uploaded audio file.
        """
        if not file.filename:
            raise HTTPException(status_code=400, detail="Empty filename")

        if file.content_type not in ALLOWED_MIME_TYPES:
            raise HTTPException(
                status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
                detail=f"Unsupported media type: {file.content_type}. Allowed: {', '.join(ALLOWED_MIME_TYPES)}",
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
        # Use simple extension matching
        ext = os.path.splitext(file.filename)[1].lower()
        if not ext:
            ext = ".webm" # fallback
        safe_filename = f"{upload_id}{ext}"
        file_path = self.upload_dir / safe_filename

        with open(file_path, "wb") as f:
            f.write(content)

        return {
            "upload_id": upload_id,
            "filename": safe_filename,
            "mime_type": file.content_type,
            "size": file_size,
            "duration": None, # Future Whisper implementation
            "status": "completed"
        }

    async def transcribe_audio(self, audio_data: bytes) -> str:
        """
        Transcribe audio binary content to text.
        """
        return ""

    async def synthesize_speech(self, text: str) -> bytes:
        """
        Synthesize speech audio content from text.
        """
        return b""
