import pytest
from typing import Any

from app.tools.base import BaseTool
from app.schemas.execution import ToolExecutionRequest, PermissionLevel, RetryConfig
from app.tools.executor import ToolExecutor, PermissionRequiredError
from app.tools.registry import ToolRegistry

class DummyTool(BaseTool):
    def __init__(self, name: str, permission_level: PermissionLevel, retry_policy: RetryConfig, should_fail: bool = False):
        self._name = name
        self._permission_level = permission_level
        self._retry_policy = retry_policy
        self._should_fail = should_fail
        self.execution_count = 0

    @property
    def name(self) -> str:
        return self._name

    @property
    def description(self) -> str:
        return "Dummy tool"

    @property
    def permission_level(self) -> PermissionLevel:
        return self._permission_level

    @property
    def retry_policy(self) -> RetryConfig:
        return self._retry_policy

    @property
    def parameters(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "arg": {"type": "string"}
            },
            "required": ["arg"]
        }

    async def execute(self, arg: str, **kwargs) -> str:
        self.execution_count += 1
        if self._should_fail and self.execution_count <= self._retry_policy.max_retries:
            raise ValueError("Transient error")
        return f"success:{arg}"


@pytest.fixture
def test_registry():
    return ToolRegistry()


@pytest.fixture
def executor():
    return ToolExecutor()


@pytest.mark.asyncio
async def test_tool_validation_success(monkeypatch, executor, test_registry):
    tool = DummyTool("test_safe", PermissionLevel.SAFE, RetryConfig())
    test_registry.register(tool)
    monkeypatch.setattr("app.tools.executor.tool_registry", test_registry)

    req = ToolExecutionRequest(tool_name="test_safe", kwargs={"arg": "value"})
    res = await executor.execute(req)
    
    assert res.success is True
    assert res.result == "success:value"
    assert tool.execution_count == 1


@pytest.mark.asyncio
async def test_tool_validation_failure(monkeypatch, executor, test_registry):
    tool = DummyTool("test_safe", PermissionLevel.SAFE, RetryConfig())
    test_registry.register(tool)
    monkeypatch.setattr("app.tools.executor.tool_registry", test_registry)

    req = ToolExecutionRequest(tool_name="test_safe", kwargs={"wrong_arg": "value"})
    res = await executor.execute(req)
    
    assert res.success is False
    assert "Invalid arguments" in res.error
    assert tool.execution_count == 0


@pytest.mark.asyncio
async def test_tool_permission_denied(monkeypatch, executor, test_registry):
    tool = DummyTool("test_destructive", PermissionLevel.DESTRUCTIVE, RetryConfig())
    test_registry.register(tool)
    monkeypatch.setattr("app.tools.executor.tool_registry", test_registry)

    req = ToolExecutionRequest(tool_name="test_destructive", kwargs={"arg": "value"})
    
    with pytest.raises(PermissionRequiredError) as exc_info:
        await executor.execute(req, approved_permissions=[])
        
    assert exc_info.value.tool_name == "test_destructive"


@pytest.mark.asyncio
async def test_tool_permission_approved(monkeypatch, executor, test_registry):
    tool = DummyTool("test_destructive", PermissionLevel.DESTRUCTIVE, RetryConfig())
    test_registry.register(tool)
    monkeypatch.setattr("app.tools.executor.tool_registry", test_registry)

    req = ToolExecutionRequest(tool_name="test_destructive", kwargs={"arg": "value"})
    res = await executor.execute(req, approved_permissions=[tool.permission_scope])
    
    assert res.success is True
    assert tool.execution_count == 1


@pytest.mark.asyncio
async def test_tool_retry_policy(monkeypatch, executor, test_registry):
    # Tool fails twice, succeeds on third try
    retry_policy = RetryConfig(max_retries=2, backoff_factor=0.01)
    tool = DummyTool("test_retry", PermissionLevel.SAFE, retry_policy, should_fail=True)
    test_registry.register(tool)
    monkeypatch.setattr("app.tools.executor.tool_registry", test_registry)

    req = ToolExecutionRequest(tool_name="test_retry", kwargs={"arg": "value"})
    res = await executor.execute(req)
    
    assert res.success is True
    assert res.retries == 2
    assert tool.execution_count == 3


@pytest.mark.asyncio
async def test_tool_retry_exhausted(monkeypatch, executor, test_registry):
    # Tool fails always, retry exhausted
    retry_policy = RetryConfig(max_retries=1, backoff_factor=0.01)
    tool = DummyTool("test_fail", PermissionLevel.SAFE, retry_policy, should_fail=True)
    # Patch execute to always fail
    async def always_fail(*args, **kwargs):
        tool.execution_count += 1
        raise ValueError("Permanent error")
    tool.execute = always_fail
    
    test_registry.register(tool)
    monkeypatch.setattr("app.tools.executor.tool_registry", test_registry)

    req = ToolExecutionRequest(tool_name="test_fail", kwargs={"arg": "value"})
    res = await executor.execute(req)
    
    assert res.success is False
    assert "Permanent error" in res.error
    assert tool.execution_count == 2
