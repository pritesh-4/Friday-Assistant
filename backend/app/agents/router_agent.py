"""Routes requests using the PlannerAgent and executes them."""

from typing import Any, AsyncGenerator

from app.core.config import settings
from app.core.logging import get_logger
from app.services.llm_service import LLMService
from app.services.providers.base import LLMProviderError, LLMResult

from app.agents.planner_agent import PlannerAgent
from app.agents.agent_manager import AgentManager
from app.tools.manager import ToolManager
from app.tools.executor import PermissionRequiredError
from app.planning.executive import ExecutivePlanner
from app.db.database import database
from app.db.vector_store import vector_store
from app.storage.repository import MemoryRepository
from app.knowledge_graph.graph import KnowledgeGraph
from app.knowledge_graph.context_engine import ContextEngine

logger = get_logger(__name__)


class RouterAgent:
    """Uses ExecutivePlanner to determine intent and routes to specialized agents."""

    def __init__(self) -> None:
        self.llm_service = LLMService()
        self.tool_manager = ToolManager()
        self.planner = PlannerAgent(self.llm_service)
        self.agent_manager = AgentManager(self.llm_service, self.tool_manager)

        # Initialize dependencies for Executive Planner
        self.repository = MemoryRepository(database, vector_store)
        self.graph = KnowledgeGraph(self.repository)
        self.context_engine = ContextEngine(self.graph, self.repository)
        self.executive_planner = ExecutivePlanner(
            database, self.llm_service, self.context_engine
        )

    async def route_and_execute(
        self,
        messages: list[dict[str, Any]],
        approved_permissions: list[str] | None = None,
    ) -> LLMResult:
        """
        Plans and executes the request.
        """
        active_providers = self.llm_service.available_providers
        if not active_providers:
            return LLMResult(
                content="I saved your message to this conversation. Configure an API key in backend/.env to enable AI.",
                provider="local-fallback",
                model="offline-storage",
                latency_ms=0,
                finish_reason="offline",
            )

        # 1. Plan Execution with Executive Planner
        query = messages[-1]["content"] if messages else ""
        mission_plan = await self.executive_planner.plan(query)
        logger.info(
            f"Executive Planning strategy: goal='{mission_plan.primary_goal}', "
            f"risk_level={mission_plan.risks.level.value}, tools={[t.tool_name for t in mission_plan.tools]}"
        )

        # Safety / confirmation override check
        if mission_plan.risks.requires_confirmation:
            is_approved = approved_permissions and any(
                p in approved_permissions for p in ("safe", "read_only", "destructive")
            )
            if not is_approved:
                raise PermissionRequiredError(
                    tool_name="Executive Planner",
                    scope=mission_plan.risks.level.value,
                    kwargs={"primary_goal": mission_plan.primary_goal},
                )

        # Determine strategy and specialized agent to route to
        agent_name = None
        for rec in mission_plan.tools:
            if rec.tool_name.lower() in ("web search", "web_search", "search"):
                agent_name = "WebResearchAgent"
                break

        # 2. Execute Strategy
        if agent_name:
            try:
                agent = self.agent_manager.spawn_agent(agent_name)
                final_content = ""
                async for chunk in agent.execute(query, messages, approved_permissions):
                    final_content += chunk + "\n"

                return LLMResult(
                    content=final_content.strip(),
                    provider="AgentFramework",
                    model=agent_name,
                    latency_ms=0,
                    finish_reason="stop",
                )
            except PermissionRequiredError as e:
                raise e
            except Exception as e:
                logger.error(f"Agent execution failed: {e}")
                pass

        # Fallback / Conversational Strategy
        try:
            return await self._call_providers(messages)
        except Exception as e:
            raise LLMProviderError(f"Conversational generation failed: {e}")

    async def route_and_stream(
        self,
        messages: list[dict[str, Any]],
        approved_permissions: list[str] | None = None,
    ) -> AsyncGenerator[str, None]:
        """Plans and streams the response."""
        active_providers = self.llm_service.available_providers
        if not active_providers:
            yield "I saved your message to this conversation. Configure an API key in backend/.env to enable AI."
            return

        query = messages[-1]["content"] if messages else ""
        mission_plan = await self.executive_planner.plan(query)
        logger.info(
            f"Executive Planning strategy (stream): goal='{mission_plan.primary_goal}', "
            f"risk_level={mission_plan.risks.level.value}"
        )

        # Safety / confirmation override check
        if mission_plan.risks.requires_confirmation:
            is_approved = approved_permissions and any(
                p in approved_permissions for p in ("safe", "read_only", "destructive")
            )
            if not is_approved:
                raise PermissionRequiredError(
                    tool_name="Executive Planner",
                    scope=mission_plan.risks.level.value,
                    kwargs={"primary_goal": mission_plan.primary_goal},
                )

        agent_name = None
        for rec in mission_plan.tools:
            if rec.tool_name.lower() in ("web search", "web_search", "search"):
                agent_name = "WebResearchAgent"
                break

        if agent_name:
            try:
                agent = self.agent_manager.spawn_agent(agent_name)
                async for chunk in agent.execute(query, messages, approved_permissions):
                    yield chunk + "\n"
                return
            except PermissionRequiredError as e:
                raise e
            except Exception as e:
                logger.error(f"Agent execution failed: {e}")
                yield f"Error running agent: {e}\nFalling back to chat.\n"

        # Conversational Strategy
        try:
            async for chunk in self._call_providers_stream(messages):
                yield chunk
        except Exception as e:
            yield f"Error: {e}"

    def _contains_images(self, messages: list[dict[str, Any]]) -> bool:
        for msg in messages:
            content = msg.get("content")
            if isinstance(content, list):
                for item in content:
                    if isinstance(item, dict) and item.get("type") == "image_url":
                        return True
        return False

    def _sanitize_for_text_only(
        self, messages: list[dict[str, Any]]
    ) -> list[dict[str, Any]]:
        sanitized = []
        for msg in messages:
            content = msg.get("content")
            if isinstance(content, list):
                text_parts = []
                for item in content:
                    if isinstance(item, dict):
                        if item.get("type") == "text":
                            text_parts.append(item.get("text", ""))
                        elif item.get("type") == "image_url":
                            text_parts.append("[Attached Image]")
                sanitized.append(
                    {
                        "role": msg.get("role", "user"),
                        "content": " ".join(text_parts).strip(),
                    }
                )
            else:
                sanitized.append(msg)
        return sanitized

    async def _call_providers(self, messages: list[dict[str, Any]]) -> LLMResult:
        chain = []
        for p in settings.fallback_chain:
            if p not in chain:
                chain.append(p)

        errors = []
        has_images = self._contains_images(messages)

        if has_images:
            for provider_name in chain:
                provider = self.llm_service.get_provider(provider_name)
                if provider and provider.supports_vision:
                    try:
                        return await provider.generate_response(messages)
                    except Exception as exc:
                        errors.append(f"{provider_name} (vision): {exc}")
            messages = self._sanitize_for_text_only(messages)

        for provider_name in chain:
            provider = self.llm_service.get_provider(provider_name)
            if not provider:
                continue
            try:
                return await provider.generate_response(messages)
            except Exception as exc:
                errors.append(f"{provider_name}: {exc}")

        for provider_name, provider in self.llm_service.available_providers.items():
            if provider_name in chain:
                continue
            try:
                return await provider.generate_response(messages)
            except Exception as exc:
                errors.append(f"{provider_name}: {exc}")

        raise LLMProviderError(f"All providers failed. Details: {' | '.join(errors)}")

    async def _call_providers_stream(
        self, messages: list[dict[str, Any]]
    ) -> AsyncGenerator[str, None]:
        chain = []
        for p in settings.fallback_chain:
            if p not in chain:
                chain.append(p)

        errors = []
        has_images = self._contains_images(messages)

        if has_images:
            for provider_name in chain:
                provider = self.llm_service.get_provider(provider_name)
                if provider and provider.supports_vision:
                    has_yielded = False
                    try:
                        async for chunk in provider.stream_response(messages):
                            has_yielded = True
                            yield chunk
                        if has_yielded:
                            return
                    except Exception as exc:
                        errors.append(f"{provider_name} (vision): {exc}")
                        if has_yielded:
                            raise
            messages = self._sanitize_for_text_only(messages)

        for provider_name in chain:
            provider = self.llm_service.get_provider(provider_name)
            if not provider:
                continue
            has_yielded = False
            try:
                async for chunk in provider.stream_response(messages):
                    has_yielded = True
                    yield chunk
                if has_yielded:
                    return
            except Exception as exc:
                errors.append(f"{provider_name}: {exc}")
                if has_yielded:
                    raise

        for provider_name, provider in self.llm_service.available_providers.items():
            if provider_name in chain:
                continue
            has_yielded = False
            try:
                async for chunk in provider.stream_response(messages):
                    has_yielded = True
                    yield chunk
                if has_yielded:
                    return
            except Exception as exc:
                errors.append(f"{provider_name}: {exc}")
                if has_yielded:
                    raise

        raise LLMProviderError(
            f"All stream providers failed. Details: {' | '.join(errors)}"
        )
