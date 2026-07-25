"""Base class for specialized Agents."""

import json
from abc import ABC, abstractmethod
from typing import Any, AsyncGenerator

from app.core.logging import get_logger
from app.services.llm_service import LLMService
from app.tools.manager import ToolManager
from app.tools.executor import PermissionRequiredError

logger = get_logger(__name__)

class BaseAgent(ABC):
    """Abstract base class for all specialized execution agents."""

    def __init__(self, llm_service: LLMService, tool_manager: ToolManager):
        self.llm_service = llm_service
        self.tool_manager = tool_manager

    @property
    @abstractmethod
    def name(self) -> str:
        """The agent's name (e.g., 'CodingAgent')."""

    @property
    @abstractmethod
    def description(self) -> str:
        """Description of what this agent excels at."""

    @property
    @abstractmethod
    def allowed_tools(self) -> list[str]:
        """List of tool names this agent is allowed to use."""

    def _build_system_prompt(self, task: str) -> str:
        """Construct the system prompt for this specific agent."""
        tools_prompt = self.tool_manager.get_tools_prompt(self.allowed_tools)
        
        prompt = (
            f"You are the {self.name}. {self.description}\n\n"
            f"Your current task is: {task}\n\n"
            "You have access to the following tools:\n\n"
            f"{tools_prompt}\n\n"
            "If you need to use a tool, you MUST reply with ONLY a JSON object in the following format:\n"
            "{\n"
            '  "tool": "tool_name",\n'
            '  "kwargs": {"param1": "value1"}\n'
            "}\n"
            "Do not include any other text if you are calling a tool. "
            "If you have completed the task or do not need a tool, answer normally as text."
        )
        return prompt

    async def execute(self, task: str, context_messages: list[dict[str, Any]], approved_permissions: list[str] = None) -> AsyncGenerator[str, None]:
        """
        Executes a specific task. Yields strings (thoughts/results) back to the caller.
        """
        # Create a fresh message history for this agent's execution loop
        messages = list(context_messages)
        messages.insert(0, {"role": "system", "content": self._build_system_prompt(task)})

        max_iterations = 10
        yield f"[{self.name}] Starting execution..."

        for _ in range(max_iterations):
            # We use a fallback chain via LLMService. For simplicity, we just take the first active provider.
            # In a full implementation, we'd iterate through providers like RouterAgent does.
            provider_name = next(iter(self.llm_service.available_providers))
            provider = self.llm_service.get_provider(provider_name)
            
            try:
                response = await provider.generate_response(messages)
            except Exception as e:
                yield f"[{self.name}] LLM Error: {e}"
                return

            content = response.content.strip()

            # Check for tool call
            if content.startswith("{") and content.endswith("}") and '"tool"' in content:
                try:
                    tool_call = json.loads(content)
                    tool_name = tool_call.get("tool")
                    tool_kwargs = tool_call.get("kwargs", {})

                    if tool_name not in self.allowed_tools:
                        yield f"[{self.name}] Attempted to use unauthorized tool: {tool_name}"
                        messages.append({"role": "assistant", "content": content})
                        messages.append({"role": "system", "content": f"Error: Tool '{tool_name}' is not allowed for this agent."})
                        continue

                    yield f"[{self.name}] Using tool: {tool_name}..."
                    messages.append({"role": "assistant", "content": content})

                    try:
                        # Call the tool
                        tool_result = await self.tool_manager.execute_tool(tool_name, tool_kwargs, approved_permissions)
                        observation = f"Tool '{tool_name}' result:\n{tool_result}"
                        messages.append({"role": "system", "content": observation})
                        # yield f"[{self.name}] Tool {tool_name} returned successfully."
                    except PermissionRequiredError as e:
                        # Bubble this up to the caller (e.g., Planner/Router) to handle the UI prompt
                        yield f"[{self.name}] PERMISSION_REQUIRED: {e.scope}"
                        raise e

                    continue # Loop again with the new observation

                except json.JSONDecodeError:
                    pass # Not a valid JSON, just standard text output

            # Reached a final answer
            yield content
            return

        yield f"[{self.name}] Exhausted maximum iterations ({max_iterations})."
