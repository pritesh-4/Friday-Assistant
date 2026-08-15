"""Voice routes — server-side speech-to-text and text-to-speech.

Endpoints:
  GET  /voice          — Capability status probe.
  GET  /voice/health   — Detailed STT/TTS diagnostic health check.
  POST /voice/upload   — Upload raw audio blob to temporary storage.
  POST /voice/transcribe — Transcribe audio using OpenRouter Whisper / Faster-Whisper STT.
  POST /voice/speak    — Synthesize text to MP3 audio using OpenRouter Fish Audio TTS.

All endpoints check VOICE_ENABLED at runtime and return 503 with a clear
message if voice features are disabled.
"""

import asyncio
import logging
import time
from typing import Any

from fastapi import (
    APIRouter,
    Depends,
    File,
    Form,
    HTTPException,
    Request,
    Response,
    UploadFile,
    WebSocket,
    WebSocketDisconnect,
    status,
)
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, field_validator

from app.api.dependencies import (
    get_speech_service,
    get_transcription_service,
    get_voice_service,
    get_voice_orchestrator,
    get_streaming_coordinator,
)
from app.core.config import settings
from app.core.rate_limit import limiter
from app.schemas.voice import TranscriptionResult
from app.services.voice.speech_service import SpeechService
from app.services.voice.transcription_service import TranscriptionService
from app.services.voice.orchestrator import VoiceOrchestrator
from app.services.voice_service import VoiceService
from app.ai.whisper.engine import WhisperEngine
from app.core.memory import log_memory

_log = logging.getLogger(__name__)
router = APIRouter(tags=["voice"])

# Maximum characters allowed for TTS synthesis.
_TTS_MAX_CHARS = 3_000

_VOICE_DISABLED_DETAIL = (
    "Voice features are disabled on this deployment. "
    "Set VOICE_ENABLED=true and install requirements-voice.txt to enable STT and TTS."
)


def _require_voice() -> None:
    """Raise HTTP 503 if VOICE_ENABLED is false."""
    if not settings.voice_enabled:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=_VOICE_DISABLED_DETAIL,
        )


@router.get("", summary="Voice capability status")
async def get_voice_status(
    speech_service: SpeechService = Depends(get_speech_service),
) -> dict[str, Any]:
    """
    Return the current availability of server-side voice features.
    This endpoint always responds — it does not raise 503 even when voice is disabled,
    so the frontend can check capability without error handling.
    """
    if not settings.voice_enabled:
        return {
            "available": False,
            "stt": None,
            "tts": None,
            "detail": _VOICE_DISABLED_DETAIL,
            "browser_fallback": True,
        }

    whisper_engine = WhisperEngine()
    tts_info = speech_service.manager.get_active_provider_info()

    return {
        "available": True,
        "stt": "faster-whisper" if whisper_engine.is_loaded else "unavailable",
        "tts": tts_info["active_provider"] if tts_info["available"] else "unavailable",
        "tts_info": tts_info,
        "detail": "Server-side STT and TTS status reported above.",
        "browser_fallback": not (whisper_engine.is_loaded and tts_info["available"]),
    }


@router.get("/health", summary="Detailed Voice Diagnostics")
async def get_voice_health() -> dict[str, Any]:
    """
    Returns detailed system readiness for the voice subsystem.
    Matches the schema specifically requested for full observability.
    """
    import shutil

    ffmpeg_installed = shutil.which("ffmpeg") is not None

    engine = WhisperEngine()

    faster_whisper_installed = False
    try:
        import faster_whisper  # noqa: F401

        faster_whisper_installed = True
    except ImportError:
        pass

    ctranslate2_installed = False
    try:
        import ctranslate2  # noqa: F401

        ctranslate2_installed = True
    except ImportError:
        pass

    av_installed = False
    try:
        import av  # noqa: F401

        av_installed = True
    except ImportError:
        pass

    tokenizers_installed = False
    try:
        import tokenizers  # noqa: F401

        tokenizers_installed = True
    except ImportError:
        pass

    ready = settings.voice_enabled and faster_whisper_installed and ffmpeg_installed

    return {
        "voice_enabled": settings.voice_enabled,
        "whisper_loaded": engine.is_loaded,
        "model": engine.model_name,
        "device": engine.device,
        "compute_type": engine.compute_type,
        "ffmpeg": ffmpeg_installed,
        "dependencies": {
            "faster_whisper": faster_whisper_installed,
            "ctranslate2": ctranslate2_installed,
            "av": av_installed,
            "tokenizers": tokenizers_installed,
        },
        "ready": ready,
    }


