"""Tool Registry for discovering and managing tools."""

import json
from app.core.logging import get_logger
from app.tools.base import BaseTool

logger = get_logger(__name__)


class ToolRegistry:
    """Centralized Tool Registry for F.R.I.D.A.Y."""

    def __init__(self):
        self._tools: dict[str, BaseTool] = {}

    def register(self, tool: BaseTool) -> None:
        """Register a new tool instance."""
        if tool.name in self._tools:
            logger.warning(f"Tool {tool.name} is already registered. Overwriting.")
        self._tools[tool.name] = tool
        logger.info(f"Registered tool: {tool.name} (v{tool.version})")

    def get_tool(self, name: str) -> BaseTool | None:
        """Retrieve a tool by name."""
        return self._tools.get(name)

    def get_all_tools(self) -> list[BaseTool]:
        """Get all registered tools."""
        return list(self._tools.values())

    def get_tools_prompt(self, allowed_tools: list[str] = None) -> str:
        """
        Returns a string description of all available tools for the LLM prompt.
        If allowed_tools is provided, only include those.
        """
        tools_to_include = []
        if allowed_tools is not None:
            for name in allowed_tools:
                if name in self._tools:
                    tools_to_include.append(self._tools[name])
        else:
            tools_to_include = self.get_all_tools()

        if not tools_to_include:
            return "No tools available."

        tool_descriptions = []
        for tool in tools_to_include:
            params = json.dumps(tool.parameters, indent=2)
            desc = (
                f"Tool Name: {tool.name}\n"
                f"Description: {tool.description}\n"
                f"Parameters (JSON Schema):\n{params}"
            )
            tool_descriptions.append(desc)

        return "\n\n---\n\n".join(tool_descriptions)


# Global singleton registry
tool_registry = ToolRegistry()
