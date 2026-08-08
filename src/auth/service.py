"""
VADP Auth Service
======================

Business logic for user registration, authentication, token refresh,
password management, and session handling.
Clean Architecture service layer decoupled from framework and database details.
"""

from __future__ import annotations

import hashlib
from datetime import datetime, timedelta, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.models import Session, User
from app.auth.repository import SessionRepository, UserRepository
from app.auth.schemas import (
    TokenResponseSchema,
    UserProfileResponse,
    UserProfileUpdateSchema,
    UserRegisterSchema,
)
from app.config import get_settings
from app.core.exceptions import (
    AuthenticationError,
    ConflictError,
    NotFoundError,
    TokenExpiredError,
    TokenInvalidError,
)
from app.core.logging import get_logger
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_jwt,
    hash_password,
    verify_password,
)

logger = get_logger(__name__)


class AuthService:
    """Service encapsulating authentication & user management workflows."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.user_repo = UserRepository(db)
        self.session_repo = SessionRepository(db)
        self.settings = get_settings()

    async def register_user(self, schema: UserRegisterSchema) -> TokenResponseSchema:
        """
        Register a new user account and issue JWT credentials.
        """
        # Check if email is taken
        existing_user = await self.user_repo.get_by_email(schema.email)
        if existing_user:
            raise ConflictError(
                message="A user with this email address already exists."
            )

        # Hash password and create User instance
        user = User(
            email=schema.email.lower(),
            hashed_password=hash_password(schema.password),
            full_name=schema.full_name,
            role=schema.role.value,
            bar_number=schema.bar_number,
            court_id=schema.court_id,
            is_active=True,
            is_verified=False,
        )

        created_user = await self.user_repo.create_user(user)
        logger.info(
            "User registered successfully",
            extra={"user_id": created_user.id, "role": created_user.role},
        )

        # Generate tokens and session
        return await self._create_tokens_and_session(created_user)

    async def authenticate_user(self, email: str, password: str) -> TokenResponseSchema:
        """
        Authenticate a user by email and password, issuing fresh tokens.
        """
        user = await self.user_repo.get_by_email(email.lower())
        if not user:
            raise AuthenticationError(message="Invalid email or password.")

        if not user.is_active:
            raise AuthenticationError(
                message="Account is deactivated. Please contact administrator."
            )

        if not verify_password(password, user.hashed_password):
            raise AuthenticationError(message="Invalid email or password.")

        # Update last login timestamp
        await self.user_repo.update_last_login(user.id)
        logger.info("User logged in", extra={"user_id": user.id, "role": user.role})

        return await self._create_tokens_and_session(user)

    async def refresh_access_token(self, refresh_token: str) -> TokenResponseSchema:
        """
        Issue a new access & refresh token pair using a valid refresh token.
        """
        # Decode and validate refresh token
        payload = decode_jwt(refresh_token, expected_type="refresh")
        user_id = payload.get("sub")
        if not user_id:
            raise TokenInvalidError(message="Invalid refresh token payload.")

        user = await self.user_repo.get_by_id(user_id)
        if not user or not user.is_active:
            raise AuthenticationError(message="User account is invalid or inactive.")

        logger.info("Token refreshed", extra={"user_id": user.id})
        return await self._create_tokens_and_session(user)

    async def get_user_profile(self, user_id: str) -> UserProfileResponse:
        """
        Retrieve user profile by ID.
        """
        user = await self.user_repo.get_by_id(user_id)
        if not user:
            raise NotFoundError(message="User not found.")
        return UserProfileResponse.model_validate(user)

    async def update_user_profile(
        self, user_id: str, schema: UserProfileUpdateSchema
    ) -> UserProfileResponse:
        """
        Update profile details for a user.
        """
        updates = schema.model_dump(exclude_unset=True)
        updated_user = await self.user_repo.update_profile(user_id, updates)
        if not updated_user:
            raise NotFoundError(message="User not found.")
        logger.info("User profile updated", extra={"user_id": user_id})
        return UserProfileResponse.model_validate(updated_user)

    async def logout_user(self, token: str) -> None:
        """
        Invalidate/revoke access token upon user logout.
        """
        from app.auth.token_blacklist import TokenBlacklistService

        TokenBlacklistService.blacklist_token(token)
        logger.info("User token blacklisted on logout")

    async def _create_tokens_and_session(self, user: User) -> TokenResponseSchema:
        """Helper to create JWT pair and record active session."""
        access_token = create_access_token(user_id=user.id, role=user.role)
        refresh_token = create_refresh_token(user_id=user.id)

        # Store session with hashed refresh token
        token_hash = hashlib.sha256(refresh_token.encode()).hexdigest()
        expires_at = datetime.now(timezone.utc) + timedelta(
            days=self.settings.REFRESH_TOKEN_EXPIRE_DAYS
        )

        session_obj = Session(
            user_id=user.id,
            refresh_token_hash=token_hash,
            device_info={},
            is_active=True,
            expires_at=expires_at,
        )
        await self.session_repo.create_session(session_obj)

        profile_res = UserProfileResponse.model_validate(user)
        return TokenResponseSchema(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            expires_in=self.settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            user=profile_res,
        )
