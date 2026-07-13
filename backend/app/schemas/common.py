from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


def to_camel(value: str) -> str:
    """Use camelCase at the browser boundary while keeping Python idiomatic."""
    head, *tail = value.split("_")
    return head + "".join(part.capitalize() for part in tail)


class ApiModel(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)


class UserSettings(ApiModel):
    theme: Literal["dark", "light", "system"] = "dark"
    animations: bool = True
    voice_enabled: bool = True
    sidebar_collapsed: bool = False
    memory_enabled: bool = True
    notifications_enabled: bool = True


class NoteCreate(ApiModel):
    title: str = Field(min_length=1, max_length=160)
    content: str = Field(min_length=1, max_length=20_000)


class Note(NoteCreate):
    id: str
    created_at: datetime
    updated_at: datetime


class TaskCreate(ApiModel):
    title: str = Field(min_length=1, max_length=200)
    status: Literal["pending", "completed"] = "pending"
    priority: Literal["low", "medium", "high"] = "medium"
    due_date: str | None = Field(default=None, max_length=32)


class TaskUpdate(ApiModel):
    title: str | None = Field(default=None, min_length=1, max_length=200)
    status: Literal["pending", "completed"] | None = None
    priority: Literal["low", "medium", "high"] | None = None
    due_date: str | None = Field(default=None, max_length=32)


class Task(TaskCreate):
    id: str


class StoredFile(ApiModel):
    id: str
    name: str
    content_type: str
    size_bytes: int
    created_at: datetime
