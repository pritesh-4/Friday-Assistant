"""Analyzes complex user requests and breaks them down into Goals, Milestones, and DAG tasks."""

import json

from app.core.logging import get_logger
from app.services.llm_service import LLMService
from app.schemas.planning import GoalBase

logger = get_logger(__name__)


class GoalAnalyzer:
    """Uses LLM to structure complex project/goal requests."""

    def __init__(self, llm_service: LLMService):
        self.llm_service = llm_service

    async def analyze_goal(
        self, request_text: str, available_agents: list[str]
    ) -> GoalBase:
        """Parses a natural language request into a structured GoalBase object."""

        system_prompt = (
            "You are the Goal Analyzer for F.R.I.D.A.Y. AI.\n"
            "Your task is to take a user's complex request or goal and break it down into a structured project plan.\n\n"
            "The plan MUST consist of:\n"
            "1. A top-level Goal (with title, description, and category).\n"
            "2. Multiple Milestones representing major phases.\n"
            "3. Specific Tasks within each milestone.\n\n"
            "DAG Dependencies:\n"
            "- Tasks can depend on other tasks (using the 'depends_on' field, which should contain the exact titles of the prerequisite tasks).\n"
            "- A task title MUST be unique across the entire goal to properly link dependencies.\n\n"
            f"Available Specialized Agents: {', '.join(available_agents)}\n"
            "- Assign 'assigned_agent' to a specific agent name if a task can be automated by them.\n"
            "- Leave 'assigned_agent' as null if it's a manual task for the user or if no agent fits.\n\n"
            "Categories: 'learning', 'coding', 'career', 'personal', 'research', 'creative', 'general'.\n"
            "Priorities: 'low', 'medium', 'high', 'critical'.\n\n"
            "You MUST return ONLY a JSON object matching this schema exactly:\n"
            "{\n"
            '  "title": "...",\n'
            '  "description": "...",\n'
            '  "category": "learning",\n'
            '  "milestones": [\n'
            "    {\n"
            '      "title": "Phase 1: ...",\n'
            '      "order_index": 0,\n'
            '      "tasks": [\n'
            "        {\n"
            '          "title": "Unique Task Title",\n'
            '          "description": "...",\n'
            '          "priority": "medium",\n'
            '          "estimated_duration": "2 hours",\n'
            '          "requires_approval": true,\n'
            '          "assigned_agent": null,\n'
            '          "expected_output": "...",\n'
            '          "depends_on": []\n'
            "        }\n"
            "      ]\n"
            "    }\n"
            "  ]\n"
            "}\n"
        )

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": request_text},
        ]

        try:
            provider_name = next(iter(self.llm_service.available_providers))
            provider = self.llm_service.get_provider(provider_name)

            if not provider:
                raise RuntimeError("No LLM provider available for analysis")

            response = await provider.generate_response(messages)
            content = response.content.strip()

            if content.startswith("```json"):
                content = content[7:]
            if content.endswith("```"):
                content = content[:-3]

            content = content.strip()

            goal_data = json.loads(content)
            return GoalBase.model_validate(goal_data)

        except Exception as e:
            logger.error(f"Goal Analyzer failed: {e}")
            raise ValueError(f"Failed to analyze goal: {e}")
