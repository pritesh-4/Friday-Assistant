"""Compatibility wrapper pointing to the refactored CognitiveMemoryService."""

from app.memory.memory_service import CognitiveMemoryService
from app.schemas.memory import (
    CognitiveMemoryPayload,
    ExtractedMemory,
    MemoryMetadata,
    MemoryType,
)

__all__ = [
    "CognitiveMemoryService",
    "CognitiveMemoryPayload",
    "ExtractedMemory",
    "MemoryMetadata",
    "MemoryType",
]
