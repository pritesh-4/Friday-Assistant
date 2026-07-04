from pydantic import BaseModel
from typing import Optional, List

class ChatRequest(BaseModel):
    """
    Schema for incoming chat prompts.
    """
    message: str

class ChatResponse(BaseModel):
    """
    Schema for chat responses returned to the client.
    """
    response: str

class MessageBase(BaseModel):
    role: str
    content: str

class MessageCreate(MessageBase):
    pass

class Message(MessageBase):
    id: str
    conversation_id: str
    created_at: str
    status: Optional[str] = "completed"
    citations: Optional[List[str]] = None
    context_awareness: Optional[str] = None
    emotional_header: Optional[str] = None

class Conversation(BaseModel):
    id: str
    title: str
    last_message: Optional[str] = None
    updated_at: str
    pinned: Optional[bool] = False
    favorite: Optional[bool] = False
