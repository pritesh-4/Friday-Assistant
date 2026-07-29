"""Files route — user file upload and management."""

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status

from app.api.dependencies import get_file_service
from app.schemas.common import StoredFile
from app.services.file_service import FileService

router = APIRouter(tags=["files"])


@router.get("", response_model=list[StoredFile])
async def list_files(
    service: FileService = Depends(get_file_service),
) -> list[StoredFile]:
    """List private uploaded-file metadata. Raw storage paths are never returned."""
    return await service.list_files()


@router.post("", response_model=StoredFile, status_code=status.HTTP_201_CREATED)
async def upload_file(
    file: UploadFile = File(...),
    service: FileService = Depends(get_file_service),
) -> StoredFile:
    """Validate and save one supported user upload."""
    return await service.save_uploaded_file(file)


@router.delete("/{file_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_file(
    file_id: str,
    service: FileService = Depends(get_file_service),
) -> None:
    """Delete a file and its metadata permanently."""
    if not await service.delete_file(file_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="File not found."
        )
