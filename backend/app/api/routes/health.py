"""Health route — liveness and readiness probes.

Endpoints:
  GET /health        — Liveness probe. Always responds quickly. No DB queries.
  GET /health/ready  — Readiness probe. Verifies database connectivity.

Design rules:
  - /health MUST always return 200 quickly — Render uses this as the health check.
  - /health/ready may return 503 if downstream dependencies are not ready.
  - Neither endpoint should expose internal implementation details.
"""

import time
from typing import Any

from fastapi import APIRouter, status
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.core.constants import API_VERSION
from app.db.database import database

router = APIRouter(tags=["health"])


# Reference to the startup timestamp set in main.py lifespan.
# Imported lazily to avoid circular import issues at module load time.
def _get_uptime_seconds() -> float:
    """Return seconds since the API started, or -1 if startup hasn't completed."""
    try:
        from app.main import _startup_time

        if _startup_time is not None:
            return round(time.monotonic() - _startup_time, 1)
    except ImportError:
        pass
    return -1.0


@router.get(
    "",
    summary="Liveness probe",
    response_description="API process is alive and serving requests.",
)
async def health_check() -> dict[str, Any]:
    """
    Confirm the API process is running.

    This is the primary health check endpoint used by Render. It MUST:
    - Always return HTTP 200.
    - Respond in under 100ms.
    - Never query external services or the database.

    For dependency checks, use ``/health/ready``.
    """
    uptime = _get_uptime_seconds()
    return {
        "status": "ok",
        "version": API_VERSION,
        "environment": settings.app_env,
        "uptime_seconds": uptime,
        "services": {
            "api": True,
            "voice_enabled": settings.voice_enabled,
        },
    }


@router.get(
    "/ready",
    summary="Readiness probe",
    response_description="API is ready to handle all requests including DB-backed ones.",
)
async def readiness_check() -> JSONResponse:
    """
    Confirm the API is ready to handle requests.

    Verifies that the SQLite persistence layer is reachable. Returns HTTP 503
    if the database is unavailable so load balancers can route around an
    unready instance.
    """
    db_ok = False
    db_error: str | None = None

    try:
        result = await database.fetch_one("SELECT 1 AS ready")
        db_ok = result is not None
    except Exception as exc:
        db_error = str(exc)

    if not db_ok:
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "status": "unavailable",
                "database": "unreachable",
                "detail": db_error or "Database did not respond.",
            },
        )

    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={
            "status": "ok",
            "database": "ready",
            "version": API_VERSION,
        },
    )
