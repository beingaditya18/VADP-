"""
VADP Auth Dependencies
===========================

FastAPI dependencies for extracting and verifying the authenticated user from JWT.
Supports role-based access restrictions.
"""

from __future__ import annotations

from typing import Callable

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.models import User
from app.auth.repository import UserRepository
from app.auth.token_blacklist import TokenBlacklistService
from app.core.exceptions import InsufficientRoleError, TokenInvalidError
from app.core.security import extract_user_id_from_token, get_token
from app.db.session import get_db_session


async def get_current_user(
    token: str = Depends(get_token),
    db: AsyncSession = Depends(get_db_session),
) -> User:
    """
    FastAPI dependency that extracts the JWT token, resolves the user from DB,
    and returns the User object.

    Raises:
        TokenInvalidError: If token is invalid, blacklisted, or user does not exist/is inactive.
    """
    if TokenBlacklistService.is_blacklisted(token):
        raise TokenInvalidError(message="Token has been revoked/logged out.")

    user_id = extract_user_id_from_token(token)
    user_repo = UserRepository(db)
    user = await user_repo.get_by_id(user_id)

    if not user or not user.is_active:
        raise TokenInvalidError(
            message="Authenticated user account is inactive or no longer exists."
        )

    return user


async def get_current_active_user(
    current_user: User = Depends(get_current_user),
) -> User:
    """
    Dependency ensuring current user is active.
    """
    if not current_user.is_active:
        raise TokenInvalidError(message="Inactive user.")
    return current_user


def require_role(*allowed_roles: str) -> Callable:
    """
    Dependency factory that restricts access to users with specified roles.

    Usage:
        @router.get("/judge-queue", dependencies=[Depends(require_role("judge", "admin"))])
    """

    async def role_checker(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in allowed_roles:
            raise InsufficientRoleError(
                message=f"Access denied. Required role(s): {', '.join(allowed_roles)}. Your role: {current_user.role}"
            )
        return current_user

    return role_checker
