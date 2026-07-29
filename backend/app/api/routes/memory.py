"""Memory route — long-term cognitive memory management."""

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.api.dependencies import get_memory_service
from app.schemas.memory import CognitiveMemoryPayload, MemoryType
from app.services.memory_service import CognitiveMemoryService

router = APIRouter(tags=["memory"])


@router.get("", response_model=list[CognitiveMemoryPayload])
async def list_memories(
    service: CognitiveMemoryService = Depends(get_memory_service),
) -> list[CognitiveMemoryPayload]:
    """List all user memories with observability metadata."""
    return await service.get_all_memories()


@router.get("/search")
async def search_memories(
    query: str = Query(..., description="Semantic search query"),
    service: CognitiveMemoryService = Depends(get_memory_service),
) -> dict[str, list[dict]]:
    """Retrieve memories using Vector similarity search."""
    return await service.retrieve_relevant_memories(query=query, limit_per_type=5)


@router.delete("/{memory_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_memory(
    memory_id: str,
    memory_type: MemoryType = Query(..., description="The type of memory to delete"),
    service: CognitiveMemoryService = Depends(get_memory_service),
) -> None:
    """Permanently delete a cognitive memory."""
    if not await service.delete_memory(memory_id, memory_type):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Memory not found."
        )
