from fastapi import APIRouter
from app.schemas.memory import MemoryCreate

router = APIRouter(tags=["memory"])

@router.get("")
def get_memory_placeholder():
    """
    Placeholder endpoint to retrieve user memory/context.
    """
    return {
        "message": "Memory endpoint coming soon."
    }

@router.post("")
def post_memory_placeholder(request: MemoryCreate):
    """
    Placeholder endpoint to store new user memory/context.
    """
    return {
        "message": "Memory endpoint coming soon."
    }
