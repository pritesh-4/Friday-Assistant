"""Chat route — conversation management and message sending."""

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.api.dependencies import get_chat_service
from app.schemas.chat import ChatRequest, ChatResponse, Conversation, Message
from app.services.chat_service import ChatService

router = APIRouter(tags=["chat"])


@router.get("", response_model=list[Conversation])
async def list_conversations(
    service: ChatService = Depends(get_chat_service),
) -> list[Conversation]:
    """Return local conversation summaries, newest first."""
    return await service.list_conversations()


@router.post("", response_model=ChatResponse, status_code=status.HTTP_201_CREATED)
async def send_chat_message(
    request: ChatRequest,
    service: ChatService = Depends(get_chat_service),
) -> ChatResponse:
    """Persist a user message and return the generated assistant reply."""
    return await service.send_message(request)


@router.get("/{conversation_id}/messages", response_model=list[Message])
async def get_conversation_messages(
    conversation_id: str,
    limit: int = Query(default=100, ge=1, le=100),
    service: ChatService = Depends(get_chat_service),
) -> list[Message]:
    """Read one conversation's bounded, chronologically ordered history."""
    return await service.get_messages(conversation_id, limit)


@router.delete("/{conversation_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_conversation(
    conversation_id: str,
    service: ChatService = Depends(get_chat_service),
) -> None:
    """Delete a conversation and all its messages."""
    if not await service.delete_conversation(conversation_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found.")
