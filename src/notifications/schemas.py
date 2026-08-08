"""
VADP Notifications Schemas
===============================

Pydantic schemas for creating and displaying in-app user notifications.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class NotificationCreateSchema(BaseModel):
    user_id: str
    title: str
    message: str
    notification_type: str = "system"
    link: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class NotificationResponseSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    user_id: str
    title: str
    message: str
    notification_type: str
    is_read: bool
    link: str | None = None
    created_at: datetime
