"""
VADP Core Security
========================

Custom JWT authentication with access tokens and refresh tokens.
No external auth provider dependency — works completely offline.

Features:
  - Access tokens (short-lived, 30 min default)
  - Refresh tokens (long-lived, 7 days default)
  - bcrypt password hashing
  - OAuth2 bearer scheme for FastAPI
  - Token payload includes user ID, role, and token type
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext

from app.config import get_settings
from app.core.exceptions import TokenExpiredError, TokenInvalidError
from app.core.logging import get_logger

logger = get_logger(__name__)

# OAuth2 bearer scheme — extracts token from Authorization header
oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="/api/v1/auth/login",
    auto_error=False,  # We handle missing tokens ourselves for better error messages
)

# Password hashing context (bcrypt)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


# ── Password Hashing ─────────────────────────────────────────


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a plaintext password against a bcrypt hash.

    Args:
        plain_password: The plaintext password to verify.
        hashed_password: The bcrypt hash to compare against.

    Returns:
        True if the password matches, False otherwise.
    """
    return pwd_context.verify(plain_password, hashed_password)


def hash_password(password: str) -> str:
    """
    Hash a plaintext password using bcrypt.

    Args:
        password: The plaintext password to hash.

    Returns:
        The bcrypt hash string.
    """
    return pwd_context.hash(password)


# ── JWT Token Creation ────────────────────────────────────────


from pathlib import Path

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ec


def _ensure_jwt_keypair() -> tuple[str, str]:
    """Ensure ECDSA keypair exists for ES256, returning (private_pem, public_pem)."""
    settings = get_settings()
    root_dir = Path(__file__).resolve().parent.parent.parent
    priv_path = Path(settings.JWT_PRIVATE_KEY_PATH) if settings.JWT_PRIVATE_KEY_PATH else (root_dir / "signing_keys" / "jwt_key.pem")
    pub_path = Path(settings.JWT_PUBLIC_KEY_PATH) if settings.JWT_PUBLIC_KEY_PATH else (root_dir / "signing_keys" / "jwt_key_pub.pem")

    if not priv_path.exists() or not pub_path.exists():
        priv_path.parent.mkdir(parents=True, exist_ok=True)
        private_key = ec.generate_private_key(ec.SECP256R1())
        priv_pem = private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption(),
        ).decode("utf-8")
        pub_pem = private_key.public_key().public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo,
        ).decode("utf-8")
        priv_path.write_text(priv_pem, encoding="utf-8")
        pub_path.write_text(pub_pem, encoding="utf-8")
        logger.info("Generated new ECDSA keypair for JWT signing (ES256)", extra={"priv_path": str(priv_path)})
        return priv_pem, pub_pem

    return priv_path.read_text(encoding="utf-8"), pub_path.read_text(encoding="utf-8")


def _get_signing_key() -> str:
    """Return key for JWT encoding (private PEM if RS256/ES256, else secret string)."""
    settings = get_settings()
    if settings.JWT_ALGORITHM == "ES256":
        priv_pem, _ = _ensure_jwt_keypair()
        return priv_pem
    if settings.JWT_ALGORITHM == "RS256" and settings.JWT_PRIVATE_KEY_PATH:
        key_path = Path(settings.JWT_PRIVATE_KEY_PATH)
        if key_path.exists():
            return key_path.read_text(encoding="utf-8")
    return settings.JWT_SECRET_KEY


def _get_verifying_key() -> str:
    """Return key for JWT decoding (public PEM if RS256/ES256, else secret string)."""
    settings = get_settings()
    if settings.JWT_ALGORITHM == "ES256":
        _, pub_pem = _ensure_jwt_keypair()
        return pub_pem
    if settings.JWT_ALGORITHM == "RS256" and settings.JWT_PUBLIC_KEY_PATH:
        key_path = Path(settings.JWT_PUBLIC_KEY_PATH)
        if key_path.exists():
            return key_path.read_text(encoding="utf-8")
    return settings.JWT_SECRET_KEY


def create_access_token(
    user_id: str,
    role: str,
    extra_claims: dict[str, Any] | None = None,
) -> str:
    """
    Create a short-lived JWT access token.
    """
    settings = get_settings()
    now = datetime.now(timezone.utc)
    expire = now + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

    payload: dict[str, Any] = {
        "sub": user_id,
        "role": role,
        "type": "access",
        "iat": now,
        "exp": expire,
    }
    if extra_claims:
        payload.update(extra_claims)

    key = _get_signing_key()
    return jwt.encode(payload, key, algorithm=settings.JWT_ALGORITHM)


def create_refresh_token(user_id: str) -> str:
    """
    Create a long-lived JWT refresh token.
    """
    settings = get_settings()
    now = datetime.now(timezone.utc)
    expire = now + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)

    payload: dict[str, Any] = {
        "sub": user_id,
        "type": "refresh",
        "iat": now,
        "exp": expire,
    }

    key = _get_signing_key()
    return jwt.encode(payload, key, algorithm=settings.JWT_ALGORITHM)


# ── JWT Token Validation ─────────────────────────────────────


def decode_jwt(token: str, expected_type: str = "access") -> dict[str, Any]:
    """
    Decode and validate a JWT token supporting symmetric and asymmetric keys.
    """
    settings = get_settings()
    key = _get_verifying_key()

    try:
        payload = jwt.decode(
            token,
            key,
            algorithms=[settings.JWT_ALGORITHM],
            options={"verify_exp": True},
        )
    except JWTError as e:
        error_str = str(e).lower()
        if "expired" in error_str:
            logger.info("JWT token expired", extra={"error": str(e)})
            raise TokenExpiredError()
        logger.warning("JWT validation failed", extra={"error": str(e)})
        raise TokenInvalidError(detail=str(e))

    # Validate required claims
    if "sub" not in payload:
        raise TokenInvalidError(
            message="Token is missing user identity.",
            detail="The 'sub' claim is required but was not found in the token.",
        )

    # Validate token type
    token_type = payload.get("type", "access")
    if token_type != expected_type:
        raise TokenInvalidError(
            message=f"Invalid token type. Expected '{expected_type}', got '{token_type}'.",
        )

    return payload


def extract_user_id_from_token(token: str) -> str:
    """
    Extract the user ID (sub claim) from an access token.

    Args:
        token: The JWT string.

    Returns:
        The user ID string from the token's 'sub' claim.
    """
    payload = decode_jwt(token, expected_type="access")
    return payload["sub"]


from fastapi import Depends, Request

async def get_token(
    request: Request,
    token: str | None = Depends(oauth2_scheme),
) -> str:
    """
    FastAPI dependency that extracts and validates the bearer token.
    Extracts from 'access_token' httpOnly cookie first, with fallback to Authorization header.

    Returns the raw token string for further processing by auth dependencies.

    Raises:
        TokenInvalidError: If no token is provided.
    """
    # 1. Explicit Authorization header takes precedence (allows header overrides)
    if token:
        return token

    # 2. httpOnly cookie fallback (for browser requests)
    cookie_token = request.cookies.get("access_token")
    if cookie_token:
        return cookie_token

    raise TokenInvalidError(
        message="Authentication required.",
        detail="No token found in Authorization header or access_token cookie.",
    )
