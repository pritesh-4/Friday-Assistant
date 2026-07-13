from fastapi import APIRouter

from app.core.config import settings
from app.schemas.common import UserSettings
from app.services.settings_service import SettingsService

router = APIRouter(tags=["settings"])
service = SettingsService()


@router.get("", response_model=UserSettings)
async def get_settings() -> UserSettings:
    """Return persisted presentation preferences for this local user."""
    return await service.get_settings()


@router.put("", response_model=UserSettings)
@router.post("", response_model=UserSettings, include_in_schema=False)
async def update_settings(request: UserSettings) -> UserSettings:
    """Replace persisted preferences. POST remains for older local clients."""
    return await service.update_settings(request)


@router.get("/providers")
async def get_providers() -> dict[str, str | list[str]]:
    """Expose configured providers without ever exposing credentials."""
    return {
        "providers": ["openai"],
        "active": "openai" if settings.openai_api_key else "local-fallback",
    }
