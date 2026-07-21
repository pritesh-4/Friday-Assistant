"""Pydantic schemas for the memory system."""

from datetime import datetime

from pydantic import Field

from app.schemas.common import ApiModel


class MemoryBase(ApiModel):
    """Core fields shared by all memory representations."""

    title: str = Field(min_length=1, max_length=160, description="Short label for the memory.")
    value: str = Field(min_length=1, max_length=4_000, description="Full memory content.")
    category: str = Field(
        default="general",
        min_length=1,
        max_length=64,
        description="Organisational category (e.g. 'preferences', 'facts', 'goals').",
    )


class MemoryCreate(MemoryBase):
    """Fields required to create a new memory entry."""

    source: str = Field(
        default="user",
        max_length=32,
        description="Origin of the memory: 'user' (manually added) or 'agent' (extracted).",
    )


class MemoryUpdate(ApiModel):
    """Fields that may be updated on an existing memory."""

    title: str | None = Field(default=None, min_length=1, max_length=160)
    value: str | None = Field(default=None, min_length=1, max_length=4_000)
    category: str | None = Field(default=None, min_length=1, max_length=64)


class Memory(MemoryBase):
    """Full representation of a persisted memory entry."""

    id: str
    source: str = "user"
    pinned: bool = False
    created_at: datetime
    updated_at: datetime | None = None
