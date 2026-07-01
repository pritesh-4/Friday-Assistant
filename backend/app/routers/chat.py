from fastapi import APIRouter
from typing import List
from app.schemas.schemas import Conversation, Message

router = APIRouter(prefix="/chats", tags=["chats"])

@router.get("/", response_model=List[Conversation])
def get_conversations():
    # Placeholder returning empty lists
    return []

@router.get("/{chat_id}/messages", response_model=List[Message])
def get_messages(chat_id: str):
    return []
