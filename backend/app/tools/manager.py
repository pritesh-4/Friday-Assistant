from typing import Any

from app.core.logging import get_logger
from app.tools.base import BaseTool
from app.tools.registry import tool_registry
from app.tools.executor import tool_executor, PermissionRequiredError
from app.schemas.execution import ToolExecutionRequest

logger = get_logger(__name__)


class ToolManager:
    """Manages registration, discovery, and execution of tools."""

    def __init__(self):
        # We delegate everything to the new architecture.
        pass

    def register(self, tool: BaseTool) -> None:
        tool_registry.register(tool)

    def get_tool(self, name: str) -> BaseTool | None:
        return tool_registry.get_tool(name)

    def get_all_tools(self) -> list[BaseTool]:
        return tool_registry.get_all_tools()

    def get_tools_prompt(self, allowed_tools: list[str] = None) -> str:
        return tool_registry.get_tools_prompt(allowed_tools)

    async def execute_tool(
        self, name: str, kwargs: dict[str, Any], approved_permissions: list[str] = None
    ) -> str:
        """Executes a tool by name with the given arguments using the new executor."""
        request = ToolExecutionRequest(tool_name=name, kwargs=kwargs)

        try:
            response = await tool_executor.execute(request, approved_permissions)
            if response.success:
                return str(response.result)
            else:
                return f"Error executing tool '{name}': {response.error}"
        except PermissionRequiredError as e:
            # Re-raise so the router can handle the approval flow
            raise e