@router.post("/upload", summary="Upload a voice recording")
@limiter.limit("20/minute")
async def upload_voice(
    request: Request,
    file: UploadFile = File(...),
    service: VoiceService = Depends(get_voice_service),
) -> dict:
    """
    Upload a voice recording to the temporary storage directory.
    Validates MIME type, file size, and handles saving securely.
    """
    _require_voice()
    log_memory("Before upload_audio")
    res = await service.upload_audio(file)
    log_memory("After upload_audio")
    return res


@router.post("/orchestrate", summary="Process full voice conversation")
@limiter.limit("20/minute")
async def orchestrate_voice(
    request: Request,
    file: UploadFile = File(...),
    conversation_id: str | None = None,
    orchestrator: VoiceOrchestrator = Depends(get_voice_orchestrator),
) -> dict[str, Any]:
    """
    Master endpoint for the complete Voice orchestration lifecycle.
    Handles upload -> STT -> LLM Chat -> returning text synchronously.
    """
    _require_voice()

    _log.info("[VOICE] START POST /voice/orchestrate")
    result = await orchestrator.process_conversation(file, conversation_id)
    _log.info("[VOICE] SUCCESS POST /voice/orchestrate")

    return result


@router.post(
    "/orchestrate/stream",
    summary="Stream full voice conversation",
    status_code=status.HTTP_200_OK,
)
@limiter.limit("20/minute")
async def orchestrate_voice_stream(
    request: Request,
    file: UploadFile = File(...),
    conversation_id: str | None = Form(None),
    orchestrator: VoiceOrchestrator = Depends(get_voice_orchestrator),
) -> StreamingResponse:
    """
    Master endpoint for real-time Voice orchestration lifecycle.
    Handles upload -> STT -> LLM Chat -> returning SSE stream to frontend.
    """
    _require_voice()

    _log.info(
        f"======== STAGE START ========\nStage Name: Backend POST /orchestrate/stream\nTimestamp: {time.time()}\nConversation ID: {conversation_id}\nInput Summary: Received file {file.filename}"
    )

    # MINIMAL FIX: FastAPI closes `file` automatically as soon as this function returns the StreamingResponse.
    # To prevent I/O operations on a closed file inside the generator, we load it into memory.
    content = await file.read()
    from io import BytesIO

    safe_file = UploadFile(
        file=BytesIO(content), filename=file.filename, headers=file.headers
    )

    log_memory("After loading UploadFile to memory")

    # Return response. The generator will run after this returns.
    return StreamingResponse(
        orchestrator.stream_conversation(safe_file, conversation_id),
        media_type="text/event-stream",
    )


@router.post(
    "/transcribe",
    summary="Transcribe audio to text",
    response_model=TranscriptionResult,
)
async def transcribe_voice(
    file: UploadFile = File(...),
    transcription_service: TranscriptionService = Depends(get_transcription_service),
) -> TranscriptionResult:
    """
    Transcribe an audio file to text using the Faster-Whisper STT provider.
    The uploaded audio file is handled completely within the service and deleted afterwards.
    """
    _require_voice()

    import time

    start_time = time.time()
    _log.info("[VOICE] START POST /voice/transcribe")

    result = await transcription_service.transcribe(file)

    elapsed = time.time() - start_time
    _log.info(f"[VOICE] SUCCESS POST /voice/transcribe in {elapsed:.2f}s")
    return TranscriptionResult(**result)


@router.post("/debug", summary="Debug complete audio pipeline")
async def debug_voice(
    file: UploadFile = File(...),
    voice_service: VoiceService = Depends(get_voice_service),
    transcription_service: TranscriptionService = Depends(get_transcription_service),
) -> dict[str, Any]:
    """
    Debug the audio pipeline from upload to transcription.
    Returns FFprobe, FFmpeg, and Whisper results.
    """
    _require_voice()

    response = {
        "uploaded_size": 0,
        "detected_mime": file.content_type,
        "detected_container": file.filename.split(".")[-1]
        if file.filename
        else "unknown",
        "codec": "unknown",
        "ffprobe_output": "",
        "ffmpeg_output": "",
        "transcription_result": None,
    }

    try:
        # Step 1: Upload (this runs ffprobe and ffmpeg internally via VoiceService)
        upload_result = await voice_service.upload_audio(file)

        response["uploaded_size"] = upload_result["size"]
        response["ffprobe_output"] = upload_result.get("ffprobe_output", "")
        response["ffmpeg_output"] = upload_result.get("ffmpeg_output", "")

        file_path = voice_service.upload_dir / upload_result["filename"]

        # Step 2: Transcribe via Engine directly, since file is already processed
        try:
            result = await transcription_service.engine.transcribe(str(file_path))
            response["transcription_result"] = result
        finally:
            try:
                file_path.unlink(missing_ok=True)
            except Exception:
                pass

    except HTTPException as e:
        response["error"] = e.detail
    except Exception as e:
        response["error"] = str(e)

    return response


