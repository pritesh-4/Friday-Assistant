"""Pydantic schemas for the Autonomous Memory & Identity System (AMIS)."""

from datetime import datetime
from enum import Enum
from typing import Any
from pydantic import Field
from app.schemas.common import ApiModel
from app.schemas.memory import MemoryType, MemoryMetadata, CognitiveMemoryPayload, ExtractedMemory


class EntityType(str, Enum):
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


class Entity(ApiModel):
    id: str
    type: EntityType
    name: str
    confidence: float = 1.0
    created_at: datetime
    updated_at: datetime


class EntityAlias(ApiModel):
    id: str
    entity_id: str
    alias: str
    created_at: datetime


class EntityAttribute(ApiModel):
    id: str
    entity_id: str
    key: str
    value: str
    confidence: float = 1.0
    created_at: datetime
    updated_at: datetime


class Relationship(ApiModel):
    id: str
    source_id: str
    target_id: str
    relation_type: str
    weight: float = 1.0
    created_at: datetime
    updated_at: datetime


class ExtractedEntity(ApiModel):
    name: str
    type: EntityType
    aliases: list[str] = Field(default_factory=list)
    attributes: dict[str, str] = Field(default_factory=dict)
    confidence: float = 1.0


class ExtractedRelationship(ApiModel):
    source_entity_name: str
    target_entity_name: str
    relation_type: str
    weight: float = 1.0


class ExtractedMemoryV2(ApiModel):
    memory_type: MemoryType
    content: str
    importance_score: int = Field(default=5, ge=1, le=10)
    confidence: float = 1.0
    event_title: str | None = None
    timeline_date: str | None = None
    workflow_name: str | None = None
    project_name: str | None = None
    reason: str | None = None


class ExplicitCommand(ApiModel):
    action: str  # 'forget', 'update', 'correct'
    target_type: str  # 'entity', 'attribute', 'relationship', 'memory'
    query: str  # Search query to locate the item
    update_value: str | None = None  # New value if update/correct
    details: str | None = None


class AMISExtraction(ApiModel):
    should_remember: bool
    entities: list[ExtractedEntity] = Field(default_factory=list)
    relationships: list[ExtractedRelationship] = Field(default_factory=list)
    memories: list[ExtractedMemoryV2] = Field(default_factory=list)
    commands: list[ExplicitCommand] = Field(default_factory=list)
