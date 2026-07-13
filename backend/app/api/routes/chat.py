from fastapi import APIRouter, HTTPException, Query, status

from app.schemas.chat import ChatRequest, ChatResponse, Conversation, Message
from app.services.chat_service import ChatService

router = APIRouter(tags=["chat"])
service = ChatService()


@router.get("", response_model=list[Conversation])
async def list_conversations() -> list[Conversation]:
    """Return local conversation summaries, newest first."""
    return await service.list_conversations()


@router.post("", response_model=ChatResponse, status_code=status.HTTP_201_CREATED)
async def send_chat_message(request: ChatRequest) -> ChatResponse:
    """Persist a user message and return the generated assistant reply."""
    return await service.send_message(request)


@router.get("/{conversation_id}/messages", response_model=list[Message])
async def get_conversation_messages(
    conversation_id: str, limit: int = Query(default=100, ge=1, le=100)
) -> list[Message]:
    """Read one conversation's bounded, chronologically ordered history."""
    return await service.get_messages(conversation_id, limit)


@router.delete("/{conversation_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_conversation(conversation_id: str) -> None:
    """Delete a conversation and its messages."""
    if not await service.delete_conversation(conversation_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found.")
