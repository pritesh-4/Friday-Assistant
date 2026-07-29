"""Notes route — personal note CRUD."""

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.dependencies import get_workspace_service
from app.schemas.common import Note, NoteCreate, NoteUpdate
from app.services.workspace_service import WorkspaceService

router = APIRouter(tags=["notes"])


@router.get("", response_model=list[Note])
async def list_notes(
    service: WorkspaceService = Depends(get_workspace_service),
) -> list[Note]:
    """Return all notes, most recently updated first."""
    return await service.list_notes()


@router.get("/{note_id}", response_model=Note)
async def get_note(
    note_id: str,
    service: WorkspaceService = Depends(get_workspace_service),
) -> Note:
    """Retrieve a single note by ID."""
    return await service.get_note(note_id)


@router.post("", response_model=Note, status_code=status.HTTP_201_CREATED)
async def create_note(
    request: NoteCreate,
    service: WorkspaceService = Depends(get_workspace_service),
) -> Note:
    """Create a new note."""
    return await service.create_note(request)


@router.patch("/{note_id}", response_model=Note)
async def update_note(
    note_id: str,
    request: NoteUpdate,
    service: WorkspaceService = Depends(get_workspace_service),
) -> Note:
    """Partially update a note's title or content."""
    return await service.update_note(note_id, request)


@router.delete("/{note_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_note(
    note_id: str,
    service: WorkspaceService = Depends(get_workspace_service),
) -> None:
    """Delete a note permanently."""
    if not await service.delete_note(note_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Note not found."
        )
