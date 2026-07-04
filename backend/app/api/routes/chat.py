from fastapi import APIRouter
from app.schemas.chat import ChatRequest

router = APIRouter(tags=["chat"])

@router.get("")
def get_chat_placeholder():
    """
    Placeholder endpoint to retrieve conversations/chats.
    """
    return {
        "message": "Chat endpoint coming soon."
    }

@router.post("")
def post_chat_placeholder(request: ChatRequest):
    """
    Placeholder endpoint to receive user prompts and generate replies.
    """
    return {
        "message": "Chat endpoint coming soon."
    }
