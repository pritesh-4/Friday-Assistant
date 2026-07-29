from datetime import datetime
from typing import Literal

from pydantic import Field

from app.schemas.common import ApiModel


class ChatRequest(ApiModel):
    """A text message sent to an existing or new conversation."""

    message: str = Field(min_length=1, max_length=8_000)
    conversation_id: str | None = Field(default=None, min_length=1, max_length=64)
    file_ids: list[str] | None = None
    approved_permissions: list[str] | None = None


class Message(ApiModel):
    id: str
    conversation_id: str
    role: Literal["user", "assistant", "system"]
    content: str
    created_at: datetime
    status: str = "completed"
    citations: list[str] | None = None
    context_awareness: str | None = None
    emotional_header: str | None = None


class Conversation(ApiModel):
    id: str
    title: str
    last_message: str | None = None
    created_at: datetime
    updated_at: datetime
    pinned: bool = False
    favorite: bool = False


class ChatResponse(ApiModel):
    conversation: Conversation
    user_message: Message
    assistant_message: Message
    provider: str
    model: str
    latency_ms: int
    finish_reason: str | None = None
    memories_used: int = 0
