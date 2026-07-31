"""Schemas for the FRIDAY Executive Planner V1."""

from typing import Optional
from pydantic import BaseModel, Field

from app.schemas.planning import Priority, Status
from app.intent.enums import RiskLevel


class SubTask(BaseModel):
    id: str = Field(description="Unique identifier for the subtask")
    title: str = Field(description="Title of the subtask")
    description: Optional[str] = Field(
        default=None, description="Detailed description of the task"
    )
    priority: Priority = Field(
        default=Priority.MEDIUM,
        description="Task priority (low, medium, high, critical)",
    )
    estimated_complexity: str = Field(
        default="medium", description="Complexity score (low, medium, high)"
    )
    dependencies: list[str] = Field(
        default_factory=list, description="IDs of tasks this task depends on"
    )
    status: Status = Field(
        default=Status.PENDING,
        description="Completion status (pending, in_progress, completed, failed)",
    )


class RiskAssessment(BaseModel):
    level: RiskLevel = Field(
        default=RiskLevel.SAFE, description="Calculated risk level"
    )
    confidence: float = Field(
        default=1.0, description="Confidence in this assessment (0.0 to 1.0)"
    )
    unknown_variables: list[str] = Field(
        default_factory=list, description="Variables that are unknown or volatile"
    )
    failure_probability: float = Field(
        default=0.0, description="Calculated failure probability (0.0 to 1.0)"
    )
    requires_confirmation: bool = Field(
        default=False, description="Whether explicit user confirmation is needed"
    )
    is_destructive: bool = Field(
        default=False,
        description="Whether the action modifies/deletes critical resources",
    )
    requires_authentication: bool = Field(
        default=False, description="Whether external authentication is required"
    )


class ContextSelection(BaseModel):
    memories: list[str] = Field(
        default_factory=list,
        description="Relevant memory strings retrieved from long-term memory",
    )
    graph_nodes: list[str] = Field(
        default_factory=list, description="Relevant Knowledge Graph entities"
    )
    projects: list[str] = Field(
        default_factory=list, description="Associated active project names"
    )
    conversations: list[str] = Field(
        default_factory=list, description="Context from past conversation snippets"
    )
    files: list[str] = Field(
        default_factory=list, description="Absolute paths to relevant workspace files"
    )


class ToolRecommendation(BaseModel):
    tool_name: str = Field(description="Name of the recommended tool")
    reason: str = Field(description="Explanation of why this tool is needed")
    permission_level: str = Field(
        default="safe", description="Permission level (safe, read_only, destructive)"
    )


class MissionPlan(BaseModel):
    primary_goal: str = Field(description="The primary objective of the mission")
    secondary_goals: list[str] = Field(
        default_factory=list, description="Supporting or secondary objectives"
    )
    subtasks: list[SubTask] = Field(
        default_factory=list, description="List of decomposed subtasks/milestones"
    )
    context: ContextSelection = Field(
        default_factory=ContextSelection, description="Retrieved context items"
    )
    tools: list[ToolRecommendation] = Field(
        default_factory=list, description="List of recommended tools"
    )
    provider_route: str = Field(
        default="Gemini", description="Provider route (e.g. Gemini, Claude, GPT)"
    )
    risks: RiskAssessment = Field(
        default_factory=RiskAssessment, description="Calculated execution risks"
    )
    expected_result: str = Field(description="What the successful outcome looks like")
    fallback_strategy: str = Field(
        description="How to proceed if the primary path fails"
    )
