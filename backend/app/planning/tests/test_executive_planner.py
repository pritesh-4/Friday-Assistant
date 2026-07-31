import pytest
from unittest.mock import AsyncMock, MagicMock

from app.intent.enums import RiskLevel
from app.tools.executor import PermissionRequiredError
from app.services.planning_service import planning_service
from app.planning.executive import ExecutivePlanner
from app.services.llm_service import LLMService


@pytest.mark.asyncio
async def test_executive_planner_fallback_flow(executive_planner):
    # Running without LLM provider config triggers the default fallback plan
    plan = await executive_planner.plan("Hello FRIDAY")

    assert plan is not None
    assert plan.primary_goal == "Hello FRIDAY"
    assert len(plan.subtasks) == 1
    assert plan.subtasks[0].title == "Process conversational request"
    assert plan.risks.level == RiskLevel.SAFE
    assert plan.risks.requires_confirmation is False


@pytest.mark.asyncio
async def test_executive_planner_llm_flow(graph, repository, context_engine):
    # Mock LLM provider to return structured MissionPlan JSON
    llm_mock = MagicMock(spec=LLMService)
    provider_mock = MagicMock()
    provider_mock.is_configured = True

    mock_plan_json = """
    {
      "primary_goal": "Build authentication",
      "secondary_goals": ["Setup Database", "Integrate JWT"],
      "subtasks": [
        {
          "id": "task_db",
          "title": "Setup database tables",
          "description": "Configure SQLite auth tables",
          "priority": "high",
          "estimated_complexity": "medium",
          "dependencies": [],
          "status": "pending"
        },
        {
          "id": "task_jwt",
          "title": "Setup JWT generation",
          "description": "Implement encode/decode endpoints",
          "priority": "high",
          "estimated_complexity": "medium",
          "dependencies": ["task_db"],
          "status": "pending"
        }
      ],
      "context": {
        "memories": [],
        "graph_nodes": [],
        "projects": [],
        "conversations": [],
        "files": []
      },
      "tools": [
        {
          "tool_name": "Code Executor",
          "reason": "Test JWT endpoint locally",
          "permission_level": "read_only"
        }
      ],
      "provider_route": "gemini",
      "risks": {
        "level": "Safe",
        "confidence": 0.95,
        "unknown_variables": [],
        "failure_probability": 0.05,
        "requires_confirmation": false,
        "is_destructive": false,
        "requires_authentication": false
      },
      "expected_result": "Working JWT tokens",
      "fallback_strategy": "Conversational code guide"
    }
    """

    response_mock = MagicMock()
    response_mock.content = mock_plan_json
    provider_mock.generate_response = AsyncMock(return_value=response_mock)

    llm_mock.available_providers = {"gemini": provider_mock}
    llm_mock.get_provider = MagicMock(return_value=provider_mock)

    planner = ExecutivePlanner(repository.db, llm_mock, context_engine)

    # Run planner
    plan = await planner.plan("Build authentication")

    # Assert plan properties
    assert plan.primary_goal == "Build authentication"
    assert len(plan.subtasks) == 2
    assert plan.subtasks[1].dependencies == ["task_db"]
    assert plan.tools[0].tool_name == "Code Executor"

    # Verify Goal Decomposition was saved in database
    goals = await planning_service.list_goals()
    assert len(goals) == 1
    assert goals[0].title == "Build authentication"

    # Fetch full goal structure
    goal_structure = await planning_service.get_goal(goals[0].id)
    assert len(goal_structure.milestones) == 1
    assert len(goal_structure.milestones[0].tasks) == 2


@pytest.mark.asyncio
async def test_router_agent_routing_and_permissions(router_agent):
    # Mock router's executive planner to return a high-risk destructive plan
    provider_mock = MagicMock()
    provider_mock.is_configured = True

    mock_plan_json = """
    {
      "primary_goal": "Delete production tables",
      "secondary_goals": [],
      "subtasks": [],
      "context": {"memories": [], "graph_nodes": [], "projects": [], "conversations": [], "files": []},
      "tools": [],
      "provider_route": "gemini",
      "risks": {
        "level": "Destructive",
        "confidence": 1.0,
        "unknown_variables": [],
        "failure_probability": 0.5,
        "requires_confirmation": true,
        "is_destructive": true,
        "requires_authentication": true
      },
      "expected_result": "Purged database",
      "fallback_strategy": "Cancel operation"
    }
    """
    response_mock = MagicMock()
    response_mock.content = mock_plan_json
    provider_mock.generate_response = AsyncMock(return_value=response_mock)

    router_agent.llm_service._providers = {"gemini": provider_mock}

    # 1. Assert PermissionRequiredError is raised when not approved
    messages = [{"role": "user", "content": "Delete production tables"}]
    with pytest.raises(PermissionRequiredError) as exc_info:
        await router_agent.route_and_execute(messages)
    assert exc_info.value.tool_name == "Executive Planner"
    assert exc_info.value.scope == "Destructive"

    # 2. Succeeds conversational fallback when approved permissions contains safe/read_only/destructive
    res = await router_agent.route_and_execute(
        messages, approved_permissions=["destructive"]
    )
    assert res is not None


@pytest.mark.asyncio
async def test_router_agent_tool_routing(router_agent):
    # Mock planner to suggest Web Search tool
    provider_mock = MagicMock()
    provider_mock.is_configured = True

    mock_plan_json = """
    {
      "primary_goal": "Search the weather",
      "secondary_goals": [],
      "subtasks": [],
      "context": {"memories": [], "graph_nodes": [], "projects": [], "conversations": [], "files": []},
      "tools": [
        {
          "tool_name": "Web Search",
          "reason": "Need current weather report",
          "permission_level": "safe"
        }
      ],
      "provider_route": "gemini",
      "risks": {
        "level": "Safe",
        "confidence": 1.0,
        "unknown_variables": [],
        "failure_probability": 0.0,
        "requires_confirmation": false,
        "is_destructive": false,
        "requires_authentication": false
      },
      "expected_result": "Weather results",
      "fallback_strategy": "Assume sunny"
    }
    """
    response_mock = MagicMock()
    response_mock.content = mock_plan_json
    provider_mock.generate_response = AsyncMock(return_value=response_mock)

    router_agent.llm_service._providers = {"gemini": provider_mock}

    # Mock WebResearchAgent execution
    agent_mock = MagicMock()

    async def mock_execute(task, messages, approved_permissions):
        yield "The weather is currently 72 degrees and sunny."

    agent_mock.execute = mock_execute
    router_agent.agent_manager.spawn_agent = MagicMock(return_value=agent_mock)

    messages = [{"role": "user", "content": "Search the weather"}]
    res = await router_agent.route_and_execute(messages)

    assert res.provider == "AgentFramework"
    assert res.model == "WebResearchAgent"
    assert "72 degrees" in res.content
