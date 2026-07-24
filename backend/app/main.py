"""FRIDAY API — application entry point."""

import time
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core.config import settings
from app.core.constants import API_DESCRIPTION, API_TITLE, API_VERSION
from app.core.logging import get_logger
from app.db.database import database

# Import API routes
from app.api.routes import (
    chat,
    files,
    health,
    memory,
    notes,
    settings as settings_route,
    tasks,
    voice,
)

_log = get_logger("main")

# Module-level startup timestamp for uptime reporting in /health.
# Set during the lifespan startup event so it reflects actual service readiness.
_startup_time: float | None = None


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
        _log.info("      Models will be lazily loaded into memory on the first request.")
    else:
        _log.info("[2/3] Voice models skipped (VOICE_ENABLED=false).")

    # ── Stage 3: Ready ────────────────────────────────────────────────────────
    _startup_time = time.monotonic()
    _log.info("[3/3] All routes registered. API is ready.")
    _log.info("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")

    yield

    # ── Shutdown ──────────────────────────────────────────────────────────────
    _log.info("Shutting down F.R.I.D.A.Y. API.")


# ── Application ────────────────────────────────────────────────────────────────

app = FastAPI(
    title=API_TITLE,
    description=API_DESCRIPTION,
    version=API_VERSION,
    lifespan=lifespan,
)

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

# ── Exception handlers ────────────────────────────────────────────────────────


@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
    """Return clean, consistent HTTP error responses."""
    _log.warning("HTTP %s — %s %s", exc.status_code, request.method, request.url.path)
    if exc.status_code == status.HTTP_404_NOT_FOUND:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={"detail": "The requested resource was not found."},
        )
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    """Return a predictable validation error envelope for browser clients."""
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": "Request validation failed.", "errors": exc.errors()},
    )


@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Return a safe 500 response for unhandled exceptions, without leaking internals."""
    _log.error(
        "Unhandled exception on %s %s: %s", request.method, request.url.path, exc, exc_info=True
    )
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "An internal server error occurred."},
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
