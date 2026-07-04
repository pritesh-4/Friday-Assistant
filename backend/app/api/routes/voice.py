from fastapi import APIRouter

router = APIRouter(tags=["voice"])

@router.get("")
def get_voice_placeholder():
    """
    Placeholder endpoint to retrieve voice configuration or status.
    """
    return {
        "message": "Voice endpoint coming soon."
    }

@router.post("/synthesize")
def post_voice_synthesize_placeholder():
    """
    Placeholder endpoint for text-to-speech voice generation.
    """
    return {
        "message": "Voice synthesis endpoint coming soon."
    }

@router.post("/transcribe")
def post_voice_transcribe_placeholder():
    """
    Placeholder endpoint for speech-to-text voice transcription.
    """
    return {
        "message": "Voice transcription endpoint coming soon."
    }
