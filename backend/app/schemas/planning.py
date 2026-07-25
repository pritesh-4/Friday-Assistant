from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field

from app.schemas.common import ApiModel

class GoalCategory(str, Enum):
    LEARNING = "learning"
    CODING = "coding"
    CAREER = "career"
    PERSONAL = "personal"
    RESEARCH = "research"
    CREATIVE = "creative"
    GENERAL = "general"

class Status(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    BLOCKED = "blocked"
    COMPLETED = "completed"
    FAILED = "failed"
    PAUSED = "paused"
    ABANDONED = "abandoned"

class Priority(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class PlanningTaskBase(BaseModel):
    title: str = Field(min_length=1)
    description: str | None = None
    priority: Priority = Priority.MEDIUM
    estimated_duration: str | None = None
    requires_approval: bool = True
    assigned_agent: str | None = None
    expected_output: str | None = None
    depends_on: list[str] = Field(default_factory=list) # List of task_ids

class PlanningTask(PlanningTaskBase, ApiModel):
    id: str
    milestone_id: str
    status: Status
    created_at: datetime
    updated_at: datetime

class MilestoneBase(BaseModel):
    title: str = Field(min_length=1)
    order_index: int = 0
    tasks: list[PlanningTaskBase] = Field(default_factory=list)

class Milestone(ApiModel):
    id: str
    goal_id: str
    title: str
    status: Status
    order_index: int
    created_at: datetime
    updated_at: datetime
    tasks: list[PlanningTask] = Field(default_factory=list)

class GoalBase(BaseModel):
    title: str = Field(min_length=1)
    description: str | None = None
    category: GoalCategory = GoalCategory.GENERAL
    milestones: list[MilestoneBase] = Field(default_factory=list)

class Goal(ApiModel):
    id: str
    title: str
    description: str | None
    category: GoalCategory
    status: Status
    progress_percent: int
    created_at: datetime
    updated_at: datetime
    milestones: list[Milestone] = Field(default_factory=list)
