from app.tools.base import BaseTool
from app.tools.manager import ToolManager
from app.tools.web_research import WebSearchTool

# Global tool manager instance
tool_manager = ToolManager()

# Register core tools
tool_manager.register(WebSearchTool())

__all__ = ["BaseTool", "ToolManager", "tool_manager", "WebSearchTool"]
