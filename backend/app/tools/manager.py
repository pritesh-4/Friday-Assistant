import json
from typing import Any

from app.core.logging import get_logger
from app.tools.base import BaseTool

logger = get_logger(__name__)

class ToolManager:
    """Manages registration, discovery, and execution of tools."""

    def __init__(self):
        self._tools: dict[str, BaseTool] = {}

    def register(self, tool: BaseTool) -> None:
        if tool.name in self._tools:
            logger.warning(f"Tool {tool.name} is already registered. Overwriting.")
        self._tools[tool.name] = tool

    def get_tool(self, name: str) -> BaseTool | None:
        return self._tools.get(name)

    def get_all_tools(self) -> list[BaseTool]:
        return list(self._tools.values())

    def get_tools_prompt(self) -> str:
        """Returns a string description of all available tools for the LLM prompt."""
        if not self._tools:
            return "No tools available."

        tool_descriptions = []
        for name, tool in self._tools.items():
            params = json.dumps(tool.parameters, indent=2)
            desc = f"Tool Name: {name}\nDescription: {tool.description}\nParameters (JSON Schema):\n{params}"
            tool_descriptions.append(desc)
        
        return "\n\n---\n\n".join(tool_descriptions)

    async def execute_tool(self, name: str, kwargs: dict[str, Any]) -> str:
        """Executes a tool by name with the given arguments."""
        tool = self.get_tool(name)
        if not tool:
            return f"Error: Tool '{name}' not found."
        
        try:
            logger.info(f"Executing tool '{name}' with kwargs: {kwargs}")
            result = await tool.execute(**kwargs)
            return str(result)
        except Exception as e:
            logger.error(f"Error executing tool '{name}': {e}", exc_info=True)
            return f"Error executing tool '{name}': {e!s}"
