from fastapi import APIRouter
from app.schemas.schemas import UserSettings

router = APIRouter(prefix="/settings", tags=["settings"])

@router.get("/", response_model=UserSettings)
def get_settings():
    return UserSettings()

@router.post("/")
def save_settings(settings: UserSettings):
    return {"status": "success", "settings": settings}
