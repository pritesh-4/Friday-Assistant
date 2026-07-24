"""Conversation orchestration for real-time streaming."""

import base64
import json
from pathlib import Path

from app.agents.context_builder import ContextBuilder
from app.agents.memory_agent import MemoryAgent
from app.agents.router_agent import RouterAgent
from app.db.database import database
from app.memory.memory_manager import memory_manager
from app.schemas.chat import ChatRequest
from app.services.document_parser import DocumentParser
from app.services.memory_service import MemoryService
from app.utils.helpers import generate_uuid, get_utc_now


class StreamingCoordinator:
    """Orchestrates real-time streaming text-chat and memory extraction."""

    def __init__(self) -> None:
        self.memory_service = MemoryService()
        self.router_agent = RouterAgent()
        self.context_builder = ContextBuilder()
        self.memory_agent = MemoryAgent()

    async def stream_chat(self, request: ChatRequest):
        """
        Yields SSE formatted strings.
        Event types: 'metadata', 'chunk', 'done', 'error'.
        """
        try:
            conversation_id, title = await self._get_or_create_conversation(request)
            
            # Send initial metadata to UI so it knows the conversation ID
            yield f'data: {json.dumps({"type": "metadata", "conversationId": conversation_id, "title": title})}\n\n'

            structured_content = [{"type": "text", "text": request.message.strip()}]
            has_files = False
            if request.file_ids:
                for file_id in request.file_ids:
                    row = await database.fetch_one("SELECT * FROM files WHERE id = ?", (file_id,))
                    if row:
                        has_files = True
                        file_path = Path(row["storage_path"])
                        if row["content_type"].startswith("image/"):
                            with open(file_path, "rb") as f:
                                b64_data = base64.b64encode(f.read()).decode("utf-8")
                            structured_content.append({
                                "type": "image_url",
                                "image_url": {"url": f"data:{row['content_type']};base64,{b64_data}"}
                            })
                        else:
                            text = DocumentParser.parse(file_path, row["content_type"])
                            if text:
                                structured_content.append({
                                    "type": "text",
                                    "text": f"\\n\\n[Attached File: {row['name']}]\\n{text}"
                                })

            content_for_db = request.message.strip()
            if has_files:
                content_for_db = json.dumps(structured_content)

            # Persist user message
            await self._create_message(conversation_id, "user", content_for_db)
            
            ctx = memory_manager.get_context(conversation_id)
            
            if not ctx.messages:
                # Load history if memory context is empty
                rows = await database.fetch_all(
                    "SELECT * FROM (SELECT * FROM messages WHERE conversation_id = ? ORDER BY created_at DESC LIMIT 16) ORDER BY created_at ASC",
                    (conversation_id,)
                )
                for row in rows:
                    content = row["content"]
                    try:
                        parsed = json.loads(content)
                        if isinstance(parsed, list):
                            ctx.messages.append({"role": row["role"], "content": parsed})
                        else:
                            ctx.messages.append({"role": row["role"], "content": content})
                    except Exception:
                        ctx.messages.append({"role": row["role"], "content": content})
            else:
                memory_manager.append_message(conversation_id, "user", structured_content if has_files else request.message.strip())

            # Retrieve long-term memories
            memories = await self.memory_service.retrieve_memories(request.message, limit=5)
            messages = self.context_builder.build_messages(ctx.messages, memories)

            # Stream response
            full_response = ""
            async for chunk in self.router_agent.route_and_stream(messages):
                full_response += chunk
                yield f'data: {json.dumps({"type": "chunk", "content": chunk})}\n\n'
                
            # Finish stream
            yield f'data: {json.dumps({"type": "done"})}\n\n'

            # Background tasks post-stream
            await self._create_message(conversation_id, "assistant", full_response)
            memory_manager.append_message(conversation_id, "assistant", full_response)
            
            extracted = self.memory_agent.extract_memories(request.message)
            for mem in extracted:
                await self.memory_service.store_memory(mem)

        except Exception as e:
            import traceback
            traceback.print_exc()
            yield f'data: {json.dumps({"type": "error", "content": str(e)})}\n\n'

    async def _get_or_create_conversation(self, request: ChatRequest) -> tuple[str, str]:
        if request.conversation_id:
            row = await database.fetch_one("SELECT * FROM conversations WHERE id = ?", (request.conversation_id,))
            if row:
                return row["id"], row["title"]

        conversation_id = generate_uuid()
        now = get_utc_now().isoformat()
        title = request.message.strip().replace("\n", " ")[:60]
        await database.execute(
            "INSERT INTO conversations (id, title, created_at, updated_at) VALUES (?, ?, ?, ?)",
            (conversation_id, title, now, now),
        )
        return conversation_id, title

    async def _create_message(self, conversation_id: str, role: str, content: str) -> str:
        message_id = generate_uuid()
        now = get_utc_now().isoformat()
        await database.execute(
            "INSERT INTO messages (id, conversation_id, role, content, created_at) VALUES (?, ?, ?, ?, ?)",
            (message_id, conversation_id, role, content, now),
        )
        await database.execute(
            "UPDATE conversations SET last_message = ?, updated_at = ? WHERE id = ?",
            (content, now, conversation_id),
        )
        return message_id
