from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from app.intent.enums import (
    IntentType,
    RiskLevel,
    ProviderType,
    ToolType,
    ContextSource,
)


class Entity(BaseModel):
    value: str
    category: str  # e.g., "language", "framework", "file", "technology"
    confidence: float


class ContextRequirement(BaseModel):
    source: ContextSource
    reason: str
    confidence: float


class RiskAssessment(BaseModel):
    level: RiskLevel
    reasons: List[str]
    requires_confirmation: bool


class ExecutionPlan(BaseModel):
    steps: List[str]
    suggested_tools: List[ToolType]
    suggested_provider: ProviderType
    estimated_tokens: Optional[int] = None


class IntentResult(BaseModel):
    request_id: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)

    # Intent and Extraction
    intent: IntentType
    confidence: float
    goal: str
    entities: List[Entity]

    # Analysis & Routing
    required_context: List[ContextRequirement]
    suggested_tools: List[ToolType]
    suggested_provider: ProviderType
    risk_assessment: RiskAssessment

    # Controls
    clarification_required: bool
    clarification_prompt: Optional[str] = None

    execution_plan: ExecutionPlan
    metadata: Dict[str, Any] = Field(default_factory=dict)
