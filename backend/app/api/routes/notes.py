from fastapi import APIRouter, HTTPException, status

from app.schemas.common import Note, NoteCreate
from app.services.workspace_service import WorkspaceService

router = APIRouter(tags=["notes"])
service = WorkspaceService()


@router.get("", response_model=list[Note])
async def list_notes() -> list[Note]:
    return await service.list_notes()


@router.post("", response_model=Note, status_code=status.HTTP_201_CREATED)
async def create_note(request: NoteCreate) -> Note:
    return await service.create_note(request)


@router.delete("/{note_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_note(note_id: str) -> None:
    if not await service.delete_note(note_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Note not found.")
