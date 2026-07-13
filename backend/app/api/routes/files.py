from fastapi import APIRouter, File, HTTPException, UploadFile, status

from app.schemas.common import StoredFile
from app.services.file_service import FileService

router = APIRouter(tags=["files"])
service = FileService()


@router.get("", response_model=list[StoredFile])
async def list_files() -> list[StoredFile]:
    """List private uploaded-file metadata; raw paths are never returned."""
    return await service.list_files()


@router.post("", response_model=StoredFile, status_code=status.HTTP_201_CREATED)
async def upload_file(file: UploadFile = File(...)) -> StoredFile:
    """Validate and save one supported user upload."""
    return await service.save_uploaded_file(file)


@router.delete("/{file_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_file(file_id: str) -> None:
    if not await service.delete_file(file_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File not found.")
