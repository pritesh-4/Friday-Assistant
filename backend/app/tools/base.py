from abc import ABC, abstractmethod
from typing import Any

class BaseTool(ABC):
    """Abstract base class for all FRIDAY tools."""

    @property
    @abstractmethod
    def name(self) -> str:
        """The name of the tool (must be unique)."""
        pass

    @property
    @abstractmethod
    def description(self) -> str:
        """A detailed description of what the tool does and when to use it."""
        pass

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
        pass

    @abstractmethod
    async def execute(self, **kwargs) -> str:
        """Execute the tool and return the result as a string."""
        pass
