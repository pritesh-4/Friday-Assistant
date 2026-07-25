"""Planner Agent for intent analysis and task routing."""

import json
from typing import Any
from enum import Enum
from pydantic import BaseModel

from app.core.logging import get_logger
from app.services.llm_service import LLMService

logger = get_logger(__name__)

class ExecutionStrategy(str, Enum):
    CONVERSATIONAL = "conversational"  # Simple Q&A, no tools needed
    SINGLE_AGENT = "single_agent"      # Delegate to a specific specialized agent
    MULTI_STEP = "multi_step"          # Needs multiple steps
    GOAL_CREATION = "goal_creation"    # User wants to set a long-term goal or project

class PlannerResponse(BaseModel):
    strategy: ExecutionStrategy
    agent_name: str | None = None
    reasoning: str

class PlannerAgent:
    """Analyzes user intent and decides the execution strategy."""
    
    def __init__(self, llm_service: LLMService):
        self.llm_service = llm_service

    async def plan_execution(self, messages: list[dict[str, Any]], available_agents: list[str]) -> PlannerResponse:
        """Determines how to handle the user's request."""
        
        system_instruction = (
            "You are the Planner Agent for F.R.I.D.A.Y.\n"
            "Your job is to analyze the user's latest request and decide the best execution strategy.\n\n"
            f"Available Specialized Agents: {', '.join(available_agents)}\n\n"
            "Execution Strategies:\n"
            "- 'conversational': The user is just chatting, asking a general knowledge question, or making a statement. No tools or agents are needed.\n"
            "- 'single_agent': The user's request requires the specific capabilities of one of the available specialized agents (e.g., searching the web).\n"
            "- 'goal_creation': The user is stating a complex, long-term goal, project, or objective that should be broken down into a structured plan (milestones and tasks).\n\n"
            "You MUST reply with ONLY a JSON object in this format:\n"
            "{\n"
            '  "strategy": "conversational" | "single_agent" | "goal_creation",\n'
            '  "agent_name": "NameOfAgentOrNull",\n'
            '  "reasoning": "Brief explanation of why this strategy was chosen"\n'
            "}"
        )
        
        # We only want to analyze the intent of the conversation, not execute tools.
        # We construct a short context window for the planner.
        planner_messages = [
            {"role": "system", "content": system_instruction}
        ]
        # Append the last few messages to give context
        planner_messages.extend(messages[-3:])
        
        try:
            # We use the fallback chain via LLMService
            provider_name = next(iter(self.llm_service.available_providers))
            provider = self.llm_service.get_provider(provider_name)
            
            response = await provider.generate_response(planner_messages)
            content = response.content.strip()
            
            # Remove markdown code blocks if the LLM wrapped the JSON
            if content.startswith("```json"):
                content = content[7:]
            if content.endswith("```"):
                content = content[:-3]
            
            content = content.strip()
            
            plan_data = json.loads(content)
            
            strategy = ExecutionStrategy(plan_data.get("strategy", "conversational"))
            agent_name = plan_data.get("agent_name")
            reasoning = plan_data.get("reasoning", "")
            
            # Validate agent name
            if strategy == ExecutionStrategy.SINGLE_AGENT and agent_name not in available_agents:
                logger.warning(f"Planner suggested unknown agent '{agent_name}'. Falling back to conversational.")
                strategy = ExecutionStrategy.CONVERSATIONAL
                agent_name = None
                
            return PlannerResponse(strategy=strategy, agent_name=agent_name, reasoning=reasoning)
            
        except Exception as e:
            logger.error(f"Planner failed to parse intent, falling back to conversational: {e}")
            return PlannerResponse(
                strategy=ExecutionStrategy.CONVERSATIONAL, 
                agent_name=None, 
                reasoning="Fallback due to error"
            )
