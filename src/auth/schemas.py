"""
VADP Auth Pydantic Schemas
===============================

Input validation and output serialization schemas for authentication endpoints.
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator


class UserRoleEnum(str, Enum):
    """Supported user roles in VADP system."""

    CITIZEN = "citizen"
    LAWYER = "lawyer"
    JUDGE = "judge"
    ADMIN = "admin"
    COURT_CLERK = "court_clerk"
    REGISTRAR = "registrar"


class UserRegisterSchema(BaseModel):
    """Request schema for user registration."""

    email: EmailStr
    password: str = Field(
        ...,
        min_length=8,
        max_length=128,
        description="Password must be at least 8 characters.",
    )
    full_name: str = Field(..., min_length=2, max_length=255)
    role: UserRoleEnum = Field(default=UserRoleEnum.CITIZEN)
    bar_number: str | None = Field(
        default=None, max_length=100, description="Bar registration number for lawyers."
    )
    court_id: str | None = Field(
        default=None, description="Court ID assignment for judges and clerks."
    )

    @field_validator("bar_number")
    @classmethod
    def validate_bar_number(cls, v: str | None, info: Any) -> str | None:
        role = info.data.get("role")
        if role == UserRoleEnum.LAWYER and not v:
            raise ValueError("Bar number is required for lawyer registration.")
        return v


class UserLoginSchema(BaseModel):
    """Request schema for user login."""

    email: EmailStr
    password: str


class RefreshTokenSchema(BaseModel):
    """Request schema for token refresh."""

    refresh_token: str


class UserProfileResponse(BaseModel):
    """Response schema for user profile."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    email: EmailStr
    full_name: str
    role: UserRoleEnum
    bar_number: str | None = None
    court_id: str | None = None
    is_active: bool
    is_verified: bool
    last_login_at: datetime | None = None
    created_at: datetime
    updated_at: datetime


class UserProfileUpdateSchema(BaseModel):
    """Request schema for profile updates."""

    full_name: str | None = Field(default=None, min_length=2, max_length=255)
    bar_number: str | None = Field(default=None, max_length=100)
    court_id: str | None = Field(default=None)


class TokenResponseSchema(BaseModel):
    """Response schema returned upon successful authentication."""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int  # Seconds until access token expires
    user: UserProfileResponse
