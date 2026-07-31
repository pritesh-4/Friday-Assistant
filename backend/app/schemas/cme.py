"""Pydantic schemas for the Cognitive Memory Engine (CME) V2."""

from datetime import datetime
from enum import Enum
from typing import Any
from pydantic import Field
from app.schemas.common import ApiModel
from app.schemas.memory import MemoryType


class CMEEntityType(str, Enum):
    PERSON = "person"
    PROJECT = "project"
    ORGANIZATION = "organization"
    AI_MODEL = "ai_model"
    APPLICATION = "application"
    PRODUCT = "product"
    REPOSITORY = "repository"
    CONCEPT = "concept"
    LOCATION = "location"
    TOOL = "tool"
    FRAMEWORK = "framework"
    OTHER = "other"


class CMEEntity(ApiModel):
    id: str
    type: CMEEntityType
    name: str
    confidence: float = 1.0
    created_at: datetime
    updated_at: datetime


class CMEEntityAlias(ApiModel):
    id: str
    entity_id: str
    alias: str
    created_at: datetime


class CMEEntityAttribute(ApiModel):
    id: str
    entity_id: str
    key: str
    value: str
    confidence: float = 1.0
    created_at: datetime
    updated_at: datetime


class CMERelationship(ApiModel):
    id: str
    source_id: str
    target_id: str
    relation_type: str
    weight: float = 1.0
    created_at: datetime
    updated_at: datetime


class CMEExtractedEntity(ApiModel):
    name: str
    type: CMEEntityType
    aliases: list[str] = Field(default_factory=list)
    attributes: dict[str, str] = Field(default_factory=dict)
    confidence: float = 1.0


class CMEExtractedRelationship(ApiModel):
    source_entity_name: str
    target_entity_name: str
    relation_type: str
    weight: float = 1.0


class CMEExtractedMemory(ApiModel):
    memory_type: MemoryType
    content: str
    importance_score: int = Field(default=5, ge=1, le=10)
    confidence: float = 1.0
    event_title: str | None = None
    timeline_date: str | None = None
    workflow_name: str | None = None
    project_name: str | None = None
    reason: str | None = None


class CMEExplicitCommand(ApiModel):
    action: str  # 'forget', 'update', 'correct'
    target_type: str  # 'entity', 'attribute', 'relationship', 'memory'
    query: str
    update_value: str | None = None
    details: str | None = None


class CMEExtraction(ApiModel):
    """Extraction output from CME V2 answering the four core questions."""

    should_remember: bool
    
    # The Four Questions Answers
    what_happened: str | None = None
    who_involved: list[str] = Field(default_factory=list)
    what_changed: str | None = None
    what_remember: str | None = None

    # Extracted structures
    entities: list[CMEExtractedEntity] = Field(default_factory=list)
    relationships: list[CMEExtractedRelationship] = Field(default_factory=list)
    memories: list[CMEExtractedMemory] = Field(default_factory=list)
    commands: list[CMEExplicitCommand] = Field(default_factory=list)
