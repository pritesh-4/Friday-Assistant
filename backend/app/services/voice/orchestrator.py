import time
import uuid
from typing import Any

from fastapi import UploadFile

from app.core.logging import get_logger
from app.schemas.chat import ChatRequest
from app.services.chat_service import ChatService
from app.services.streaming_coordinator import StreamingCoordinator
from app.services.voice.transcription_service import TranscriptionService

_log = get_logger("voice_orchestrator")


class VoiceOrchestrator:
    """
    Coordinates the entire backend lifecycle of a voice interaction.
    Orchestrates the transition from audio upload -> STT -> Conversation Pipeline,
    collecting precise latencies and acting as the single entrypoint for the UI.
    """

    def __init__(self):
        self.transcription_service = TranscriptionService()
        self.chat_service = ChatService()
        self.streaming_coordinator = StreamingCoordinator()

    async def stream_conversation(
        self, file: UploadFile, conversation_id: str | None = None
    ):
        """
        Takes an uploaded audio file, transcribes it, yields the transcript,
        then streams the conversation back using Server-Sent Events.
        """
        import json
        import traceback

        request_id = str(uuid.uuid4())
        session_log_prefix = f"[VOICE-STREAM][Req:{request_id[:8]}]"

        start_time = time.time()
        _log.info(
            f"======== STAGE START ========\nStage Name: Orchestrator stream_conversation\nTimestamp: {start_time}\nConversation ID: {conversation_id}\nInput Summary: Starting stream pipeline for UploadFile"
        )

        try:
            # ── 1. Transcription ──────────────────────────────────────────
            _log.info(f"{session_log_prefix} Transcription Started")
            stt_start = time.time()

            stt_result = await self.transcription_service.transcribe(file)
            transcript = stt_result["transcript"]

            stt_latency = time.time() - stt_start
            _log.info(
                f"{session_log_prefix} Transcription Complete (Latency: {stt_latency:.2f}s)"
            )

            if not transcript.strip():
                _log.info(
                    f"{session_log_prefix} Empty transcript. Aborting conversation pipeline."
                )
                yield f"data: {json.dumps({'type': 'done', 'metrics': {'ttft_ms': 0, 'tps': 0.0, 'total_time_ms': int((time.time() - start_time) * 1000)}})}\n\n"
                _log.info(
                    f"======== STAGE END =========\nResult: Success\nElapsed Time: {time.time() - start_time}s\nOutput Summary: Empty transcript"
                )
                return

            # Yield the transcript immediately so the UI can transition state
            yield f"data: {json.dumps({'type': 'transcript', 'text': transcript, 'stt_latency_ms': int(stt_latency * 1000)})}\n\n"

            # ── 2. Conversation Streaming ─────────────────────────────
            _log.info(f"{session_log_prefix} Streaming Coordinator Started")

            chat_request = ChatRequest(
                message=transcript, conversation_id=conversation_id
            )

            async for event in self.streaming_coordinator.stream_chat(chat_request):
                yield event

            _log.info(
                f"======== STAGE END =========\nResult: Success\nElapsed Time: {time.time() - start_time}s\nOutput Summary: Stream completed normally"
            )
        except Exception as e:
            err_msg = f"{type(e).__name__} - {str(e)}"
            _log.error(
                f"======== STAGE END =========\nResult: Error\nElapsed Time: {time.time() - start_time}s\nOutput Summary: Exception caught: {err_msg}"
            )
            _log.error(traceback.format_exc())
            yield f"data: {json.dumps({'type': 'error', 'content': err_msg})}\n\n"

    async def process_conversation(
        self, file: UploadFile, conversation_id: str | None = None
    ) -> dict[str, Any]:
        """
        Takes an uploaded audio file and processes it through STT and the Chat Pipeline.

        Args:
            file: The raw audio upload from the user.
            conversation_id: The active chat session ID, or None if starting a new one.

        Returns:
            A structured dict containing transcript, AI response, latencies, and conversation context.
        """
        request_id = str(uuid.uuid4())
        session_log_prefix = f"[VOICE][Req:{request_id[:8]}]"

        start_time = time.time()
        _log.info(f"{session_log_prefix} Upload Complete")

        # ── 1. Transcription ──────────────────────────────────────────
        _log.info(f"{session_log_prefix} Transcription Started")
        stt_start = time.time()

        stt_result = await self.transcription_service.transcribe(file)
        transcript = stt_result["transcript"]

        stt_latency = time.time() - stt_start
        _log.info(
            f"{session_log_prefix} Transcription Complete (Latency: {stt_latency:.2f}s)"
        )

        if not transcript.strip():
            _log.info(
                f"{session_log_prefix} Empty transcript. Aborting conversation pipeline."
            )
            total_latency = time.time() - start_time
            return {
                "transcript": "",
                "response": "",
                "conversation_id": conversation_id,
                "latency": {
                    "stt": stt_latency,
                    "provider": 0.0,
                    "total": total_latency,
                },
            }

        # ── 2. Conversation Intelligence ─────────────────────────────
        _log.info(f"{session_log_prefix} Conversation Started")
        provider_start = time.time()

        chat_request = ChatRequest(message=transcript, conversation_id=conversation_id)
        chat_response = await self.chat_service.send_message(chat_request)

        provider_latency = time.time() - provider_start
        _log.info(
            f"{session_log_prefix} Response Received (Provider Latency: {provider_latency:.2f}s, Provider: {chat_response.provider})"
        )

        total_latency = time.time() - start_time
        _log.info(
            f"{session_log_prefix} Complete (Total Latency: {total_latency:.2f}s)"
        )

        return {
            "transcript": transcript,
            "response": chat_response.assistant_message.content,
            "conversation_id": chat_response.conversation.id,
            "latency": {
                "stt": stt_latency,
                "provider": provider_latency,
                "total": total_latency,
            },
        }
