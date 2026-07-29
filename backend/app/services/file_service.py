import asyncio
from pathlib import Path

from fastapi import HTTPException, UploadFile, status

from app.core.config import settings
from app.db.database import database
from app.schemas.common import StoredFile
from app.utils.helpers import generate_uuid, get_utc_now


class FileService:
    """Keep small user uploads in a private, application-controlled directory."""

    allowed_extensions = {
        ".csv",
        ".docx",
        ".jpeg",
        ".jpg",
        ".json",
        ".md",
        ".pdf",
        ".png",
        ".txt",
        ".webp",
    }

    async def list_files(self) -> list[StoredFile]:
        rows = await database.fetch_all("SELECT * FROM files ORDER BY created_at DESC")
        return [StoredFile.model_validate(row) for row in rows]

    async def save_uploaded_file(self, upload: UploadFile) -> StoredFile:
        import re

        raw_name = Path(upload.filename or "").name
        # Sanitize filename to prevent malicious header injections or unsafe filesystem chars
        original_name = re.sub(r"[^a-zA-Z0-9_.-]", "_", raw_name) or "unnamed_file"
        suffix = Path(original_name).suffix.lower()
        if not original_name or suffix not in self.allowed_extensions:
            raise HTTPException(
                status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
                detail="Unsupported file type.",
            )

        content = await upload.read(settings.max_upload_size_bytes + 1)
        if not content:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="File is empty."
            )
        if len(content) > settings.max_upload_size_bytes:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"File exceeds the {settings.max_upload_size_bytes // (1024 * 1024)} MB limit.",
            )

        file_id = generate_uuid()
        uploads_dir = settings.uploads_directory.resolve()
        storage_path = (uploads_dir / f"{file_id}{suffix}").resolve()

        # Verify no path traversal outside uploads directory
        if not str(storage_path).startswith(str(uploads_dir)):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid storage path."
            )

        await asyncio.to_thread(storage_path.parent.mkdir, parents=True, exist_ok=True)
        await asyncio.to_thread(storage_path.write_bytes, content)

        created_at = get_utc_now().isoformat()
        content_type = upload.content_type or "application/octet-stream"
        try:
            await database.execute(
                """
                INSERT INTO files (id, name, content_type, size_bytes, storage_path, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    file_id,
                    original_name,
                    content_type,
                    len(content),
                    str(storage_path),
                    created_at,
                ),
            )
        except Exception:
            await asyncio.to_thread(storage_path.unlink, missing_ok=True)
            raise
        finally:
            await upload.close()

        return StoredFile(
            id=file_id,
            name=original_name,
            content_type=content_type,
            size_bytes=len(content),
            created_at=created_at,
        )

    async def delete_file(self, file_id: str) -> bool:
        row = await database.fetch_one(
            "SELECT storage_path FROM files WHERE id = ?", (file_id,)
        )
        if row is None:
            return False
        await database.execute("DELETE FROM files WHERE id = ?", (file_id,))
        await asyncio.to_thread(Path(row["storage_path"]).unlink, missing_ok=True)
        return True
