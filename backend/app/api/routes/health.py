from fastapi import APIRouter

from app.db.database import database

router = APIRouter(tags=["health"])

@router.get("")
async def health_check():
    """
    Check the running status of the F.R.I.D.A.Y. API.
    """
    return {
        "status": "ok",
        "service": "FRIDAY API"
    }


@router.get("/ready")
async def readiness_check():
    """Confirm the local persistence layer is available."""
    await database.fetch_one("SELECT 1 AS ready")
    return {"status": "ok", "database": "ready"}
