"""
VADP Notifications Router
==============================

REST API endpoints for user notifications:
  - GET  /api/v1/notifications
  - POST /api/v1/notifications/{id}/read
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user
from app.auth.models import User
from app.db.session import get_db_session
from app.notifications.schemas import NotificationResponseSchema
from app.notifications.service import NotificationService

router = APIRouter(prefix="/notifications", tags=["notifications"])


@router.get(
    "",
    response_model=list[NotificationResponseSchema],
    status_code=status.HTTP_200_OK,
    summary="Get user notifications",
    description="Retrieve all notifications for the current authenticated user.",
)
async def get_my_notifications(
    unread_only: bool = False,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> list[NotificationResponseSchema]:
    service = NotificationService(db)
    return await service.get_user_notifications(current_user.id, unread_only=unread_only)


@router.post(
    "/{notification_id}/read",
    response_model=NotificationResponseSchema,
    status_code=status.HTTP_200_OK,
    summary="Mark notification as read",
    description="Update notification status to read.",
)
async def mark_notification_read(
    notification_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> NotificationResponseSchema:
    service = NotificationService(db)
    return await service.mark_as_read(notification_id, current_user.id)
