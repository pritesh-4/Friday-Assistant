from pydantic import BaseModel
from typing import Optional

class MemoryBase(BaseModel):
    """
    Base attributes for a memory entry.
    """
    content: str
    category: Optional[str] = "general"

class MemoryCreate(MemoryBase):
    """
    Attributes required to create a memory.
    """
    pass

class Memory(MemoryBase):
    """
    Fully representation of a memory entry.
    """
    id: str
    created_at: str
