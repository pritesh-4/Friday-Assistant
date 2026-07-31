"""Pydantic schemas for Identity Engine V1."""

from datetime import datetime
from enum import Enum
from typing import Any
from pydantic import Field
from app.schemas.common import ApiModel


class IdentityType(str, Enum):
    USER = "user"
    PERSON = "person"
    FRIEND = "friend"
    FAMILY = "family"
    COLLEAGUE = "colleague"
    ORGANIZATION = "organization"
    COMPANY = "company"
    PROJECT = "project"
    REPOSITORY = "repository"
    TECHNOLOGY = "technology"
    FRAMEWORK = "framework"
    API = "api"
    AI_MODEL = "ai_model"
    APPLICATION = "application"
    BOOK = "book"
    MOVIE = "movie"
    PLACE = "place"
    DEVICE = "device"
    EVENT = "event"
    TASK = "task"
    GOAL = "goal"
    FILE = "file"
    DOCUMENT = "document"
    PROGRAMMING_LANGUAGE = "programming_language"
    WEBSITE = "website"
    LOCATION = "location"
    MEMORY = "memory"
    SKILL = "skill"
    HABIT = "habit"


class IdentityEntity(ApiModel):
    """Represents a canonical entity profile inside the Identity Engine."""

    id: str
    type: IdentityType
    display_name: str
    canonical_name: str
    aliases: list[str] = Field(default_factory=list)
    description: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
    confidence: float = 1.0
    created_at: datetime
    updated_at: datetime
    status: str = "active"
    version: int = 1
    embedding: list[float] | None = None
    source_history: list[str] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)
    visit_count: int = 0
    last_accessed: datetime | None = None
    relationship_references: list["IdentityRelationship"] = Field(default_factory=list)

    @property
    def name(self) -> str:
        return self.canonical_name

    @name.setter
    def name(self, value: str) -> None:
        self.canonical_name = value


class IdentityRelationship(ApiModel):
    """Directed connection edge between two entities with trust scores."""

    source_id: str
    target_id: str
    relation_type: str
    weight: float = 1.0
    confidence: float = 1.0
    timestamp: datetime
    evidence: str | None = None
    direction: str = "directed"


class ExtractedIdentity(ApiModel):
    """Structure returned by the Recognition system."""

    name: str
    type: IdentityType
    aliases: list[str] = Field(default_factory=list)
    attributes: dict[str, Any] = Field(default_factory=dict)
    confidence: float = 1.0
    description: str | None = None


class ExtractedRelationship(ApiModel):
    """Structure for extracted links between identities."""

    source_name: str
    target_name: str
    relation_type: str
    confidence: float = 1.0
    evidence: str | None = None


class IdentityExtraction(ApiModel):
    """Complete structured output from Recognition."""

    should_register: bool
    entities: list[ExtractedIdentity] = Field(default_factory=list)
    relationships: list[ExtractedRelationship] = Field(default_factory=list)
