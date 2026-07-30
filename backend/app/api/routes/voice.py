"""Voice routes — server-side speech-to-text and text-to-speech.

Endpoints:
  GET  /voice          — Capability status probe.
  GET  /voice/health   — Detailed STT/TTS diagnostic health check.
  POST /voice/upload   — Upload raw audio blob to temporary storage.
  POST /voice/transcribe — Transcribe audio using Faster-Whisper STT.
  POST /voice/speak    — Synthesize text to WAV audio using Kokoro TTS.

All endpoints check VOICE_ENABLED at runtime and return 503 with a clear
message if voice features are disabled. This prevents confusing 500 errors
when faster-whisper / kokoro-onnx are not installed.
"""

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
async def get_voice_status() -> dict[str, Any]:
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

    from app.ai.tts.loader import is_tts_available

    whisper_engine = WhisperEngine()

    return {
        "available": True,
        "stt": "faster-whisper" if whisper_engine.is_loaded else "unavailable",
        "tts": "kokoro-onnx" if is_tts_available() else "unavailable",
        "detail": "Server-side STT and TTS status reported above.",
        "browser_fallback": not (whisper_engine.is_loaded and is_tts_available()),
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
    Convert text to a WAV audio stream using the Kokoro TTS engine.
    Returns binary audio/wav. Maximum input is 3,000 characters.
    """
    _require_voice()

    import time

    start_time = time.time()
    _log.info("[VOICE] START POST /voice/speak")

    try:
        audio_bytes = await speech_service.synthesize(request.text)
        elapsed = time.time() - start_time
        _log.info(f"[VOICE] SUCCESS POST /voice/speak in {elapsed:.2f}s")
        return Response(content=audio_bytes, media_type="audio/wav")
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


@router.websocket("/stream")
async def websocket_voice_stream(
    websocket: WebSocket,
    transcription_service: TranscriptionService = Depends(get_transcription_service),
    streaming_coordinator=Depends(get_streaming_coordinator),
):
    """
    WebSocket endpoint for real-time binary audio streaming.
    Receives raw 16kHz Int16 mono PCM chunks from client,
    buffers in memory, transcribes, and streams response events.
    """
    import json
    import numpy as np
    from datetime import datetime, timezone

    # Stage 1: Client starts connection & Stage 2: Server receives connection
    _log.info(
        f"[TRACE] [Stage 1 & 2] [{datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')}] WebSocket connection request received by server"
    )

    # Stage 3: websocket.accept()
    _log.info(
        f"[TRACE] [Stage 3] [{datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')}] Initiating websocket.accept()..."
    )
    await websocket.accept()
    _log.info(
        f"[TRACE] [Stage 3] [{datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')}] websocket.accept() complete"
    )

    # Stage 4: Authentication
    # When SECRET_KEY is configured, the client must pass ?token=<SECRET_KEY>.
    # If not configured, auth is skipped (open MVP mode).
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

    audio_chunks = []
    active_conversation_id = None
    first_message_received = False

    try:
        while True:
            message = await websocket.receive()

            if not first_message_received:
                # Stage 7: First message received
                _log.info(
                    f"[TRACE] [Stage 7] [{datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')}] First message received from client"
                )
                first_message_received = True

            if "bytes" in message:
                data = message["bytes"]
                if len(data) > 0:
                    # Convert bytes to Int16 numpy array, then normalize to float32
                    chunk = (
                        np.frombuffer(data, dtype=np.int16).astype(np.float32) / 32768.0
                    )
                    audio_chunks.append(chunk)

            elif "text" in message:
                try:
                    command = json.loads(message["text"])
                    cmd_type = command.get("type")

                    if cmd_type == "start":
                        active_conversation_id = command.get("conversation_id")
                        audio_chunks = []
                        _log.info(
                            f"[VOICE-WS] Session started for conversation: {active_conversation_id}"
                        )
                        await websocket.send_json({"type": "session_started"})

                    elif cmd_type == "stop":
                        _log.info(
                            "[VOICE-WS] Silence detected or user stopped speaking. Finalizing turn..."
                        )
                        if not audio_chunks:
                            await websocket.send_json(
                                {"type": "transcript", "text": "", "final": True}
                            )
                            continue

                        # Concatenate all chunks to a single numpy array, then reset
                        # the buffer immediately so the next turn starts clean.
                        full_audio = np.concatenate(audio_chunks)
                        audio_chunks = []

                        await websocket.send_json(
                            {"type": "status", "state": "transcribing"}
                        )

                        # Stage 8: Transcription starts
                        _log.info(
                            f"[TRACE] [Stage 8] [{datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')}] Transcription starts on buffered audio array"
                        )
                        stt_result = await transcription_service.transcribe_array(
                            full_audio
                        )
                        transcript = stt_result["transcript"]
                        _log.info(
                            f"[TRACE] [Stage 8] [{datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')}] Transcription complete: '{transcript}'"
                        )

                        _log.info(f"[VOICE-WS] Final transcript: '{transcript}'")
                        await websocket.send_json(
                            {"type": "transcript", "text": transcript, "final": True}
                        )

                        # If transcript is empty, stop
                        if not transcript.strip():
                            await websocket.send_json({"type": "done"})
                            continue

                        # Trigger LLM and stream response
                        await websocket.send_json(
                            {"type": "status", "state": "processing_intent"}
                        )

                        from app.schemas.chat import ChatRequest

                        chat_request = ChatRequest(
                            message=transcript, conversation_id=active_conversation_id
                        )

                        async for event in streaming_coordinator.stream_chat(
                            chat_request
                        ):
                            if event.startswith("data: "):
                                payload_str = event[6:].strip()
                                if payload_str:
                                    payload = json.loads(payload_str)
                                    await websocket.send_json(payload)

                except Exception as exc:
                    _log.error(
                        f"[VOICE-WS] Error processing text frame: {exc}", exc_info=True
                    )
                    await websocket.send_json({"type": "error", "message": str(exc)})

    except WebSocketDisconnect:
        # Stage 11: Socket closed
        _log.info(
            f"[TRACE] [Stage 11] [{datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')}] Socket closed: WebSocket voice stream disconnected by client"
        )
    except Exception as exc:
        _log.error(
            f"[TRACE] [Stage 11] [{datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')}] Socket closed with error in handler: {exc}",
            exc_info=True,
        )
    finally:
        _log.info(
            f"[TRACE] [Stage 11] [{datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')}] WebSocket connection clean up complete"
        )
