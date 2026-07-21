"""
Nyaya-ZTA Auth Router
=====================

REST API endpoints for authentication:
  - POST /api/v1/auth/register
  - POST /api/v1/auth/login
  - POST /api/v1/auth/refresh
  - GET  /api/v1/auth/me
  - PUT  /api/v1/auth/me
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user
from app.auth.models import User
from app.auth.schemas import (
    RefreshTokenSchema,
    TokenResponseSchema,
    UserLoginSchema,
    UserProfileResponse,
    UserProfileUpdateSchema,
    UserRegisterSchema,
)
from app.auth.service import AuthService
from app.db.session import get_db_session

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post(
    "/register",
    response_model=TokenResponseSchema,
    status_code=status.HTTP_201_CREATED,
    summary="Register new user",
    description="Create a new user profile and return access and refresh JWT tokens.",
)
async def register(
    schema: UserRegisterSchema,
    db: AsyncSession = Depends(get_db_session),
) -> TokenResponseSchema:
    service = AuthService(db)
    return await service.register_user(schema)


@router.post(
    "/login",
    response_model=TokenResponseSchema,
    status_code=status.HTTP_200_OK,
    summary="User login",
    description="Authenticate with email and password, returning JWT tokens.",
)
async def login(
    schema: UserLoginSchema,
    db: AsyncSession = Depends(get_db_session),
) -> TokenResponseSchema:
    service = AuthService(db)
    return await service.authenticate_user(schema.email, schema.password)


@router.post(
    "/refresh",
    response_model=TokenResponseSchema,
    status_code=status.HTTP_200_OK,
    summary="Refresh access token",
    description="Exchange a valid refresh token for a new access/refresh token pair.",
)
async def refresh_token(
    schema: RefreshTokenSchema,
    db: AsyncSession = Depends(get_db_session),
) -> TokenResponseSchema:
    service = AuthService(db)
    return await service.refresh_access_token(schema.refresh_token)


@router.get(
    "/me",
    response_model=UserProfileResponse,
    status_code=status.HTTP_200_OK,
    summary="Get current user profile",
    description="Retrieve profile details of the authenticated user.",
)
async def get_my_profile(
    current_user: User = Depends(get_current_user),
) -> UserProfileResponse:
    return UserProfileResponse.model_validate(current_user)


@router.put(
    "/me",
    response_model=UserProfileResponse,
    status_code=status.HTTP_200_OK,
    summary="Update current user profile",
    description="Update profile information for the authenticated user.",
)
async def update_my_profile(
    schema: UserProfileUpdateSchema,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> UserProfileResponse:
    service = AuthService(db)
    return await service.update_user_profile(current_user.id, schema)
