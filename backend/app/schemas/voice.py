from pydantic import BaseModel
from typing import List, Optional, Any, Dict

class WhisperSegment(BaseModel):
    id: int
    start: float
    end: float
    text: str

class TranscriptionResult(BaseModel):
    transcript: str
    detected_language: str
    confidence: Optional[float]
    duration: float
    processing_time: float
    segments: List[WhisperSegment]
    metadata: Optional[Dict[str, Any]] = None
