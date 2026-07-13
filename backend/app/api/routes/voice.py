from fastapi import APIRouter, HTTPException, status

router = APIRouter(tags=["voice"])

@router.get("")
async def get_voice_status():
    """Describe the intentionally deferred server-side voice capability."""
    return {"available": False, "detail": "Server-side voice is planned for a later milestone."}

@router.post("/synthesize")
async def synthesize_voice():
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Server-side speech synthesis is not implemented yet.",
    )

@router.post("/transcribe")
async def transcribe_voice():
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Server-side transcription is not implemented yet.",
    )
