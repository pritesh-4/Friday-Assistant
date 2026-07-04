from pydantic import BaseModel

class UserSettings(BaseModel):
    """
    User preference settings.
    """
    theme: str = "dark"
    animations: bool = True
    voice_enabled: bool = True
    memory_enabled: bool = True
    notifications_enabled: bool = True

class Note(BaseModel):
    """
    Note model representation.
    """
    id: str
    title: str
    content: str
    created_at: str

class Task(BaseModel):
    """
    Todo task model representation.
    """
    id: str
    text: str
    completed: bool = False
