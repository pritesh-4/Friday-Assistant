"""Executive Planner V1: The decision-making brain of F.R.I.D.A.Y."""

import json
from typing import Optional
from app.core.logging import get_logger
from app.db.database import Database
from app.services.llm_service import LLMService
from app.knowledge_graph.context_engine import ContextEngine
from app.schemas.executive_planning import (
    MissionPlan,
    SubTask,
    RiskAssessment,
    ContextSelection,
)
from app.schemas.planning import (
    Priority,
    Status,
    GoalBase,
    MilestoneBase,
    PlanningTaskBase,
    GoalCategory,
)
from app.intent.enums import RiskLevel
from app.intent.engine import IntentEngine
from app.tools.registry import tool_registry
from app.services.planning_service import planning_service

logger = get_logger("planning.executive")


class ExecutivePlanner:
    """Decomposes goals, selects tools, assesses risk, and constructs structured execution strategies."""

    def __init__(
        self, db: Database, llm_service: LLMService, context_engine: ContextEngine
    ) -> None:
        self.db = db
        self.llm_service = llm_service
        self.context_engine = context_engine
        self.intent_engine = IntentEngine()

    async def plan(
        self, query: str, conversation_id: Optional[str] = None
    ) -> MissionPlan:
        """
        Executes the planning pipeline:
        1. Classifies query using Intent Engine.
        2. Resolves Knowledge Graph contexts.
        3. Invokes planning LLM to generate structured MissionPlan.
        4. Triggers automatic Goal Decomposition storage if complex.
        """
        logger.info(f"Executive Planner analyzing request: '{query}'")

        # Step 1: Analyze Intent
        intent_res = None
        try:
            intent_res = await self.intent_engine.process(query, conversation_id)
        except Exception as e:
            logger.warning(f"Intent Engine processing failed: {e}")

        # Step 2: Retrieve Graph and Memory Contexts
        kg_context = None
        kg_context_md = ""
        try:
            kg_context = await self.context_engine.build_context(query)
            kg_context_md = self.context_engine.format_as_markdown(kg_context)
        except Exception as e:
            logger.warning(f"Context Engine retrieval failed: {e}")

        # Step 3: Build planning system prompt with tools and agents descriptions
        tools_prompt = tool_registry.get_tools_prompt()

        system_instruction = (
            "You are the Executive Planner, the central decision-making brain of F.R.I.D.A.Y.\n"
            "Your job is to analyze the user's request and decide HOW FRIDAY should accomplish it by creating a structured plan.\n"
            "DO NOT answer the user directly with a reply. Your job is ONLY to produce the strategy and plan.\n\n"
            f"Available Tools:\n{tools_prompt}\n\n"
            "Available Specialized Agents: ['WebResearchAgent']\n\n"
            "You MUST reply with a single JSON object matching the following structure, with NO other text or markdown formatting:\n"
            "{\n"
            '  "primary_goal": "The primary objective of the request",\n'
            '  "secondary_goals": ["supporting goal 1", ...],\n'
            '  "subtasks": [\n'
            "    {\n"
            '      "id": "task_id_1",\n'
            '      "title": "Short title",\n'
            '      "description": "Details of what to do",\n'
            '      "priority": "low" | "medium" | "high" | "critical",\n'
            '      "estimated_complexity": "low" | "medium" | "high",\n'
            '      "dependencies": [],\n'
            '      "status": "pending"\n'
            "    }\n"
            "  ],\n"
            '  "context": {\n'
            '    "memories": [],\n'
            '    "graph_nodes": [],\n'
            '    "projects": [],\n'
            '    "conversations": [],\n'
            '    "files": []\n'
            "  },\n"
            '  "tools": [\n'
            "    {\n"
            '      "tool_name": "Web Search" | "Repository Analyzer" | "Calculator" | "Code Executor",\n'
            '      "reason": "Why this tool is needed",\n'
            '      "permission_level": "safe" | "read_only" | "destructive"\n'
            "    }\n"
            "  ],\n"
            '  "provider_route": "Gemini" | "Claude" | "GPT",\n'
            '  "risks": {\n'
            '    "level": "Safe" | "Needs Confirmation" | "High Impact" | "Destructive" | "Expensive",\n'
            '    "confidence": 0.9,\n'
            '    "unknown_variables": [],\n'
            '    "failure_probability": 0.1,\n'
            '    "requires_confirmation": false,\n'
            '    "is_destructive": false,\n'
            '    "requires_authentication": false\n'
            "  },\n"
            '  "expected_result": "Details of successful outcome",\n'
            '  "fallback_strategy": "What to do if the primary strategy fails"\n'
            "}"
        )

        user_content = f"User Request: {query}\n"
        if intent_res:
            user_content += f"Extracted Intent: {intent_res.intent.value} (Confidence: {intent_res.confidence:.2f})\n"
        if kg_context_md:
            user_content += f"\nKnowledge Graph & Memory context:\n{kg_context_md}\n"

        messages = [
            {"role": "system", "content": system_instruction},
            {"role": "user", "content": user_content},
        ]

        # Step 4: Call LLM Provider
        provider = None
        if self.llm_service.available_providers:
            try:
                provider_name = next(iter(self.llm_service.available_providers))
                provider = self.llm_service.get_provider(provider_name)
            except Exception as e:
                logger.warning(f"Could not load LLM provider: {e}")

        if not provider:
            logger.warning("No LLM provider available. Falling back to default plan.")
            return self._generate_fallback_plan(query)

        try:
            response = await provider.generate_response(messages)
            content = response.content.strip()

            # Clean potential markdown block wrapping
            if content.startswith("```json"):
                content = content[7:]
            if content.endswith("```"):
                content = content[:-3]
            content = content.strip()

            plan_dict = json.loads(content)

            # Populate Context Selection with KG contexts if empty
            if not plan_dict.get("context") or not any(plan_dict["context"].values()):
                memories_list = (
                    kg_context.get("relevant_memories", []) if kg_context else []
                )
                nodes_list = (
                    [n.canonical_name for n in kg_context.get("relevant_nodes", [])]
                    if kg_context
                    else []
                )
                projects_list = (
                    [p.canonical_name for p in kg_context.get("relevant_projects", [])]
                    if kg_context
                    else []
                )
                plan_dict["context"] = {
                    "memories": memories_list,
                    "graph_nodes": nodes_list,
                    "projects": projects_list,
                    "conversations": [],
                    "files": [],
                }

            plan = MissionPlan.model_validate(plan_dict)

            # Step 5: Automatically save complex plans as Goals in database
            if len(plan.subtasks) > 1 or (
                intent_res
                and intent_res.intent.value
                in ("Planning", "Goal Creation", "Automation")
            ):
                await self._persist_goal_structure(plan)

            return plan

        except Exception as e:
            logger.error(
                f"Failed to generate or parse MissionPlan: {e}. Falling back to default."
            )
            return self._generate_fallback_plan(query)

    async def _persist_goal_structure(self, plan: MissionPlan) -> None:
        """Decomposes subtasks into Milestones and Tasks and saves them via PlanningService."""
        try:
            # Map subtasks to PlanningTaskBase
            tasks_base = []
            for sub in plan.subtasks:
                tasks_base.append(
                    PlanningTaskBase(
                        title=sub.title,
                        description=sub.description,
                        priority=sub.priority,
                        estimated_duration="1 hour",
                        requires_approval=plan.risks.requires_confirmation,
                        assigned_agent="GeneralAgent",
                        expected_output=plan.expected_result,
                        depends_on=sub.dependencies,
                    )
                )

            # Create Goal structure
            goal_base = GoalBase(
                title=plan.primary_goal,
                description=f"Auto-generated mission. Expected outcome: {plan.expected_result}",
                category=GoalCategory.GENERAL,
                milestones=[
                    MilestoneBase(
                        title="Execution Tasks", order_index=0, tasks=tasks_base
                    )
                ],
            )
            created_goal = await planning_service.create_goal(goal_base)
            logger.info(
                f"Auto-decomposed complex mission and persisted Goal: '{created_goal.id}'"
            )
        except Exception as e:
            logger.error(f"Failed to persist goal decomposition: {e}")

    def _generate_fallback_plan(self, query: str) -> MissionPlan:
        """Generates a default, safe execution plan when LLM/offline fails."""
        return MissionPlan(
            primary_goal=query,
            secondary_goals=[],
            subtasks=[
                SubTask(
                    id="task_fallback",
                    title="Process conversational request",
                    description="Answer the user's conversational query directly.",
                    priority=Priority.MEDIUM,
                    estimated_complexity="low",
                    dependencies=[],
                    status=Status.PENDING,
                )
            ],
            context=ContextSelection(),
            tools=[],
            provider_route="Gemini",
            risks=RiskAssessment(
                level=RiskLevel.SAFE,
                confidence=1.0,
                unknown_variables=[],
                failure_probability=0.0,
                requires_confirmation=False,
                is_destructive=False,
                requires_authentication=False,
            ),
            expected_result="Direct assistant text reply.",
            fallback_strategy="Respond conversationally.",
        )
