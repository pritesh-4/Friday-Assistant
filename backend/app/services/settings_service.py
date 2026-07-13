from app.db.database import database
from app.schemas.common import UserSettings


class SettingsService:
    """Store the single local user's presentation preferences."""

    async def get_settings(self) -> UserSettings:
        row = await database.fetch_one("SELECT * FROM user_settings WHERE id = 1")
        if row is None:
            raise RuntimeError("Default user settings were not initialized.")
        return UserSettings.model_validate(row)

    async def update_settings(self, settings_data: UserSettings) -> UserSettings:
        await database.execute(
            """
            UPDATE user_settings
            SET theme = ?, animations = ?, voice_enabled = ?, sidebar_collapsed = ?,
                memory_enabled = ?, notifications_enabled = ?
            WHERE id = 1
            """,
            (
                settings_data.theme,
                settings_data.animations,
                settings_data.voice_enabled,
                settings_data.sidebar_collapsed,
                settings_data.memory_enabled,
                settings_data.notifications_enabled,
            ),
        )
        return await self.get_settings()
