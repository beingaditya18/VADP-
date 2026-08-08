"""
VADP Configuration Module
==============================

Centralized configuration using pydantic-settings.
All settings are loaded from environment variables with sensible defaults.

Database Architecture:
  - Default: SQLite3 (fully offline, zero setup)
  - Future: PostgreSQL (change DATABASE_URL only)
  - No cloud dependencies. No internet required for database.

Authentication:
  - Custom JWT (python-jose + bcrypt)
  - No external auth provider dependency

Storage:
  - Local filesystem (/backend/uploads/)
  - No cloud storage dependency
"""

from __future__ import annotations

import os
from enum import Enum
from functools import lru_cache
from pathlib import Path
from typing import Any

from pydantic import field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# Determine the backend root directory (where this file's parent is)
BACKEND_DIR = Path(__file__).resolve().parent.parent


class Environment(str, Enum):
    """Application deployment environment."""

    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"
    TESTING = "testing"


class LogLevel(str, Enum):
    """Supported log levels."""

    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.

    All UPPER_CASE attributes map directly to environment variable names.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ── Application ──────────────────────────────────────────
    APP_NAME: str = "VADP"
    APP_VERSION: str = "0.1.0"
    APP_DESCRIPTION: str = (
        "Zero Trust Explainable AI Framework for Secure Judicial Decision Support"
    )
    ENVIRONMENT: Environment = Environment.DEVELOPMENT
    DEBUG: bool = False
    LOG_LEVEL: LogLevel = LogLevel.INFO

    # ── Server ───────────────────────────────────────────────
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    CORS_ORIGINS: str | list[str] = ["http://localhost:3000", "http://localhost:3001"]
    API_PREFIX: str = "/api/v1"

    # ── Database (SQLite by default, PostgreSQL supported) ───
    # Default: SQLite stored at backend/database/nyaya.db
    # To migrate to PostgreSQL, set DATABASE_URL to:
    #   postgresql+asyncpg://nyaya:nyayazta_password@localhost:5432/nyaya_db
    DATABASE_URL: str = f"sqlite+aiosqlite:///{BACKEND_DIR / 'database' / 'nyaya.db'}"
    POSTGRES_USER: str = "nyaya"
    POSTGRES_PASSWORD: str = "nyayazta_password"
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_DB: str = "nyaya_db"
    USE_PGVECTOR: bool = True
    VECTOR_DIMENSION: int = 384
    DB_POOL_SIZE: int = 20
    DB_MAX_OVERFLOW: int = 10
    DB_POOL_TIMEOUT: int = 30
    DB_ECHO: bool = False

    # ── Authentication (Custom JWT) ──────────────────────────
    JWT_SECRET_KEY: str = "change-this-to-a-secure-random-string-in-production"
    JWT_ALGORITHM: str = "ES256"
    JWT_PRIVATE_KEY_PATH: str | None = str(BACKEND_DIR / "signing_keys" / "jwt_key.pem")
    JWT_PUBLIC_KEY_PATH: str | None = str(BACKEND_DIR / "signing_keys" / "jwt_key_pub.pem")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # ── File Storage (Local) ─────────────────────────────────
    UPLOAD_DIR: str = str(BACKEND_DIR / "uploads")
    MAX_UPLOAD_SIZE_MB: int = 50
    FILE_ENCRYPTION_KEY: str = ""
    ALLOWED_FILE_TYPES: str | list[str] = [
        "application/pdf",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "text/plain",
        "image/png",
        "image/jpeg",
        "image/webp",
    ]

    # ── LLM (Provider-Independent) ───────────────────────────
    LLM_PROVIDER: str = "groq"
    LLM_BASE_URL: str = "https://api.groq.com/openai/v1"
    LLM_API_KEY: str = ""
    LLM_MODEL: str = "llama-3.3-70b-versatile"
    LLM_MAX_TOKENS: int = 4096
    LLM_TEMPERATURE: float = 0.1
    LLM_TIMEOUT: int = 60

    # ── RAG & Vector Store Configuration ────────────────────
    VECTOR_STORE_BACKEND: str = "faiss"  # "faiss" | "pgvector" | "qdrant"
    EMBEDDING_MODEL: str = "all-MiniLM-L6-v2"
    EMBEDDING_DIMENSION: int = 384
    FAISS_INDEX_PATH: str = str(BACKEND_DIR / "faiss_indices")
    RAG_TOP_K: int = 5
    RAG_SIMILARITY_THRESHOLD: float = 0.3
    RAG_MAX_CONTEXT_TOKENS: int = 3000
    CHUNK_SIZE: int = 512
    CHUNK_OVERLAP: int = 50

    # ── HSM & Cryptographic Key Management ───────────────────
    HSM_PROVIDER: str = "mock"  # "mock" | "aws_kms" | "azure_kv" | "pkcs11"
    AWS_KMS_KEY_ID: str = ""
    AZURE_KEY_VAULT_URL: str = ""

    # ── Ledger ───────────────────────────────────────────────
    LEDGER_SIGNING_KEY_PATH: str = str(BACKEND_DIR / "signing_keys" / "ledger_key.pem")
    LEDGER_BLOCK_SIZE: int = 50  # entries per block
    LEDGER_AUTO_FINALIZE: bool = True

    # ── Secrets Management ────────────────────────────────────
    SECRETS_PROVIDER: str = "env"  # "env" | "aws" | "vault" | "auto"
    AWS_SECRET_NAME: str = "VADP/production"
    AWS_REGION: str = "us-east-1"
    VAULT_ADDR: str = "http://localhost:8200"
    VAULT_TOKEN: str = ""
    VAULT_SECRET_PATH: str = "VADP/config"
    VAULT_MOUNT_POINT: str = "secret"

    # ── Rate Limiting & Distributed Redis ─────────────────────
    RATE_LIMIT_REQUESTS: int = 100
    RATE_LIMIT_WINDOW_SECONDS: int = 60
    REDIS_URL: str = "redis://localhost:6379/0"

    # ── Monitoring ───────────────────────────────────────────
    HEALTH_CHECK_PATH: str = "/health"
    ENABLE_REQUEST_LOGGING: bool = True

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def parse_cors_origins(cls, v: Any) -> list[str]:
        """Parse CORS origins from comma-separated string or list."""
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",") if origin.strip()]
        return v

    @field_validator("ALLOWED_FILE_TYPES", mode="before")
    @classmethod
    def parse_file_types(cls, v: Any) -> list[str]:
        """Parse allowed file types from comma-separated string or list."""
        if isinstance(v, str):
            return [ft.strip() for ft in v.split(",") if ft.strip()]
        return v

    @field_validator("DATABASE_URL", mode="before")
    @classmethod
    def normalize_database_url(cls, v: str) -> str:
        """
        Normalize database URL for the appropriate async driver.

        - SQLite: ensure sqlite+aiosqlite:// prefix
        - PostgreSQL: ensure postgresql+asyncpg:// prefix
        """
        if not v:
            return f"sqlite+aiosqlite:///{BACKEND_DIR / 'database' / 'nyaya.db'}"

        # PostgreSQL normalization (for future migration)
        if v.startswith("postgres://"):
            return v.replace("postgres://", "postgresql+asyncpg://", 1)
        if v.startswith("postgresql://") and "+asyncpg" not in v:
            return v.replace("postgresql://", "postgresql+asyncpg://", 1)

        return v

    @model_validator(mode="after")
    def ensure_directories_exist(self) -> Settings:
        """Create required directories if they don't exist and load dynamic secrets."""
        # Load dynamic secrets from SecretsFactory if enabled
        if self.SECRETS_PROVIDER != "env":
            try:
                from app.core.secrets import SecretsFactory

                provider = SecretsFactory.get_provider()
                secrets_dict = provider.get_secret_dict()
                if "JWT_SECRET_KEY" in secrets_dict:
                    self.JWT_SECRET_KEY = secrets_dict["JWT_SECRET_KEY"]
                if "LLM_API_KEY" in secrets_dict:
                    self.LLM_API_KEY = secrets_dict["LLM_API_KEY"]
                if "DATABASE_URL" in secrets_dict:
                    self.DATABASE_URL = secrets_dict["DATABASE_URL"]
            except Exception as e:
                import logging

                logging.getLogger(__name__).warning(f"Failed to load dynamic secrets: {e}")

        # Create database directory
        db_url = self.DATABASE_URL
        if "sqlite" in db_url:
            db_path = db_url.replace("sqlite+aiosqlite:///", "").replace("sqlite:///", "")
            db_dir = os.path.dirname(db_path)
            if db_dir:
                os.makedirs(db_dir, exist_ok=True)

        # Create upload directory
        os.makedirs(self.UPLOAD_DIR, exist_ok=True)

        # Create FAISS index directory
        os.makedirs(self.FAISS_INDEX_PATH, exist_ok=True)

        # Create signing keys directory
        signing_dir = os.path.dirname(self.LEDGER_SIGNING_KEY_PATH)
        if signing_dir:
            os.makedirs(signing_dir, exist_ok=True)

        return self

    @property
    def is_sqlite(self) -> bool:
        """Check if the current database is SQLite."""
        return "sqlite" in self.DATABASE_URL

    @property
    def is_postgres(self) -> bool:
        """Check if the current database is PostgreSQL."""
        return "postgresql" in self.DATABASE_URL or "postgres" in self.DATABASE_URL

    @property
    def is_development(self) -> bool:
        return self.ENVIRONMENT == Environment.DEVELOPMENT

    @property
    def is_production(self) -> bool:
        return self.ENVIRONMENT == Environment.PRODUCTION

    @property
    def is_testing(self) -> bool:
        return self.ENVIRONMENT == Environment.TESTING


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """
    Return cached application settings.

    Uses lru_cache to ensure settings are loaded exactly once per process
    and shared across all modules that import this function.
    """
    return Settings()
