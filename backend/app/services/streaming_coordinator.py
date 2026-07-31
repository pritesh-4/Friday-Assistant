"""Conversation orchestration for real-time streaming."""

import base64
import json
from pathlib import Path

from typing import Any

from app.agents.context_builder import ContextBuilder
from app.agents.memory_extractor import MemoryExtractor
from app.agents.router_agent import RouterAgent
from app.db.database import database
from app.memory.memory_manager import memory_manager
from app.schemas.chat import ChatRequest
from app.services.document_parser import DocumentParser
from app.services.memory_service import CognitiveMemoryService
from app.tools.executor import PermissionRequiredError
from app.utils.helpers import generate_uuid, get_utc_now
from app.core.memory import log_memory
from app.core.logging import get_logger
from datetime import datetime, timezone

_log = get_logger("streaming_coordinator")


class StreamingCoordinator:
    """Orchestrates real-time streaming text-chat and memory extraction."""

    def __init__(self) -> None:
        self.memory_service = CognitiveMemoryService()
        self.router_agent = RouterAgent()
        self.context_builder = ContextBuilder()
        from app.services.llm_service import LLMService

        self.memory_extractor = MemoryExtractor(LLMService())

    async def stream_chat(
        self,
        request: ChatRequest,
        prefetched_memories: dict[str, list[dict]] | None = None,
    ):
        """
        Yields SSE formatted strings.
        Event types: 'metadata', 'chunk', 'done', 'error'.
        """
        try:
            yield f"data: {json.dumps({'type': 'status', 'status': 'processing_intent'})}\n\n"
            conversation_id, title = await self._get_or_create_conversation(request)

            # Send initial metadata to UI so it knows the conversation ID
            yield f"data: {json.dumps({'type': 'metadata', 'conversationId': conversation_id, 'title': title})}\n\n"

            structured_content: list[dict[str, Any]] = [
                {"type": "text", "text": request.message.strip()}
            ]
            db_structured_content: list[dict[str, Any]] = [
                {"type": "text", "text": request.message.strip()}
            ]
            has_files = False
            if request.file_ids:
                for file_id in request.file_ids:
                    row = await database.fetch_one(
                        "SELECT * FROM files WHERE id = ?", (file_id,)
                    )
                    if row:
                        has_files = True
                        file_path = Path(row["storage_path"])
                        if row["content_type"].startswith("image/"):
                            with open(file_path, "rb") as f:
                                b64_data = base64.b64encode(f.read()).decode("utf-8")
                            structured_content.append(
                                {
                                    "type": "image_url",
                                    "image_url": {
                                        "url": f"data:{row['content_type']};base64,{b64_data}"
                                    },
                                }
                            )
                            db_structured_content.append(
                                {
                                    "type": "text",
                                    "text": f"\\n\\n[Attached Image: {row['name']}]",
                                }
                            )
                        else:
                            text = DocumentParser.parse(file_path, row["content_type"])
                            if text:
                                structured_content.append(
                                    {
                                        "type": "text",
                                        "text": f"\\n\\n[Attached File: {row['name']}]\\n{text}",
                                    }
                                )
                                db_structured_content.append(
                                    {
                                        "type": "text",
                                        "text": f"\\n\\n[Attached File: {row['name']}]\\n{text}",
                                    }
                                )

            content_for_db = request.message.strip()
            if has_files:
                content_for_db = json.dumps(db_structured_content)

            # Persist user message
            await self._create_message(conversation_id, "user", content_for_db)

            # Cognitive gateway: Process message via Intent Engine
            from app.intent.engine import IntentEngine

            # Stage 5: Intent Engine initialized
            _log.info(
                f"[TRACE] [Stage 5] [{datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')}] Initializing Intent Engine..."
            )
            intent_engine = IntentEngine()
            intent_res = await intent_engine.process(request.message, conversation_id)
            _log.info(
                f"[TRACE] [Stage 5] [{datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')}] Intent Engine processed successfully"
            )

            if intent_res.clarification_required and intent_res.clarification_prompt:
                yield f"data: {json.dumps({'type': 'chunk', 'content': intent_res.clarification_prompt})}\n\n"
                await self._create_message(
                    conversation_id, "assistant", intent_res.clarification_prompt
                )
                memory_manager.append_message(
                    conversation_id, "assistant", intent_res.clarification_prompt
                )
                yield f"data: {json.dumps({'type': 'done', 'metrics': {'latency_ms': 0}})}\n\n"
                return

            # Intercept explicit memory commands (forget, correct, update)
            is_memory_command = any(word in request.message.lower() for word in ["forget", "update", "correct", "incorrect", "wrong", "delete", "remove"])
            if is_memory_command:
                command_response = await self.memory_service.process_interaction(
                    request.message, conversation_id
                )
                if command_response:
                    yield f"data: {json.dumps({'type': 'chunk', 'content': command_response})}\n\n"
                    await self._create_message(conversation_id, "assistant", command_response)
                    memory_manager.append_message(conversation_id, "assistant", command_response)
                    yield f"data: {json.dumps({'type': 'done', 'metrics': {'latency_ms': 0}})}\n\n"
                    return

            yield f"data: {json.dumps({'type': 'status', 'status': 'accessing_memory'})}\n\n"

            # Stage 6: Memory initialized
            _log.info(
                f"[TRACE] [Stage 6] [{datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')}] Accessing and initializing Memory Context for conversation: {conversation_id}..."
            )
            ctx = memory_manager.get_context(conversation_id)
            _log.info(
                f"[TRACE] [Stage 6] [{datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')}] Memory Context initialized successfully"
            )

            if not ctx.messages:
                # Load history if memory context is empty
                log_memory("Before DB history fetch")
                rows = await database.fetch_all(
                    "SELECT * FROM (SELECT * FROM messages WHERE conversation_id = ? ORDER BY created_at DESC LIMIT 16) ORDER BY created_at ASC",
                    (conversation_id,),
                )
                for row in rows:
                    content = row["content"]
                    try:
                        parsed = json.loads(content)
                        if isinstance(parsed, list):
                            ctx.messages.append(
                                {"role": row["role"], "content": parsed}
                            )
                        else:
                            ctx.messages.append(
                                {"role": row["role"], "content": content}
                            )
                    except Exception:
                        ctx.messages.append({"role": row["role"], "content": content})
                log_memory("After DB history fetch")
            else:
                memory_manager.append_message(
                    conversation_id,
                    "user",
                    structured_content if has_files else request.message.strip(),
                )

            # Retrieve long-term memories
            if prefetched_memories is not None:
                memories = prefetched_memories
                _log.info(
                    f"[TRACE] [Stage 6] [{datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')}] "
                    "Bypassed memory retrieval using cached prefetch result"
                )
            else:
                memories = await self.memory_service.retrieve_relevant_memories(
                    request.message, limit_per_type=2
                )
            messages = self.context_builder.build_messages(ctx.messages, memories)

            # Stream response
            import time

            start_time = time.time()
            ttft = 0.0
            total_tokens = 0

            full_response = ""
            sentence_buffer = ""

            punctuation_marks = {".", "?", "!", "\n"}

            try:
                yield f"data: {json.dumps({'type': 'status', 'status': 'reasoning'})}\n\n"
                log_memory("Before router stream")

                # Stage 9: Provider called
                _log.info(
                    f"[TRACE] [Stage 9] [{datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')}] LLM Provider stream router called"
                )
                async for chunk in self.router_agent.route_and_stream(
                    messages, request.approved_permissions
                ):
                    if ttft == 0.0:
                        yield f"data: {json.dumps({'type': 'status', 'status': 'building_response'})}\n\n"
                        ttft = time.time() - start_time

                    total_tokens += 1
                    full_response += chunk
                    sentence_buffer += chunk

                    # Emit raw chunk for UI
                    yield f"data: {json.dumps({'type': 'chunk', 'content': chunk})}\n\n"

                    # Intelligent sentence buffering for TTS readiness
                    if any(p in chunk for p in punctuation_marks):
                        # Find the last punctuation mark to split correctly
                        last_punc_idx = max(
                            sentence_buffer.rfind(p) for p in punctuation_marks
                        )
                        if last_punc_idx != -1:
                            complete_sentence = sentence_buffer[
                                : last_punc_idx + 1
                            ].strip()
                            if complete_sentence:
                                yield f"data: {json.dumps({'type': 'sentence', 'content': complete_sentence})}\n\n"
                            sentence_buffer = sentence_buffer[last_punc_idx + 1 :]
            except PermissionRequiredError as e:
                # Yield a special permission request event
                req_data = {
                    "type": "permission_request",
                    "tool": e.tool_name,
                    "scope": e.scope,
                    "kwargs": e.kwargs,
                    "justification": f"F.R.I.D.A.Y. needs permission to execute '{e.tool_name}' ({e.scope}).",
                }
                yield f"data: {json.dumps(req_data)}\n\n"
                # Terminate the stream here. The frontend is expected to prompt the user
                # and then automatically re-submit the request with `approved_permissions` populated.
                return

            log_memory("After router stream")

            if sentence_buffer.strip():
                yield f"data: {json.dumps({'type': 'sentence', 'content': sentence_buffer.strip()})}\n\n"

            total_time = time.time() - start_time
            tps = total_tokens / total_time if total_time > 0 else 0.0

            # Finish stream with metrics
            metrics = {
                "ttft_ms": round(ttft * 1000),
                "tps": round(tps, 1),
                "total_time_ms": round(total_time * 1000),
            }
            # Stage 10: Response sent
            _log.info(
                f"[TRACE] [Stage 10] [{datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')}] LLM Response stream completed and sent to client"
            )
            yield f"data: {json.dumps({'type': 'done', 'metrics': metrics})}\n\n"

            # Background tasks post-stream
            await self._create_message(conversation_id, "assistant", full_response)
            memory_manager.append_message(conversation_id, "assistant", full_response)

            if not is_memory_command:
                try:
                    await self.memory_service.process_interaction(request.message, conversation_id)
                except Exception as e:
                    _log.error(f"Failed to process memory extraction: {e}")

        except Exception as e:
            import traceback

            traceback.print_exc()
            yield f"data: {json.dumps({'type': 'error', 'content': str(e)})}\n\n"

    async def _get_or_create_conversation(
        self, request: ChatRequest
    ) -> tuple[str, str]:
        if request.conversation_id:
            row = await database.fetch_one(
                "SELECT * FROM conversations WHERE id = ?", (request.conversation_id,)
            )
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

    async def _create_message(
        self, conversation_id: str, role: str, content: str
    ) -> str:
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
