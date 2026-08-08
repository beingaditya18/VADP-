"""
VADP Notifications Service
================================

Business logic for creating, fetching, and marking notifications as read.
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.core.logging import get_logger
from app.notifications.models import Notification
from app.notifications.schemas import NotificationCreateSchema, NotificationResponseSchema

logger = get_logger(__name__)


class NotificationService:
    """Service managing user notifications."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def create_notification(self, schema: NotificationCreateSchema) -> NotificationResponseSchema:
        """Create a new user notification."""
        notif = Notification(
            user_id=schema.user_id,
            title=schema.title,
            message=schema.message,
            notification_type=schema.notification_type,
            link=schema.link,
            metadata_=schema.metadata,
        )
        self.db.add(notif)
        await self.db.flush()
        await self.db.refresh(notif)
        logger.info("Created notification", extra={"user_id": schema.user_id, "type": schema.notification_type})
        return NotificationResponseSchema.model_validate(notif)

    async def get_user_notifications(self, user_id: str, unread_only: bool = False) -> list[NotificationResponseSchema]:
        """Fetch notifications for a user."""
        query = select(Notification).where(Notification.user_id == user_id)
        if unread_only:
            query = query.where(Notification.is_read.is_(False))
        query = query.order_by(Notification.created_at.desc())

        result = await self.db.execute(query)
        notifications = result.scalars().all()
        return [NotificationResponseSchema.model_validate(n) for n in notifications]

    async def mark_as_read(self, notification_id: str, user_id: str) -> NotificationResponseSchema:
        """Mark a notification as read."""
        query = select(Notification).where(
            Notification.id == notification_id,
            Notification.user_id == user_id,
        )
        result = await self.db.execute(query)
        notif = result.scalar_one_or_none()
        if not notif:
            raise NotFoundError(message="Notification not found.")

        notif.is_read = True
        await self.db.flush()
        return NotificationResponseSchema.model_validate(notif)
