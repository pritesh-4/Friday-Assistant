import logging
import os
import subprocess
import uuid
from fastapi import HTTPException, UploadFile, status

from app.core.config import settings

_log = logging.getLogger("voice_service")

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
            _log.warning(f"[VOICE] FAILURE: Upload too large ({file_size} bytes)")
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail="File is too large",
            )
            
        upload_id = str(uuid.uuid4())
        ext = os.path.splitext(file.filename)[1].lower()
        if not ext:
            ext = ".webm"  # fallback
            
        raw_filename = f"{upload_id}_raw{ext}"
        raw_file_path = self.upload_dir / raw_filename

        with open(raw_file_path, "wb") as f:
            f.write(content)
            
        # Validate with ffprobe
        probe_output = ""
        try:
            probe_cmd = [
                "ffprobe",
                "-v", "error",
                "-show_entries", "format=duration",
                "-of", "default=noprint_wrappers=1:nokey=1",
                str(raw_file_path)
            ]
            probe_result = subprocess.run(
                probe_cmd,
                capture_output=True,
                text=True,
                check=True
            )
            probe_output = probe_result.stdout.strip()
            duration_str = probe_output
            duration = float(duration_str) if duration_str and duration_str != "N/A" else 0.0
            _log.info(f"[VOICE] Audio file validated via ffprobe. Duration: {duration:.2f}s")
        except subprocess.CalledProcessError as e:
            _log.error(f"[VOICE] FAILURE: Invalid or corrupted audio file (ffprobe failed):\nstderr: {e.stderr}")
            raw_file_path.unlink(missing_ok=True)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid or corrupted audio file. Format not recognised. FFprobe: {e.stderr}",
            )
        except Exception as e:
            _log.error(f"[VOICE] FAILURE: ffprobe execution failed: {e}")
            raw_file_path.unlink(missing_ok=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Audio validation failed: {e!s}",
            )

        # Convert to pristine 16kHz WAV
        wav_filename = f"{upload_id}.wav"
        wav_file_path = self.upload_dir / wav_filename
        
        ffmpeg_output = ""
        try:
            ffmpeg_cmd = [
                "ffmpeg",
                "-y",
                "-i", str(raw_file_path),
                "-ar", "16000",
                "-ac", "1",
                "-c:a", "pcm_s16le",
                str(wav_file_path)
            ]
            ffmpeg_result = subprocess.run(
                ffmpeg_cmd,
                capture_output=True,
                text=True,
                check=True
            )
            ffmpeg_output = ffmpeg_result.stderr # ffmpeg logs to stderr
            _log.info(f"[VOICE] Audio file successfully converted to 16kHz WAV: {wav_filename}")
        except subprocess.CalledProcessError as e:
            _log.error(f"[VOICE] FAILURE: ffmpeg conversion failed:\nstderr: {e.stderr}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Audio conversion to WAV failed. FFmpeg: {e.stderr}",
            )
        finally:
            raw_file_path.unlink(missing_ok=True)

        return {
            "upload_id": upload_id,
            "filename": wav_filename,
            "mime_type": "audio/wav",
            "size": wav_file_path.stat().st_size if wav_file_path.exists() else 0,
            "duration": duration,
            "status": "completed",
            "ffprobe_output": probe_output,
            "ffmpeg_output": ffmpeg_output
        }

