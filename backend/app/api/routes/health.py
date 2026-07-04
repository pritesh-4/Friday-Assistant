from fastapi import APIRouter

router = APIRouter(tags=["health"])

@router.get("")
def health_check():
    """
    Check the running status of the F.R.I.D.A.Y. API.
    """
    return {
        "status": "ok",
        "service": "FRIDAY API"
    }
