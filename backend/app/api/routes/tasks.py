"""Tasks route — personal task list management."""

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.dependencies import get_workspace_service
from app.schemas.common import Task, TaskCreate, TaskUpdate
from app.services.workspace_service import WorkspaceService

router = APIRouter(tags=["tasks"])


@router.get("", response_model=list[Task])
async def list_tasks(
    service: WorkspaceService = Depends(get_workspace_service),
) -> list[Task]:
    """Return all tasks — pending tasks first, then sorted by due date."""
    return await service.list_tasks()


@router.post("", response_model=Task, status_code=status.HTTP_201_CREATED)
async def create_task(
    request: TaskCreate,
    service: WorkspaceService = Depends(get_workspace_service),
) -> Task:
    """Create a new task."""
    return await service.create_task(request)


@router.patch("/{task_id}", response_model=Task)
async def update_task(
    task_id: str,
    request: TaskUpdate,
    service: WorkspaceService = Depends(get_workspace_service),
) -> Task:
    """Partially update a task (status, priority, title, or due date)."""
    return await service.update_task(task_id, request)


@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_task(
    task_id: str,
    service: WorkspaceService = Depends(get_workspace_service),
) -> None:
    """Delete a task permanently."""
    if not await service.delete_task(task_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found.")
