"""Service for managing user notifications."""

from app.core.logging import get_logger
from app.db.database import database
from app.schemas.background import Notification, NotificationCreate, NotificationStatus
from app.utils.helpers import generate_uuid, get_utc_now

logger = get_logger(__name__)

class NotificationService:
    async def create_notification(self, data: NotificationCreate) -> Notification:
        notif_id = generate_uuid()
        now = get_utc_now().isoformat()
        
        await database.execute(
            """
            INSERT INTO notifications (id, title, message, type, action_url, status, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (notif_id, data.title, data.message, data.type.value, data.action_url, NotificationStatus.UNREAD.value, now)
        )
        logger.info(f"Notification created: {data.title}")
        return await self.get_notification(notif_id)

    async def get_notification(self, notif_id: str) -> Notification | None:
        row = await database.fetch_one("SELECT * FROM notifications WHERE id = ?", (notif_id,))
        if not row:
            return None
        return Notification.model_validate(dict(row))

    async def list_notifications(self, status: NotificationStatus | None = None, limit: int = 50) -> list[Notification]:
        if status:
            rows = await database.fetch_all(
                "SELECT * FROM notifications WHERE status = ? ORDER BY created_at DESC LIMIT ?", 
                (status.value, limit)
            )
        else:
            rows = await database.fetch_all(
                "SELECT * FROM notifications ORDER BY created_at DESC LIMIT ?", 
                (limit,)
            )
        return [Notification.model_validate(dict(r)) for r in rows]

    async def mark_as_read(self, notif_id: str) -> None:
        await database.execute(
            "UPDATE notifications SET status = ? WHERE id = ?",
            (NotificationStatus.READ.value, notif_id)
        )

# Global singleton
notification_service = NotificationService()
