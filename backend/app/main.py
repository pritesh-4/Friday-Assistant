"""FRIDAY API — application entry point."""

import time
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, status, WebSocket, Depends
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

# Import API routes
from app.api.routes import (
    chat,
    files,
    health,
    memory,
    notes,
    tasks,
    voice,
    planning,
    background,
)
from app.api.routes.voice import websocket_voice_stream
from app.api.routes import (
    settings as settings_route,
)
from app.core.config import settings
from app.core.constants import API_DESCRIPTION, API_TITLE, API_VERSION
from app.core.logging import get_logger
from app.core.middleware import RequestContextMiddleware
from app.core.rate_limit import configure_rate_limiting
from app.db.database import database
from app.schemas.errors import ErrorResponse, ErrorDetail
from app.services.worker import BackgroundWorker
from app.api.dependencies import (
    get_agent_manager,
    get_scheduler,
    get_transcription_service,
    get_streaming_coordinator,
)

_log = get_logger("main")

# Module-level startup timestamp for uptime reporting in /health.
# Set during the lifespan startup event so it reflects actual service readiness.
_startup_time: float | None = None

# Global background worker instance
_bg_worker: BackgroundWorker | None = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Handle API startup and shutdown lifecycles."""
    global _startup_time

    _log.info("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    _log.info("  F.R.I.D.A.Y. API  —  version %s", API_VERSION)
    _log.info("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    _log.info("✓ Environment : %s", settings.app_env)
    _log.info("✓ Debug mode  : %s", settings.debug)
    _log.info("✓ Log level   : %s", settings.log_level)
    _log.info("✓ Voice       : %s", "enabled" if settings.voice_enabled else "disabled")

    # ── Stage 1: Database ─────────────────────────────────────────────────────
    _log.info("[1/3] Initializing database...")
    try:
        await database.initialize()
        _log.info("✓ SQLite persistence ready: %s", database.path)
    except Exception as exc:
        _log.critical(
            "FATAL: Database initialization failed — cannot start without persistence. "
            "Error: %s",
            exc,
            exc_info=True,
        )
        raise  # DB failure IS a fatal error — we cannot serve without persistence.

    # ── Stage 2: Voice models (optional) ──────────────────────────────────────
    if settings.voice_enabled:
        _log.info("[2/3] Voice models enabled (VOICE_ENABLED=true).")
        _log.info("      Validating dependencies and initializing WhisperEngine...")

        try:
            # Import to verify dependencies
            import faster_whisper  # noqa: F401
            import ctranslate2  # noqa: F401
            import av  # noqa: F401
            import tokenizers  # noqa: F401
            import shutil

            if not shutil.which("ffmpeg"):
                raise RuntimeError("ffmpeg executable not found in system PATH.")

            from app.ai.whisper.engine import WhisperEngine

            engine = WhisperEngine()
            _log.info(f"      Model     : {engine.model_name} (default)")
            _log.info(f"      Device    : {engine.device}")
            _log.info(f"      Compute   : {engine.compute_type}")
            _log.info(
                "      Dependencies validated. Model will be lazily loaded into memory on the first STT request."
            )
        except ImportError as exc:
            _log.critical(
                "FATAL: Voice features are enabled but required dependencies are missing.\n"
                "Please run: pip install -r requirements-voice.txt\n"
                f"Error: {exc}"
            )
            raise RuntimeError(f"Missing voice dependency: {exc}") from exc
        except RuntimeError as exc:
            _log.critical(f"FATAL: Voice initialization failed: {exc}")
            raise
    else:
        _log.info("[2/3] Voice models skipped (VOICE_ENABLED=false).")

    # ── Stage 3: Ready ────────────────────────────────────────────────────────

    # Start Background Worker & Scheduler
    agent_mgr = get_agent_manager()
    global _bg_worker
    _bg_worker = BackgroundWorker(agent_mgr)
    await _bg_worker.start()

    scheduler = get_scheduler()
    await scheduler.start()

    _startup_time = time.monotonic()
    _log.info("[3/3] All routes registered. API is ready.")
    _log.info("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")

    yield

    # ── Shutdown ──────────────────────────────────────────────────────────────
    if _bg_worker:
        _bg_worker.stop()

    scheduler = get_scheduler()
    if scheduler:
        scheduler.stop()

    _log.info("Shutting down F.R.I.D.A.Y. API.")


# ── Application ────────────────────────────────────────────────────────────────

app = FastAPI(
    title=API_TITLE,
    description=API_DESCRIPTION,
    version=API_VERSION,
    lifespan=lifespan,
)

# ── Rate Limiting ─────────────────────────────────────────────────────────────
configure_rate_limiting(app)

# ── CORS ──────────────────────────────────────────────────────────────────────

_origins = ["http://localhost:5173", "http://127.0.0.1:5173", "http://localhost:3000"]
if settings.frontend_url and settings.frontend_url not in _origins:
    _origins.append(settings.frontend_url)

app.add_middleware(
    CORSMiddleware,
    allow_origins=_origins,
    allow_origin_regex=r"https://.*\.vercel\.app",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(RequestContextMiddleware)

# ── Exception handlers ────────────────────────────────────────────────────────


@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(
    request: Request, exc: StarletteHTTPException
) -> JSONResponse:
    """Return clean, consistent HTTP error responses."""
    _log.warning("HTTP %s — %s %s", exc.status_code, request.method, request.url.path)

    msg = (
        "The requested resource was not found."
        if exc.status_code == status.HTTP_404_NOT_FOUND
        else exc.detail
    )

    err = ErrorResponse(
        error=ErrorDetail(
            code=f"HTTP_{exc.status_code}",
            message=msg,
            request_id=getattr(request.state, "request_id", None),
        )
    )
    return JSONResponse(status_code=exc.status_code, content=err.model_dump())


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    """Return a predictable validation error envelope for browser clients."""
    err = ErrorResponse(
        error=ErrorDetail(
            code="VALIDATION_ERROR",
            message="Request validation failed.",
            details=exc.errors(),
            request_id=getattr(request.state, "request_id", None),
        )
    )
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=err.model_dump(),
    )


@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Return a safe 500 response for unhandled exceptions, without leaking internals."""
    _log.error(
        "Unhandled exception on %s %s: %s",
        request.method,
        request.url.path,
        exc,
        exc_info=True,
    )
    err = ErrorResponse(
        error=ErrorDetail(
            code="INTERNAL_SERVER_ERROR",
            message="An internal server error occurred.",
            request_id=getattr(request.state, "request_id", None),
        )
    )
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=err.model_dump(),
    )


