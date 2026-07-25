from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field

from app.schemas.common import ApiModel

class JobStatus(str, Enum):
    QUEUED = "queued"
    SCHEDULED = "scheduled"
    RUNNING = "running"
    WAITING = "waiting" # E.g., waiting for user permission
    RETRY = "retry"
    COMPLETED = "completed"
    FAILED = "failed"
    ARCHIVED = "archived"

class NotificationType(str, Enum):
    INFO = "info"
    SUCCESS = "success"
    WARNING = "warning"
    ERROR = "error"
    APPROVAL = "approval"

class NotificationStatus(str, Enum):
    UNREAD = "unread"
    READ = "read"
    ARCHIVED = "archived"

class JobCreate(BaseModel):
    task_type: str = Field(..., description="e.g., 'research', 'periodic_scan', 'kb_index'")
    payload: dict = Field(default_factory=dict, description="JSON payload for the task")
    scheduled_at: datetime | None = None
    max_retries: int = 3
    agent_name: str | None = None

class Job(ApiModel):
    id: str
    task_type: str
    payload: dict
    status: JobStatus
    scheduled_at: datetime
    started_at: datetime | None
    completed_at: datetime | None
    retries: int
    max_retries: int
    error_message: str | None
    agent_name: str | None
    created_at: datetime
    updated_at: datetime

class NotificationCreate(BaseModel):
    title: str
    message: str
    type: NotificationType = NotificationType.INFO
    action_url: str | None = None

class Notification(ApiModel):
    id: str
    title: str
    message: str
    type: NotificationType
    action_url: str | None
    status: NotificationStatus
    created_at: datetime