class SpeakRequest(BaseModel):
    text: str

    @field_validator("text")
    @classmethod
    def text_must_not_be_too_long(cls, v: str) -> str:
        if len(v) > _TTS_MAX_CHARS:
            raise ValueError(
                f"Text too long for TTS synthesis ({len(v)} chars). "
                f"Maximum is {_TTS_MAX_CHARS} characters."
            )
        return v


@router.post("/speak", summary="Synthesize text to speech")
async def speak_voice(
    request: SpeakRequest,
    speech_service: SpeechService = Depends(get_speech_service),
) -> Response:
    """
    Convert text to an audio stream (MP3 or WAV) using OpenRouter Fish Audio TTS.
    Returns binary audio (audio/mpeg or audio/wav). Maximum input is 3,000 characters.
    """
    _require_voice()

    import time

    start_time = time.time()
    _log.info("[VOICE] START POST /voice/speak")

    try:
        (
            audio_bytes,
            media_type,
            provider_name,
        ) = await speech_service.synthesize_with_metadata(request.text)
        elapsed = time.time() - start_time
        _log.info(
            f"[VOICE] SUCCESS POST /voice/speak via [{provider_name}] in {elapsed:.2f}s -> {len(audio_bytes)} bytes ({media_type})"
        )
        return Response(content=audio_bytes, media_type=media_type)
    except ValueError as exc:
        _log.error(f"[VOICE] FAILURE POST /voice/speak - ValueError: {exc}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    except RuntimeError as exc:
        _log.error(f"[VOICE] FAILURE POST /voice/speak - RuntimeError: {exc}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)
        )
    except Exception as exc:
        _log.error(f"[VOICE] FAILURE POST /voice/speak - Exception: {exc}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"TTS synthesis failed: {exc!s}",
        )


@router.post("/speak/stream", summary="Stream synthesized speech chunks")
async def speak_voice_stream(
    request: SpeakRequest,
    speech_service: SpeechService = Depends(get_speech_service),
) -> StreamingResponse:
    """
    Convert text to an audio stream using OpenRouter Fish Audio TTS,
    yielding audio chunks as they arrive from the provider.
    """
    _require_voice()

    try:
        audio_gen, media_type, provider_name = await speech_service.stream_synthesize(
            request.text
        )
        _log.info(f"[VOICE] START POST /voice/speak/stream via [{provider_name}]")
        return StreamingResponse(audio_gen, media_type=media_type)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"TTS stream synthesis failed: {exc!s}",
        )


class VoiceSessionState:
    """Connection-scoped state tracker for full-duplex WebSocket conversations."""

    def __init__(self):
        self.audio_chunks = []
        self.active_conversation_id = None
        self.interrupted = False
        self.stop_event = asyncio.Event()
        self.lock = asyncio.Lock()
        self.prefetched_memories = None
        self.active_generation_task = None


