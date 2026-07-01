from pydantic import BaseModel
from typing import Optional

class MessageBase(BaseModel):
    role: str
    content: str

class MessageCreate(MessageBase):
    pass

class Message(MessageBase):
    id: str
    conversation_id: str
    created_at: str

class Conversation(BaseModel):
    id: str
    title: str
    last_message: Optional[str] = None
    updated_at: str

class UserSettings(BaseModel):
    theme: str = "dark"
    animations: bool = True
    voice_enabled: bool = True
    memory_enabled: bool = True
    notifications_enabled: bool = True

class Note(BaseModel):
    id: str
    title: str
    content: str
    created_at: str

class Task(BaseModel):
    id: str
    text: str
    completed: bool = False
