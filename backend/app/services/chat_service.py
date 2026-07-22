"""Conversation orchestration: persistence, context retrieval, and LLM generation."""

from fastapi import HTTPException, status

from app.agents.context_builder import ContextBuilder
from app.agents.memory_agent import MemoryAgent
from app.agents.router_agent import RouterAgent
from app.db.database import database
from app.memory.memory_manager import memory_manager
from app.schemas.chat import ChatRequest, ChatResponse, Conversation, Message
from app.services.memory_service import MemoryService
from app.services.providers.base import LLMProviderError
from app.utils.helpers import generate_uuid, get_utc_now


class ChatService:
    """Implement the smallest reliable text-chat vertical slice."""

    def __init__(self) -> None:
        self.memory_service = MemoryService()
        self.router_agent = RouterAgent()
        self.context_builder = ContextBuilder()
        self.memory_agent = MemoryAgent()

    async def list_conversations(self) -> list[Conversation]:
        rows = await database.fetch_all("SELECT * FROM conversations ORDER BY updated_at DESC")
        return [Conversation.model_validate(row) for row in rows]

    async def get_messages(self, conversation_id: str, limit: int = 100) -> list[Message]:
        await self._get_conversation(conversation_id)
        limit = max(1, min(limit, 100))
        rows = await database.fetch_all(
            """
            SELECT * FROM (
                SELECT * FROM messages WHERE conversation_id = ?
                ORDER BY created_at DESC LIMIT ?
            ) ORDER BY created_at ASC
            """,
            (conversation_id, limit),
        )
        return [Message.model_validate(row) for row in rows]

    async def send_message(self, request: ChatRequest) -> ChatResponse:
        conversation = await self._get_or_create_conversation(request)
        user_message = await self._create_message(
            conversation.id, "user", request.message.strip()
        )
        
        session_id = conversation.id
        ctx = memory_manager.get_context(session_id)
        
        # 1. Manage Session Memory
        if not ctx.messages:
            history = await self.get_messages(conversation.id, limit=16)
            for msg in history:
                ctx.messages.append({"role": msg.role, "content": msg.content})
        else:
            memory_manager.append_message(session_id, "user", request.message.strip())

        # 2. Retrieve Long-Term Memories
        memories = await self.memory_service.retrieve_memories(request.message, limit=5)

        # 3. Build Context Prompt
        messages = self.context_builder.build_messages(ctx.messages, memories)

        # 4. Route and Execute Provider
        try:
            llm_result = await self.router_agent.route_and_execute(messages)
        except LLMProviderError as exc:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc)
            ) from exc

        # 5. Save Response and update session
        assistant_message = await self._create_message(
            conversation.id, "assistant", llm_result.content
        )
        memory_manager.append_message(session_id, "assistant", llm_result.content)
        
        # 6. Extract and Store new Memories
        extracted = self.memory_agent.extract_memories(request.message)
        for mem in extracted:
            await self.memory_service.store_memory(mem)

        conversation = await self._get_conversation(conversation.id)
        return ChatResponse(
            conversation=conversation,
            user_message=user_message,
            assistant_message=assistant_message,
            provider=llm_result.provider,
            model=llm_result.model,
            latency_ms=llm_result.latency_ms,
            finish_reason=llm_result.finish_reason,
            memories_used=len(memories),
        )

    async def delete_conversation(self, conversation_id: str) -> bool:
        memory_manager.clear_context(conversation_id)
        return bool(
            await database.execute("DELETE FROM conversations WHERE id = ?", (conversation_id,))
        )

    async def _get_or_create_conversation(self, request: ChatRequest) -> Conversation:
        if request.conversation_id:
            return await self._get_conversation(request.conversation_id)

        conversation_id = generate_uuid()
        now = get_utc_now().isoformat()
        title = request.message.strip().replace("\n", " ")[:60]
        await database.execute(
            """
            INSERT INTO conversations (id, title, created_at, updated_at)
            VALUES (?, ?, ?, ?)
            """,
            (conversation_id, title, now, now),
        )
        return Conversation(
            id=conversation_id,
            title=title,
            created_at=now,
            updated_at=now,
        )

    async def _get_conversation(self, conversation_id: str) -> Conversation:
        row = await database.fetch_one("SELECT * FROM conversations WHERE id = ?", (conversation_id,))
        if row is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found."
            )
        return Conversation.model_validate(row)

    async def _create_message(
        self, conversation_id: str, role: str, content: str
    ) -> Message:
        message_id = generate_uuid()
        now = get_utc_now().isoformat()
        await database.execute(
            """
            INSERT INTO messages (id, conversation_id, role, content, created_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (message_id, conversation_id, role, content, now),
        )
        await database.execute(
            "UPDATE conversations SET last_message = ?, updated_at = ? WHERE id = ?",
            (content, now, conversation_id),
        )
        return Message(
            id=message_id,
            conversation_id=conversation_id,
            role=role,
            content=content,
            created_at=now,
        )
