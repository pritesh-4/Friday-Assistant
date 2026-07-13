from datetime import datetime

from pydantic import Field

from app.schemas.common import ApiModel



class MemoryBase(ApiModel):
    """A user-approved long-term memory record."""

    title: str = Field(min_length=1, max_length=160)
    value: str = Field(min_length=1, max_length=4_000)
    category: str = Field(default="general", min_length=1, max_length=64)

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
    created_at: datetime
