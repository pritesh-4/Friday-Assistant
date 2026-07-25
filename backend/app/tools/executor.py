"""Tool Executor for secure, resilient tool invocation."""

import asyncio
import time
from typing import Any
import jsonschema

from app.core.logging import get_logger
from app.schemas.execution import ToolExecutionRequest, ToolExecutionResponse
from app.tools.registry import tool_registry

logger = get_logger(__name__)

class PermissionRequiredError(Exception):
    """Raised when a tool requires explicit user permission."""
    def __init__(self, tool_name: str, scope: str, kwargs: dict[str, Any]):
        self.tool_name = tool_name
        self.scope = scope
        self.kwargs = kwargs
        super().__init__(f"Tool '{tool_name}' requires permission: {scope}")

class ToolExecutor:
    """Handles execution, validation, timeout, retries, and permissions for tools."""

    async def execute(
        self, 
        request: ToolExecutionRequest, 
        approved_permissions: list[str] = None
    ) -> ToolExecutionResponse:
        """Execute a tool with validation, timeout, retries, and permission checks."""
        start_time = time.time()
        approved_permissions = approved_permissions or []

        tool = tool_registry.get_tool(request.tool_name)
        if not tool:
            return self._build_error_response("Tool not found.", start_time)

        # 1. Validation
        try:
            jsonschema.validate(instance=request.kwargs, schema=tool.parameters)
        except jsonschema.ValidationError as e:
            return self._build_error_response(f"Invalid arguments: {e.message}", start_time)

        # 2. Permission Check
        if tool.requires_permission and tool.permission_scope not in approved_permissions:
            # We raise this so the upper layer (Agent/Router) can catch it and prompt the user
            raise PermissionRequiredError(tool.name, tool.permission_scope, request.kwargs)

        # 3. Execution with Retries & Timeout
        retries = 0
        max_retries = tool.retry_policy.max_retries
        backoff = tool.retry_policy.backoff_factor

        while retries <= max_retries:
            try:
                # Run the tool with timeout
                result = await asyncio.wait_for(
                    tool.execute(**request.kwargs),
                    timeout=tool.timeout_seconds
                )
                
                execution_time = int((time.time() - start_time) * 1000)
                logger.info(f"Tool '{tool.name}' executed successfully in {execution_time}ms")
                
                return ToolExecutionResponse(
                    success=True,
                    result=result,
                    execution_time_ms=execution_time,
                    retries=retries
                )

            except asyncio.TimeoutError:
                err_msg = f"Tool '{tool.name}' timed out after {tool.timeout_seconds}s"
                logger.warning(err_msg)
            
            except Exception as e:
                err_msg = f"Tool '{tool.name}' failed: {e!s}"
                logger.warning(err_msg)

            retries += 1
            if retries <= max_retries:
                sleep_time = min(backoff * (2 ** (retries - 1)), tool.retry_policy.max_backoff)
                logger.info(f"Retrying tool '{tool.name}' in {sleep_time}s... ({retries}/{max_retries})")
                await asyncio.sleep(sleep_time)

        # Exhausted retries
        execution_time = int((time.time() - start_time) * 1000)
        return ToolExecutionResponse(
            success=False,
            result=None,
            error=err_msg,
            execution_time_ms=execution_time,
            retries=retries - 1
        )

    def _build_error_response(self, error: str, start_time: float) -> ToolExecutionResponse:
        execution_time = int((time.time() - start_time) * 1000)
        return ToolExecutionResponse(
            success=False,
            result=None,
            error=error,
            execution_time_ms=execution_time
        )

# Global singleton executor
tool_executor = ToolExecutor()
