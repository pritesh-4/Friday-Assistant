"""FRIDAY API — application entry point."""

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


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Handle API startup and shutdown lifecycles."""
    _log.info("Initializing F.R.I.D.A.Y. API — version %s", API_VERSION)
    _log.info("Environment: %s | Debug: %s | Log level: %s", settings.app_env, settings.debug, settings.log_level)
    await database.initialize()
    _log.info("SQLite persistence is ready: %s", database.path)
    yield
    _log.info("Shutting down F.R.I.D.A.Y. API.")


# ── Application ────────────────────────────────────────────────────────────────

app = FastAPI(
    title=API_TITLE,
    description=API_DESCRIPTION,
    version=API_VERSION,
    lifespan=lifespan,
)

# ── CORS ──────────────────────────────────────────────────────────────────────

_origins = ["http://localhost:5173"]
if settings.frontend_url and settings.frontend_url not in _origins:
    _origins.append(settings.frontend_url)

app.add_middleware(
    CORSMiddleware,
    allow_origins=_origins,
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
    _log.error("Unhandled exception on %s %s: %s", request.method, request.url.path, exc, exc_info=True)
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
