from fastapi import APIRouter
from app.schemas.common import UserSettings

router = APIRouter(tags=["settings"])

@router.get("")
def get_settings_placeholder():
    """
    Placeholder endpoint to retrieve user settings.
    """
    return {
        "message": "Settings endpoint coming soon."
    }

@router.post("")
def post_settings_placeholder(settings: UserSettings):
    """
    Placeholder endpoint to update user settings.
    """
    return {
        "message": "Settings endpoint coming soon.",
        "settings": settings.model_dump()
    }
