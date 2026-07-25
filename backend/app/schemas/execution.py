"""Execution and tool-related schemas."""

from enum import Enum
from pydantic import BaseModel, Field
from typing import Any, Optional

class PermissionLevel(str, Enum):
    SAFE = "safe"              # No approval needed (e.g., Web Search)
    READ_ONLY = "read_only"    # Configurable approval (e.g., Read File)
    DESTRUCTIVE = "destructive" # Explicit approval required (e.g., Write File, Delete File)

class RetryConfig(BaseModel):
    max_retries: int = Field(default=0, description="Maximum number of retry attempts")
    backoff_factor: float = Field(default=1.0, description="Exponential backoff factor")
    max_backoff: float = Field(default=10.0, description="Maximum backoff in seconds")

class ToolExecutionRequest(BaseModel):
    tool_name: str
    kwargs: dict[str, Any]

class ToolExecutionResponse(BaseModel):
    success: bool
    result: Any
    error: Optional[str] = None
    execution_time_ms: int
    retries: int = 0

class PermissionRequest(BaseModel):
    tool_name: str
    permission_scope: str
    kwargs: dict[str, Any]
    justification: str

class PermissionState(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    DENIED = "denied"