@router.websocket("/stream")
async def websocket_voice_stream(
    websocket: WebSocket,
    transcription_service: TranscriptionService = Depends(get_transcription_service),
    streaming_coordinator=Depends(get_streaming_coordinator),
):
    """
    Full-duplex WebSocket endpoint for real-time conversational voice mode.
    Runs concurrent loops for audio streaming, speculative rolling speech-to-text,
    background memory prefetching, and LLM text generation with barge-in support.
    """
    import json
    import numpy as np
    from datetime import datetime, timezone
    from app.schemas.chat import ChatRequest
    from app.intent.engine import IntentEngine
    from app.intent.utils import match_heuristics
    from app.api.dependencies import get_memory_service

    # Stage 1 & 2: Connection request received
    _log.info(
        f"[TRACE] [Stage 1 & 2] [{datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')}] WebSocket connection request received by server"
    )

    # Stage 3: Accept connection
    _log.info(
        f"[TRACE] [Stage 3] [{datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')}] Initiating websocket.accept()..."
    )
    await websocket.accept()
    _log.info(
        f"[TRACE] [Stage 3] [{datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')}] websocket.accept() complete"
    )

    # Stage 4: Authentication
    if settings.secret_key:
        client_token = websocket.query_params.get("token", "")
        if client_token != settings.secret_key:
            _log.warning(
                f"[TRACE] [Stage 4] [{datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')}] "
                "Authentication FAILED — invalid or missing token. Closing connection (4003)."
            )
            await websocket.close(code=4003, reason="Unauthorized")
            return
        _log.info(
            f"[TRACE] [Stage 4] [{datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')}] "
            "Authentication passed (token validated)."
        )
    else:
        _log.info(
            f"[TRACE] [Stage 4] [{datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')}] "
            "Authentication skipped (SECRET_KEY not configured — open MVP mode)."
        )

    session_state = VoiceSessionState()
    intent_engine = IntentEngine()
    memory_service = get_memory_service()

    # Define the reader loop (reads incoming packages from the client)
    async def reader_loop():
        first_msg = True
        try:
            while True:
                message = await websocket.receive()
                if first_msg:
                    _log.info(
                        f"[TRACE] [Stage 7] [{datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')}] First message received from client"
                    )
                    first_msg = False

                if "bytes" in message:
                    data = message["bytes"]
                    if len(data) > 0:
                        chunk = (
                            np.frombuffer(data, dtype=np.int16).astype(np.float32)
                            / 32768.0
                        )
                        async with session_state.lock:
                            session_state.audio_chunks.append(chunk)

                elif "text" in message:
                    command = json.loads(message["text"])
                    cmd_type = command.get("type")

                    if cmd_type == "start":
                        async with session_state.lock:
                            session_state.active_conversation_id = command.get(
                                "conversation_id"
                            )
                            session_state.audio_chunks = []
                            session_state.prefetched_memories = None
                            session_state.interrupted = False
                        _log.info(
                            f"[VOICE-WS] Session started for conversation: {session_state.active_conversation_id}"
                        )
                        await websocket.send_json({"type": "session_started"})

                    elif cmd_type == "stop":
                        _log.info("[VOICE-WS] Stop frame received. Finalizing turn...")
                        session_state.stop_event.set()

                    elif cmd_type == "interrupt":
                        _log.info(
                            "[VOICE-WS] Interrupt frame received (barge-in requested)."
                        )
                        session_state.interrupted = True
                        if (
                            session_state.active_generation_task
                            and not session_state.active_generation_task.done()
                        ):
                            _log.info(
                                "[VOICE-WS] Canceling current active response generation task..."
                            )
                            session_state.active_generation_task.cancel()

        except (WebSocketDisconnect, RuntimeError):
            _log.info("[VOICE-WS] Client disconnected from reader loop.")
        except Exception as e:
            _log.error(f"[VOICE-WS] Error in reader loop: {e}", exc_info=True)
            raise

    # Define speculative rolling STT + Memory prefetch loop
    async def rolling_stt_loop():
        last_transcribed_len = 0
        while True:
            await asyncio.sleep(0.8)
            # Skip rolling STT if we are processing a final turn or if generation is active
            if (
                session_state.stop_event.is_set()
                or session_state.active_generation_task
            ):
                continue

            async with session_state.lock:
                chunks_count = len(session_state.audio_chunks)
                if chunks_count == last_transcribed_len:
                    continue
                audio_data = list(session_state.audio_chunks)
                last_transcribed_len = chunks_count

            if not audio_data:
                continue

            try:
                full_audio = np.concatenate(audio_data)
                # Call transcription_service.transcribe_array non-blockingly
                stt_result = await transcription_service.transcribe_array(full_audio)
                transcript = stt_result["transcript"]

                if transcript.strip():
                    # Send partial transcript to UI
                    await websocket.send_json(
                        {"type": "transcript", "text": transcript, "final": False}
                    )

                    # speculatively run heuristics to find intent and pre-fetch memories
                    cleaned_message = intent_engine.gateway.validate_and_preprocess(
                        transcript
                    )
                    heuristic_res = match_heuristics(cleaned_message)

                    # If heuristics match (high confidence) or query has at least 3 words, prefetch
                    if heuristic_res or len(transcript.split()) >= 3:
                        session_state.prefetched_memories = (
                            await memory_service.retrieve_relevant_memories(
                                transcript, limit_per_type=2
                            )
                        )
                        _log.info(
                            f"[VOICE-WS] Speculatively prefetched memory context for: '{transcript[:30]}...'"
                        )
            except Exception as e:
                _log.warning(f"[VOICE-WS] Speculative rolling STT error: {e}")

    # Define the writer/processor loop
    async def writer_loop():
        while True:
            await session_state.stop_event.wait()
            session_state.stop_event.clear()

            # Set interrupted flag to false for the new generation run
            session_state.interrupted = False

            # Create non-blocking generation task
            session_state.active_generation_task = asyncio.create_task(
                process_turn_generation()
            )
            try:
                await session_state.active_generation_task
            except asyncio.CancelledError:
                _log.info(
                    "[VOICE-WS] Generation task was cancelled (barge-in interruption succeeded)."
                )
                await websocket.send_json({"type": "interrupted"})
            except Exception as exc:
                _log.error(f"[VOICE-WS] Generation task error: {exc}", exc_info=True)
                await websocket.send_json({"type": "error", "message": str(exc)})
            finally:
                session_state.active_generation_task = None

    async def process_turn_generation():
        import uuid

        turn_id = f"turn_{uuid.uuid4().hex[:12]}"
        turn_start_time = time.time()

        async with session_state.lock:
            if not session_state.audio_chunks:
                await websocket.send_json(
                    {"type": "transcript", "text": "", "final": True}
                )
                await websocket.send_json({"type": "done", "turn_id": turn_id})
                return
            full_audio = np.concatenate(session_state.audio_chunks)
            session_state.audio_chunks = []

        await websocket.send_json(
            {"type": "status", "state": "transcribing", "turn_id": turn_id}
        )

        # Stage 8: Transcription starts
        _log.info(
            f"[TRACE] [Stage 8] [{datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')}] Final transcription starts (turn_id: {turn_id})"
        )
        stt_start_time = time.time()
        stt_result = await transcription_service.transcribe_array(full_audio)
        stt_latency_ms = round((time.time() - stt_start_time) * 1000)
        transcript = stt_result["transcript"]
        stt_provider = stt_result.get("provider", "faster_whisper")

        _log.info(
            f"[TRACE] [Stage 8] [{datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')}] Final transcription complete ({stt_latency_ms}ms via {stt_provider}): '{transcript}'"
        )

        await websocket.send_json(
            {
                "type": "transcript",
                "text": transcript,
                "final": True,
                "turn_id": turn_id,
            }
        )

        if not transcript.strip():
            await websocket.send_json({"type": "done", "turn_id": turn_id})
            return

        # Trigger LLM and stream response
        await websocket.send_json(
            {"type": "status", "state": "processing_intent", "turn_id": turn_id}
        )

        chat_request = ChatRequest(
            message=transcript, conversation_id=session_state.active_conversation_id
        )

        # Retrieve prefetched memories
        prefetched = session_state.prefetched_memories
        session_state.prefetched_memories = None  # consume

        async for event in streaming_coordinator.stream_chat(
            chat_request, prefetched_memories=prefetched
        ):
            # Check for early exit/barge-in interruption
            if session_state.interrupted:
                _log.info(f"[VOICE-WS] Turn {turn_id} interrupted by barge-in event.")
                raise asyncio.CancelledError()

            if event.startswith("data: "):
                payload_str = event[6:].strip()
                if payload_str:
                    payload = json.loads(payload_str)
                    payload["turn_id"] = turn_id
                    if payload.get("type") == "done":
                        total_turn_ms = round((time.time() - turn_start_time) * 1000)
                        if "metrics" in payload:
                            payload["metrics"]["stt_latency_ms"] = stt_latency_ms
                            payload["metrics"]["total_turn_ms"] = total_turn_ms
                            payload["metrics"]["stt_provider"] = stt_provider
                            payload["metrics"]["tts_provider"] = (
                                settings.friday_tts_provider
                            )
                    await websocket.send_json(payload)

    # Gather reader, rolling STT, and writer tasks
    group = asyncio.gather(reader_loop(), rolling_stt_loop(), writer_loop())
    try:
        await group
    except WebSocketDisconnect:
        _log.info(
            f"[TRACE] [Stage 11] [{datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')}] Socket closed: WebSocket voice stream disconnected by client"
        )
    except Exception as exc:
        _log.error(
            f"[TRACE] [Stage 11] [{datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')}] Socket closed with error in handler: {exc}",
            exc_info=True,
        )
    finally:
        # Cancel tasks in group
        group.cancel()
        _log.info(
            f"[TRACE] [Stage 11] [{datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')}] WebSocket connection clean up complete"
        )
