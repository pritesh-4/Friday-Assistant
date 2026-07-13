from fastapi import APIRouter, HTTPException, status

from app.schemas.common import Task, TaskCreate, TaskUpdate
from app.services.workspace_service import WorkspaceService

router = APIRouter(tags=["tasks"])
service = WorkspaceService()


@router.get("", response_model=list[Task])
async def list_tasks() -> list[Task]:
    return await service.list_tasks()


@router.post("", response_model=Task, status_code=status.HTTP_201_CREATED)
async def create_task(request: TaskCreate) -> Task:
    return await service.create_task(request)


@router.patch("/{task_id}", response_model=Task)
async def update_task(task_id: str, request: TaskUpdate) -> Task:
    return await service.update_task(task_id, request)


@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_task(task_id: str) -> None:
    if not await service.delete_task(task_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found.")
