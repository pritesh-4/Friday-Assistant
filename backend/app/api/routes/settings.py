"""Settings route — user preferences and provider configuration."""

from fastapi import APIRouter, Depends

from app.api.dependencies import get_settings_service
from app.core.config import settings
from app.schemas.common import UserSettings
from app.services.settings_service import SettingsService

router = APIRouter(tags=["settings"])


@router.get("", response_model=UserSettings)
async def get_settings(
    service: SettingsService = Depends(get_settings_service),
) -> UserSettings:
    """Return persisted presentation preferences for the local user."""
    return await service.get_settings()


@router.put("", response_model=UserSettings)
@router.post("", response_model=UserSettings, include_in_schema=False)
async def update_settings(
    request: UserSettings,
    service: SettingsService = Depends(get_settings_service),
) -> UserSettings:
    """
    Replace persisted preferences.

    PUT is the canonical method. POST is accepted for backwards compatibility
    with older local clients.
    """
    return await service.update_settings(request)


@router.get("/providers")
async def get_providers() -> dict[str, str | list[str]]:
    """
    Expose which LLM providers are configured.

    Credentials are never returned — only the provider name and active status.
    """
    configured = []
    if settings.groq_api_key:
        configured.append("groq")
    if settings.gemini_api_key:
        configured.append("gemini")
    if settings.openrouter_api_key:
        configured.append("openrouter")
    if settings.nvidia_api_key:
        configured.append("nvidia")

    return {
        "providers": configured or ["local-fallback"],
        "active": configured[0] if configured else "local-fallback",
        "model": getattr(settings, f"{configured[0]}_model") if configured else None,
    }