# ── Routers ───────────────────────────────────────────────────────────────────

app.include_router(health.router, prefix="/health")
app.include_router(chat.router, prefix="/chat")
app.include_router(memory.router, prefix="/memory")
app.include_router(voice.router, prefix="/voice")
app.include_router(files.router, prefix="/files")
app.include_router(settings_route.router, prefix="/settings")
app.include_router(notes.router, prefix="/notes")
app.include_router(tasks.router, prefix="/tasks")
app.include_router(planning.router)
app.include_router(background.router)


# WebSocket legacy path compatibility mapping
@app.websocket("/api/voice/stream")
async def websocket_voice_stream_alias(
    websocket: WebSocket,
    transcription_service=Depends(get_transcription_service),
    streaming_coordinator=Depends(get_streaming_coordinator),
):
    """WebSocket route alias to support legacy frontend connection paths."""
    await websocket_voice_stream(
        websocket, transcription_service, streaming_coordinator
    )


# ── Root endpoint ─────────────────────────────────────────────────────────────


@app.get("/", tags=["root"], summary="API root")
async def read_root() -> dict[str, str]:
    """
    API root — confirms the service is online and returns basic metadata.

    Use ``/health`` for liveness and ``/health/ready`` for readiness probes.
    """
    return {
        "message": "FRIDAY API is online.",
        "version": API_VERSION,
        "docs": "/docs",
    }
