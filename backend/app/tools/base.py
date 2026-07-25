from abc import ABC, abstractmethod
from typing import Any
from app.schemas.execution import PermissionLevel, RetryConfig


class BaseTool(ABC):
    """Abstract base class for all FRIDAY tools."""

    @property
    @abstractmethod
    def name(self) -> str:
        """The name of the tool (must be unique)."""

    @property
    @abstractmethod
    def description(self) -> str:
        """A detailed description of what the tool does and when to use it."""

    @property
    @abstractmethod
    def parameters(self) -> dict[str, Any]:
        """
        JSON schema for the tool's parameters.
        Example:
        {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "The search query"}
            },
            "required": ["query"]
        }
        """

    @property
    def requires_permission(self) -> bool:
        """Returns True if the tool requires explicit user permission."""
        return self.permission_level == PermissionLevel.DESTRUCTIVE

    @property
    def permission_level(self) -> PermissionLevel:
        """The permission level required to execute this tool."""
        return PermissionLevel.SAFE

    @property
    def permission_scope(self) -> str:
        """A string representing the permission scope (e.g., 'fs:read', 'shell:execute')."""
        return f"{self.name}:execute"

    @property
    def timeout_seconds(self) -> int:
        """Maximum time in seconds allowed for the tool to execute."""
        return 60

    @property
    def retry_policy(self) -> RetryConfig:
        """Retry configuration for transient failures."""
        return RetryConfig()

    @property
    def version(self) -> str:
        """The version of this tool."""
        return "1.0.0"

    @abstractmethod
    async def execute(self, **kwargs) -> Any:
        """Execute the tool and return the result as a dict, string, or Any."""
