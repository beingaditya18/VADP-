"""
VADP Auth Router
=====================

REST API endpoints for authentication:
  - POST /api/v1/auth/register
  - POST /api/v1/auth/login
  - POST /api/v1/auth/refresh
  - GET  /api/v1/auth/me
  - PUT  /api/v1/auth/me
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, Response, status
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
from app.config import get_settings
from app.core.security import get_token
from app.db.session import get_db_session

router = APIRouter(prefix="/auth", tags=["auth"])


def _set_auth_cookies(response: Response, token_data: TokenResponseSchema) -> None:
    settings = get_settings()
    response.set_cookie(
        key="access_token",
        value=token_data.access_token,
        httponly=True,
        samesite="lax",
        secure=settings.is_production,
        max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        path="/",
    )
    if token_data.refresh_token:
        response.set_cookie(
            key="refresh_token",
            value=token_data.refresh_token,
            httponly=True,
            samesite="lax",
            secure=settings.is_production,
            max_age=settings.REFRESH_TOKEN_EXPIRE_DAYS * 86400,
            path="/",
        )


def _clear_auth_cookies(response: Response) -> None:
    response.delete_cookie("access_token", path="/")
    response.delete_cookie("refresh_token", path="/")


@router.post(
    "/logout",
    status_code=status.HTTP_200_OK,
    summary="User logout",
    description="Revoke the active access token, rendering it invalid for future requests.",
)
async def logout(
    response: Response,
    token: str = Depends(get_token),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> dict[str, str]:
    service = AuthService(db)
    await service.logout_user(token)
    _clear_auth_cookies(response)
    return {"message": "Successfully logged out and revoked token."}


@router.post(
    "/register",
    response_model=TokenResponseSchema,
    status_code=status.HTTP_201_CREATED,
    summary="Register new user",
    description="Create a new user profile and return access and refresh JWT tokens.",
)
async def register(
    schema: UserRegisterSchema,
    response: Response,
    db: AsyncSession = Depends(get_db_session),
) -> TokenResponseSchema:
    service = AuthService(db)
    token_data = await service.register_user(schema)
    _set_auth_cookies(response, token_data)
    return token_data


@router.post(
    "/login",
    response_model=TokenResponseSchema,
    status_code=status.HTTP_200_OK,
    summary="User login",
    description="Authenticate with email and password, returning JWT tokens.",
)
async def login(
    schema: UserLoginSchema,
    response: Response,
    db: AsyncSession = Depends(get_db_session),
) -> TokenResponseSchema:
    service = AuthService(db)
    token_data = await service.authenticate_user(schema.email, schema.password)
    _set_auth_cookies(response, token_data)
    return token_data


@router.post(
    "/refresh",
    response_model=TokenResponseSchema,
    status_code=status.HTTP_200_OK,
    summary="Refresh access token",
    description="Exchange a valid refresh token for a new access/refresh token pair.",
)
async def refresh_token(
    schema: RefreshTokenSchema,
    response: Response,
    db: AsyncSession = Depends(get_db_session),
) -> TokenResponseSchema:
    service = AuthService(db)
    token_data = await service.refresh_access_token(schema.refresh_token)
    _set_auth_cookies(response, token_data)
    return token_data


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
