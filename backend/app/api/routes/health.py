"""Health route — liveness and readiness probes."""

from fastapi import APIRouter

from app.core.constants import API_VERSION
from app.db.database import database

router = APIRouter(tags=["health"])


@router.get("", summary="Liveness probe")
async def health_check() -> dict[str, str]:
    """
    Confirm the API process is running.

    Returns the service name and current API version.  Does **not** check
    downstream dependencies — use ``/health/ready`` for that.
    """
    return {
        "status": "ok",
        "service": "FRIDAY API",
        "version": API_VERSION,
    }


@router.get("/ready", summary="Readiness probe")
async def readiness_check() -> dict[str, str]:
    """
    Confirm the API is ready to handle requests.

    Verifies that the SQLite persistence layer is reachable.
    Returns a non-2xx response if the database is unavailable.
    """
    await database.fetch_one("SELECT 1 AS ready")
    return {"status": "ok", "database": "ready"}
