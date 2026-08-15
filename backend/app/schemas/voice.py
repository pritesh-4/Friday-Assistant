from enum import Enum
from typing import Any

from pydantic import BaseModel


class VoiceState(str, Enum):
    IDLE = "IDLE"
    LISTENING = "LISTENING"
    CAPTURING = "CAPTURING"
    TRANSCRIBING = "TRANSCRIBING"
    THINKING = "THINKING"
    SPEAKING = "SPEAKING"
    INTERRUPTED = "INTERRUPTED"
    ERROR = "ERROR"
    RECONNECTING = "RECONNECTING"


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
    provider: str | None = None


class VoiceTurnMetrics(BaseModel):
    turn_id: str
    conversation_id: str | None = None
    stt_latency_ms: int = 0
    intent_latency_ms: int = 0
    memory_latency_ms: int = 0
    planner_latency_ms: int = 0
    llm_ttft_ms: int = 0
    llm_total_ms: int = 0
    tts_ttfa_ms: int = 0
    tts_total_ms: int = 0
    total_turn_ms: int = 0
    stt_provider: str = "openrouter_whisper"
    tts_provider: str = "openrouter"
    estimated_cost_usd: float = 0.0
