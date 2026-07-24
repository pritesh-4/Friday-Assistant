import time
import os
from typing import Dict, Any
from fastapi import HTTPException, status
from app.core.logging import get_logger
from app.ai.whisper.engine import WhisperEngine

_log = get_logger("transcription_service")

class TranscriptionService:
    """
    Service for handling transcription of audio files using WhisperEngine.
    """
    def __init__(self):
        self.engine = WhisperEngine()

    async def transcribe(self, audio_path: str) -> Dict[str, Any]:
        """
        Transcribe an audio file and return structured results including metrics.
        
        Args:
            audio_path: The absolute or relative path to the audio file on disk.
        
        Returns:
            Dictionary matching the TranscriptionResult schema.
        """
        if not os.path.exists(audio_path):
            _log.error(f"Audio file not found: {audio_path}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Audio file not found for transcription."
            )
            
        _log.info(f"[VOICE] STT Engine Started processing audio: {audio_path}")
        start_time = time.time()
        
        try:
            result = await self.engine.transcribe(audio_path)
        except Exception as e:
            _log.error(f"Transcription failed: {e}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to transcribe audio file due to an internal error."
            )
            
        processing_time = time.time() - start_time
        _log.info(f"[VOICE] STT Engine Completed transcription in {processing_time:.2f}s")
        
        # Check if any speech was detected (segments empty)
        if not result["segments"] or not result["transcript"].strip():
            _log.warning(f"No speech detected in audio file: {audio_path}")
            # Note: We still return success but with empty transcript
            # depending on requirements, it could also raise an error.
            # We return empty for now, the client can handle it.
        
        return {
            "transcript": result["transcript"],
            "detected_language": result["detected_language"],
            "confidence": result["confidence"],
            "duration": result["duration"],
            "processing_time": processing_time,
            "segments": result["segments"],
            "metadata": result["metadata"]
        }
