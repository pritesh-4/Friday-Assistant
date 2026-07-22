import json
from typing import Any

from app.core.config import settings
from app.core.logging import get_logger
from app.services.llm_service import LLMService
from app.services.providers.base import LLMProviderError, LLMResult
from app.tools import tool_manager

logger = get_logger(__name__)

class RouterAgent:
    """Routes the incoming request to the appropriate LLM provider and handles tool calls."""

    def __init__(self) -> None:
        self.llm_service = LLMService()

    def _inject_tools_prompt(self, messages: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Injects tool descriptions into the system prompt."""
        tools_prompt = tool_manager.get_tools_prompt()
        if tools_prompt == "No tools available.":
            return messages

        system_instruction = (
            "You are FRIDAY, an advanced AI assistant. "
            "You have access to the following tools:\n\n"
            f"{tools_prompt}\n\n"
            "If you need to use a tool to answer the user's request, you MUST reply with ONLY a JSON object in the following format:\n"
            "{\n"
            '  "tool": "tool_name",\n'
            '  "kwargs": {"param1": "value1"}\n'
            "}\n"
            "Do not include any other text if you are calling a tool. "
            "If you do not need a tool, just answer normally as text."
        )

        # Check if the first message is a system message
        new_messages = list(messages)
        if new_messages and new_messages[0]["role"] == "system":
            new_messages[0]["content"] = system_instruction + "\n\n" + str(new_messages[0]["content"])
        else:
            new_messages.insert(0, {"role": "system", "content": system_instruction})

        return new_messages

    async def route_and_execute(self, messages: list[dict[str, Any]]) -> LLMResult:
        """
        Selects a provider, executes it, and handles any tool calls in a loop.
        """
        active_providers = self.llm_service.available_providers
        if not active_providers:
            return LLMResult(
                content=(
                    "I saved your message to this conversation. Configure at least one "
                    "provider (GROQ_API_KEY, GEMINI_API_KEY, OPENROUTER_API_KEY, or NVIDIA_API_KEY) "
                    "in backend/.env to enable AI-generated replies."
                ),
                provider="local-fallback",
                model="offline-storage",
                latency_ms=0,
                finish_reason="offline",
            )

        current_messages = self._inject_tools_prompt(messages)
        
        # Max tool iterations to prevent infinite loops
        max_iterations = 3
        total_latency = 0
        last_provider = "unknown"
        last_model = "unknown"

        for _ in range(max_iterations):
            # Attempt LLM inference
            result = await self._call_providers(current_messages)
            total_latency += result.latency_ms
            last_provider = result.provider
            last_model = result.model
            
            content = result.content.strip()
            
            # Check if it's a JSON tool call
            if content.startswith("{") and content.endswith("}") and '"tool"' in content:
                try:
                    tool_call = json.loads(content)
                    tool_name = tool_call.get("tool")
                    tool_kwargs = tool_call.get("kwargs", {})
                    
                    if tool_name:
                        # Append the LLM's tool call message
                        current_messages.append({"role": "assistant", "content": content})
                        
                        # Execute the tool
                        tool_result = await tool_manager.execute_tool(tool_name, tool_kwargs)
                        
                        # Append the tool observation
                        observation = f"Tool '{tool_name}' result:\n{tool_result}"
                        current_messages.append({"role": "system", "content": observation})
                        continue  # Loop again with the new context
                except json.JSONDecodeError:
                    pass # Not a valid tool JSON, fall through and return as normal response

            # If we reach here, it's not a tool call, or we failed to parse it, so return the final answer
            return LLMResult(
                content=content,
                provider=last_provider,
                model=last_model,
                latency_ms=total_latency,
                finish_reason=result.finish_reason
            )

        # Fallback if max iterations reached
        return LLMResult(
            content="I used too many tools and had to stop. Please try asking in a different way.",
            provider=last_provider,
            model=last_model,
            latency_ms=total_latency,
            finish_reason="max_iterations"
        )

    async def _call_providers(self, messages: list[dict[str, Any]]) -> LLMResult:
        chain = []
        for p in settings.fallback_chain:
            if p not in chain:
                chain.append(p)
                
        errors = []
        for provider_name in chain:
            provider = self.llm_service.get_provider(provider_name)
            if not provider:
                continue
            try:
                return await provider.generate_response(messages)
            except Exception as exc:
                logger.error(f"Provider {provider_name} failed: {exc}")
                errors.append(f"{provider_name}: {exc}")
                
        active_providers = self.llm_service.available_providers
        for provider_name, provider in active_providers.items():
            if provider_name in chain:
                continue
            try:
                return await provider.generate_response(messages)
            except Exception as exc:
                errors.append(f"{provider_name}: {exc}")
                
        raise LLMProviderError(f"All providers failed. Details: {' | '.join(errors)}")
