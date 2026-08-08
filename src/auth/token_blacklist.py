"""
VADP JWT Token Blacklist Service
======================================

In-memory thread-safe storage service tracking revoked JWT access tokens.
In production environments, this can be backed by Redis TTL sets.
"""

from __future__ import annotations

import time
from typing import Set


class TokenBlacklistService:
    """Singleton/shared service managing revoked JWT signatures/tokens."""

    _blacklisted_tokens: Set[str] = set()

    @classmethod
    def blacklist_token(cls, token: str) -> None:
        """Add raw token or signature to the revocation blacklist."""
        cls._blacklisted_tokens.add(token)

    @classmethod
    def is_blacklisted(cls, token: str) -> bool:
        """Check if a token has been revoked."""
        return token in cls._blacklisted_tokens

    @classmethod
    def clear(cls) -> None:
        """Clear blacklist (for test suite isolation)."""
        cls._blacklisted_tokens.clear()
