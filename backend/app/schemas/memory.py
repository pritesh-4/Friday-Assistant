"""Pydantic schemas for the Cognitive Memory system."""

from datetime import datetime
from enum import Enum
from pydantic import Field

from app.schemas.common import ApiModel


class MemoryType(str, Enum):
    WORKING = "working"
    SEMANTIC = "semantic"
    EPISODIC = "episodic"
    PROCEDURAL = "procedural"
    PROJECT = "project"


class MemoryMetadata(ApiModel):
    """Metadata used for observability and retrieval logic."""
    id: str
    memory_type: MemoryType
    memory_id: str
    importance_score: int = Field(default=5, ge=1, le=10)
    reason: str
    retrieval_count: int = 0
    created_at: datetime


class WorkingMemory(ApiModel):
    id: str
    conversation_id: str
    content: str
    expires_at: datetime | None = None
    created_at: datetime


class SemanticMemory(ApiModel):
    id: str
    fact: str
    confidence: float = 1.0
    created_at: datetime
    updated_at: datetime


class EpisodicMemory(ApiModel):
    id: str
    event_title: str
    timeline_date: str | None = None
    details: str
    created_at: datetime
    updated_at: datetime


class ProceduralMemory(ApiModel):
    id: str
    workflow_name: str
    steps: str
    created_at: datetime
    updated_at: datetime


class ProjectMemory(ApiModel):
    id: str
    project_id: str
    content: str
    created_at: datetime
    updated_at: datetime


class Project(ApiModel):
    id: str
    name: str
    architecture: str | None = None
    progress: str | None = None
    created_at: datetime
    updated_at: datetime


class CognitiveMemoryPayload(ApiModel):
    """Used for returning memory data to the client."""
    id: str
    memory_type: MemoryType
    content: str
    metadata: MemoryMetadata
    created_at: datetime
    updated_at: datetime | None = None


class ExtractedMemory(ApiModel):
    """Output from the MemoryExtractor LLM Agent."""
    should_remember: bool
    memory_type: MemoryType | None = None
    importance_score: int | None = None
    reason: str | None = None
    content: str | None = None
    event_title: str | None = None  # for episodic
    timeline_date: str | None = None  # for episodic
    workflow_name: str | None = None  # for procedural
    project_name: str | None = None  # for project
    confidence: float | None = None  # for semantic
