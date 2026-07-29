from typing import Any

from pydantic import BaseModel


class WhisperSegment(BaseModel):
    id: int
    start: float
    end: float
    text: str


class TranscriptionResult(BaseModel):
    transcript: str
    detected_language: str
    confidence: float | None
    duration: float
    processing_time: float
    segments: list[WhisperSegment]
    metadata: dict[str, Any] | None = None
