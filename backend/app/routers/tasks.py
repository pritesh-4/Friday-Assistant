from fastapi import APIRouter
from typing import List
from app.schemas.schemas import Task

router = APIRouter(prefix="/tasks", tags=["tasks"])

@router.get("/", response_model=List[Task])
def get_tasks():
    return []
