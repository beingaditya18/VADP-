"""
VADP Auth Repository
=========================

Data access layer for User and Session entities using SQLAlchemy 2.x async API.
Abstracts database operations away from business logic.
"""

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.models import Session, User


class UserRepository:
    """Repository pattern implementation for User entity operations."""

    def __init__(self, session: AsyncSession) -> None:
        self.db = session

    async def create_user(self, user: User) -> User:
        """Add a new user to the database."""
        self.db.add(user)
        await self.db.flush()
        await self.db.refresh(user)
        return user

    async def get_by_id(self, user_id: str) -> User | None:
        """Fetch a user by primary key UUID string."""
        result = await self.db.execute(select(User).where(User.id == user_id))
        return result.scalar_one_or_none()

    async def get_by_email(self, email: str) -> User | None:
        """Fetch a user by email address."""
        result = await self.db.execute(select(User).where(User.email == email.lower()))
        return result.scalar_one_or_none()

    async def update_last_login(self, user_id: str) -> None:
        """Update last_login_at timestamp for user."""
        now = datetime.now(timezone.utc)
        await self.db.execute(
            update(User).where(User.id == user_id).values(last_login_at=now)
        )

    async def update_profile(self, user_id: str, updates: dict) -> User | None:
        """Update profile fields for a user."""
        user = await self.get_by_id(user_id)
        if not user:
            return None
        for field, value in updates.items():
            if value is not None and hasattr(user, field):
                setattr(user, field, value)
        user.updated_at = datetime.now(timezone.utc)
        await self.db.flush()
        await self.db.refresh(user)
        return user


class SessionRepository:
    """Repository pattern implementation for Session entity operations."""

    def __init__(self, session: AsyncSession) -> None:
        self.db = session

    async def create_session(self, session_obj: Session) -> Session:
        """Store a new auth session."""
        self.db.add(session_obj)
        await self.db.flush()
        await self.db.refresh(session_obj)
        return session_obj

    async def get_by_id(self, session_id: str) -> Session | None:
        """Fetch session by ID."""
        result = await self.db.execute(select(Session).where(Session.id == session_id))
        return result.scalar_one_or_none()

    async def deactivate_user_sessions(self, user_id: str) -> None:
        """Deactivate all active sessions for a user (e.g., on password reset or logout all)."""
        await self.db.execute(
            update(Session)
            .where(Session.user_id == user_id, Session.is_active == True)  # noqa: E712
            .values(is_active=False)
        )
