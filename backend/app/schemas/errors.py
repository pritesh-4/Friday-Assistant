from typing import Any
from pydantic import BaseModel, Field

class ErrorDetail(BaseModel):
    code: str = Field(..., description="A unique machine-readable error code.")
    message: str = Field(..., description="A human-readable error message.")
    details: dict[str, Any] | list[Any] | None = Field(default=None, description="Additional structured context about the error.")
    request_id: str | None = Field(default=None, description="The correlation ID for this request.")

class ErrorResponse(BaseModel):
    error: ErrorDetail
