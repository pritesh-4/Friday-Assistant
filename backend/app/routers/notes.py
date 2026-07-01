from fastapi import APIRouter
from typing import List
from app.schemas.schemas import Note

router = APIRouter(prefix="/notes", tags=["notes"])

@router.get("/", response_model=List[Note])
def get_notes():
    return []
