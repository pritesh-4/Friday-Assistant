from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core.config import settings
from app.core.constants import API_TITLE, API_DESCRIPTION, API_VERSION
from app.core.logging import logger
from app.db.database import database

# Import API routes
from app.api.routes import (
    health,
    chat,
    memory,
    voice,
    files,
    notes,
    settings as settings_route,
    tasks,
)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Handles API startup and shutdown lifecycles.
    """
    logger.info("Initializing F.R.I.D.A.Y. API...")
    logger.info(f"Environment: {settings.app_env}")
    logger.info(f"Debug Mode: {settings.debug}")
    await database.initialize()
    logger.info("SQLite persistence is ready.")
    yield
    logger.info("Shutting down F.R.I.D.A.Y. API...")

# Initialize FastAPI application
app = FastAPI(
    title=API_TITLE,
    description=API_DESCRIPTION,
    version=API_VERSION,
    lifespan=lifespan
)

# CORS setup
origins = [
    "http://localhost:5173",
]
if settings.frontend_url and settings.frontend_url not in origins:
    origins.append(settings.frontend_url)

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Custom exception handlers
@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    """
    Return clean and consistent HTTP exception responses, with special formatting for 404.
    """
    logger.warning(f"HTTP exception: {exc.status_code} - {exc.detail}")
    if exc.status_code == 404:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={"detail": "The requested resource was not found."}
        )
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail}
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Return a predictable validation envelope for browser clients."""
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
        content={"detail": "Request validation failed.", "errors": exc.errors()},
    )

@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    """
    Return clean 500 responses for unhandled application exceptions.
    """
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "An internal server error occurred."}
    )

# Router registrations
app.include_router(health.router, prefix="/health")
app.include_router(chat.router, prefix="/chat")
app.include_router(memory.router, prefix="/memory")
app.include_router(voice.router, prefix="/voice")
app.include_router(files.router, prefix="/files")
app.include_router(settings_route.router, prefix="/settings")
app.include_router(notes.router, prefix="/notes")
app.include_router(tasks.router, prefix="/tasks")

@app.get("/")
def read_root():
    """
    Root endpoint for FRIDAY API.
    """
    return {
        "message": "FRIDAY API is online."
    }
