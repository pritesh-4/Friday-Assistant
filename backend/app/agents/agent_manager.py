"""Agent Manager for lifecycle management of specialized agents."""

from app.core.logging import get_logger
from app.services.llm_service import LLMService
from app.tools.manager import ToolManager
from app.agents.base_agent import BaseAgent

logger = get_logger(__name__)


# Sample specialized agent for the framework
class WebResearchAgent(BaseAgent):
    @property
    def name(self) -> str:
        return "WebResearchAgent"

    @property
    def description(self) -> str:
        return (
            "An agent specializing in finding up-to-date information on the internet."
        )

    @property
    def allowed_tools(self) -> list[str]:
        return ["web_search"]


class AgentManager:
    """Manages the creation and lifecycle of specialized agents."""

    def __init__(self, llm_service: LLMService, tool_manager: ToolManager):
        self.llm_service = llm_service
        self.tool_manager = tool_manager

        # Registry of available agent classes
        self._agent_classes = {
            "WebResearchAgent": WebResearchAgent,
            # Future agents will be registered here (e.g., CodingAgent, FileAgent)
        }

    def get_available_agents(self) -> list[str]:
        """Returns a list of registered agent names."""
        return list(self._agent_classes.keys())

    def spawn_agent(self, agent_name: str) -> BaseAgent:
        """Instantiates an agent by name."""
        agent_cls = self._agent_classes.get(agent_name)
        if not agent_cls:
            raise ValueError(f"Agent '{agent_name}' is not registered.")

        logger.info(f"Spawning agent: {agent_name}")
        return agent_cls(self.llm_service, self.tool_manager)
