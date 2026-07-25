from fastapi import APIRouter, HTTPException, status
from typing import Any

from app.schemas.planning import Goal, GoalBase, Status
from app.services.planning_service import planning_service
from app.agents.scheduler import ExecutionScheduler
from app.agents.agent_manager import AgentManager
from app.services.llm_service import LLMService
from app.tools.manager import ToolManager

router = APIRouter(prefix="/planning", tags=["planning"])

# We initialize a singleton scheduler here for the routes to trigger.
# In a real production app, this would be managed by a lifespan event or dependency injection.
llm_svc = LLMService()
tool_mgr = ToolManager()
agent_mgr = AgentManager(llm_svc, tool_mgr)
scheduler = ExecutionScheduler(agent_mgr)

@router.on_event("startup")
async def startup_event():
    await scheduler.start()

@router.on_event("shutdown")
def shutdown_event():
    scheduler.stop()

@router.get("/goals", response_model=list[Goal])
async def list_goals():
    """Retrieve all goals."""
    return await planning_service.list_goals()

@router.get("/goals/{goal_id}", response_model=Goal)
async def get_goal(goal_id: str):
    """Retrieve a specific goal and its full DAG."""
    goal = await planning_service.get_goal(goal_id)
    if not goal:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Goal not found")
    return goal

@router.post("/goals", response_model=Goal, status_code=status.HTTP_201_CREATED)
async def create_goal(goal_data: GoalBase):
    """Manually create a new goal (usually the GoalAnalyzer does this)."""
    goal = await planning_service.create_goal(goal_data)
    await scheduler.trigger_evaluation(goal.id)
    return goal

@router.patch("/tasks/{task_id}/status")
async def update_task_status(task_id: str, payload: dict[str, Any]):
    """Update a task's status, triggering DAG recalculation."""
    new_status_str = payload.get("status")
    if not new_status_str:
        raise HTTPException(status_code=400, detail="Missing status field")
        
    try:
        new_status = Status(new_status_str)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid status: {new_status_str}")
        
    await planning_service.update_task_status(task_id, new_status)
    
    # We must trigger the scheduler on the parent goal to unblock downstream tasks
    from app.db.database import database
    row = await database.fetch_one(
        "SELECT m.goal_id FROM planning_tasks t JOIN milestones m ON t.milestone_id = m.id WHERE t.id = ?",
        (task_id,)
    )
    if row:
        await scheduler.trigger_evaluation(row["goal_id"])
        
    return {"status": "updated"}
