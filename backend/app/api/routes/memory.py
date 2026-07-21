"""Memory route — long-term memory CRUD, search, and management."""

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.api.dependencies import get_memory_service
from app.schemas.memory import Memory, MemoryCreate, MemoryUpdate
from app.services.memory_service import MemoryService

router = APIRouter(tags=["memory"])


@router.get("", response_model=list[Memory])
async def list_memories(
    query: str | None = Query(default=None, max_length=200, description="Full-text search query."),
    category: str | None = Query(default=None, max_length=64, description="Filter by category."),
    limit: int = Query(default=100, ge=1, le=100),
    service: MemoryService = Depends(get_memory_service),
) -> list[Memory]:
    """List user memories, optionally filtered by a text query or category."""
    return await service.list_memories(query=query, category=category, limit=limit)


@router.get("/categories", response_model=list[str])
async def list_categories(
    service: MemoryService = Depends(get_memory_service),
) -> list[str]:
    """Return the distinct memory categories currently in use."""
    return await service.list_categories()


@router.get("/{memory_id}", response_model=Memory)
async def get_memory(
    memory_id: str,
    service: MemoryService = Depends(get_memory_service),
) -> Memory:
    """Retrieve a single memory by its ID."""
    memory = await service.get_memory(memory_id)
    if memory is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Memory not found.")
    return memory


@router.post("", response_model=Memory, status_code=status.HTTP_201_CREATED)
async def create_memory(
    request: MemoryCreate,
    service: MemoryService = Depends(get_memory_service),
) -> Memory:
    """Store a memory explicitly supplied by the user or the agent."""
    return await service.store_memory(request)


@router.patch("/{memory_id}", response_model=Memory)
async def update_memory(
    memory_id: str,
    request: MemoryUpdate,
    service: MemoryService = Depends(get_memory_service),
) -> Memory:
    """Partially update an existing memory's title, value, or category."""
    memory = await service.update_memory(memory_id, request)
    if memory is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Memory not found.")
    return memory


@router.post("/{memory_id}/pin", response_model=Memory)
async def pin_memory(
    memory_id: str,
    service: MemoryService = Depends(get_memory_service),
) -> Memory:
    """Pin a memory so it appears at the top of all listings."""
    memory = await service.set_pinned(memory_id, pinned=True)
    if memory is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Memory not found.")
    return memory


@router.delete("/{memory_id}/pin", status_code=status.HTTP_200_OK, response_model=Memory)
async def unpin_memory(
    memory_id: str,
    service: MemoryService = Depends(get_memory_service),
) -> Memory:
    """Remove the pin from a memory."""
    memory = await service.set_pinned(memory_id, pinned=False)
    if memory is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Memory not found.")
    return memory


@router.delete("/{memory_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_memory(
    memory_id: str,
    service: MemoryService = Depends(get_memory_service),
) -> None:
    """Permanently delete a memory."""
    if not await service.delete_memory(memory_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Memory not found.")
