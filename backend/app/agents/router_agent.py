"""Routes requests using the PlannerAgent and executes them."""

from typing import Any, AsyncGenerator

from app.core.config import settings
from app.core.logging import get_logger
from app.services.llm_service import LLMService
from app.services.providers.base import LLMProviderError, LLMResult

from app.agents.planner_agent import PlannerAgent, ExecutionStrategy
from app.agents.agent_manager import AgentManager
from app.tools.manager import ToolManager
from app.tools.executor import PermissionRequiredError

logger = get_logger(__name__)

class RouterAgent:
    """Uses PlannerAgent to determine intent and routes to specialized agents."""

    def __init__(self) -> None:
        self.llm_service = LLMService()
        self.tool_manager = ToolManager()
        self.planner = PlannerAgent(self.llm_service)
        self.agent_manager = AgentManager(self.llm_service, self.tool_manager)

    async def route_and_execute(self, messages: list[dict[str, Any]], approved_permissions: list[str] | None = None) -> LLMResult:
        """
        Plans and executes the request. 
        Note: The return format is an LLMResult to maintain backwards compatibility,
        even if the work was done by an agent.
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

        # 1. Plan Execution
        available_agents = self.agent_manager.get_available_agents()
        plan = await self.planner.plan_execution(messages, available_agents)
        logger.info(f"Execution plan: Strategy={plan.strategy.value}, Agent={plan.agent_name}")

        # 2. Execute Strategy
        if plan.strategy == ExecutionStrategy.SINGLE_AGENT and plan.agent_name:
            try:
                agent = self.agent_manager.spawn_agent(plan.agent_name)
                # To simulate non-streaming, we exhaust the generator
                final_content = ""
                # We need the task string, typically the last user message
                task = messages[-1]["content"] if messages else ""
                
                async for chunk in agent.execute(task, messages, approved_permissions):
                    final_content += chunk + "\n"
                    
                return LLMResult(
                    content=final_content.strip(),
                    provider="AgentFramework",
                    model=plan.agent_name,
                    latency_ms=0,
                    finish_reason="stop"
                )
            except PermissionRequiredError as e:
                raise e # Handled by outer service
            except Exception as e:
                logger.error(f"Agent execution failed: {e}")
                # Fallback to conversational
                pass

        # Fallback / Conversational Strategy
        try:
            return await self._call_providers(messages)
        except Exception as e:
            raise LLMProviderError(f"Conversational generation failed: {e}")

    async def route_and_stream(self, messages: list[dict[str, Any]], approved_permissions: list[str] | None = None) -> AsyncGenerator[str, None]:
        """Plans and streams the response."""
        active_providers = self.llm_service.available_providers
        if not active_providers:
            yield "I saved your message to this conversation. Configure an API key in backend/.env to enable AI."
            return

        available_agents = self.agent_manager.get_available_agents()
        plan = await self.planner.plan_execution(messages, available_agents)
        logger.info(f"Execution plan: Strategy={plan.strategy.value}, Agent={plan.agent_name}")

        if plan.strategy == ExecutionStrategy.SINGLE_AGENT and plan.agent_name:
            try:
                agent = self.agent_manager.spawn_agent(plan.agent_name)
                task = messages[-1]["content"] if messages else ""
                
                async for chunk in agent.execute(task, messages, approved_permissions):
                    yield chunk + "\n"
                return
            except PermissionRequiredError as e:
                raise e
            except Exception as e:
                logger.error(f"Agent execution failed: {e}")
                yield f"Error running agent: {e}\nFalling back to chat.\n"

        # Conversational Strategy
        try:
            stream = await self._call_providers_stream(messages)
            async for chunk in stream:
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

    def _sanitize_for_text_only(self, messages: list[dict[str, Any]]) -> list[dict[str, Any]]:
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
                sanitized.append({"role": msg.get("role", "user"), "content": " ".join(text_parts).strip()})
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

    async def _call_providers_stream(self, messages: list[dict[str, Any]]) -> Any:
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
                        return provider.stream_response(messages)
                    except Exception as exc:
                        errors.append(f"{provider_name} (vision): {exc}")
            messages = self._sanitize_for_text_only(messages)

        for provider_name in chain:
            provider = self.llm_service.get_provider(provider_name)
            if not provider:
                continue
            try:
                return provider.stream_response(messages)
            except Exception as exc:
                errors.append(f"{provider_name}: {exc}")
                
        for provider_name, provider in self.llm_service.available_providers.items():
            if provider_name in chain:
                continue
            try:
                return provider.stream_response(messages)
            except Exception as exc:
                errors.append(f"{provider_name}: {exc}")
                
        raise LLMProviderError(f"All stream providers failed. Details: {' | '.join(errors)}")
