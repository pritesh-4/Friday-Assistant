from fastapi import APIRouter, HTTPException, Query, status

from app.schemas.memory import Memory, MemoryCreate
from app.services.memory_service import MemoryService

router = APIRouter(tags=["memory"])
service = MemoryService()


@router.get("", response_model=list[Memory])
async def list_memory(
    query: str | None = Query(default=None, max_length=200),
    limit: int = Query(default=100, ge=1, le=100),
) -> list[Memory]:
    """List user-approved memories or search them with a text query."""
    return await service.list_memories(query=query, limit=limit)


@router.post("", response_model=Memory, status_code=status.HTTP_201_CREATED)
async def create_memory(request: MemoryCreate) -> Memory:
    """Store a memory explicitly supplied by the user interface."""
    return await service.store_memory(request)


@router.delete("/{memory_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_memory(memory_id: str) -> None:
    if not await service.delete_memory(memory_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Memory not found.")
