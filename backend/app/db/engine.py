"""
Nyaya-ZTA Database Engine
=========================

Async SQLAlchemy engine supporting both SQLite (default) and PostgreSQL.

SQLite-specific configuration:
  - WAL mode for concurrent read performance
  - Foreign key enforcement (disabled by default in SQLite)
  - No connection pooling (SQLite handles this internally)

PostgreSQL-specific configuration:
  - Connection pooling with configurable pool size
  - Statement cache disabled for pgbouncer compatibility

The engine is created lazily on first use and reused for the
lifetime of the application process.

Usage:
    from app.db.engine import get_async_engine

    engine = get_async_engine()
"""

from __future__ import annotations

import logging

from sqlalchemy import event, text
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine

from app.config import get_settings

logger = logging.getLogger(__name__)

_engine: AsyncEngine | None = None


def _configure_sqlite_connection(dbapi_connection, connection_record) -> None:  # noqa: ANN001
    """
    Configure SQLite connections on checkout.

    Enables:
      - WAL mode (better concurrent read performance)
      - Foreign key enforcement (off by default in SQLite)
      - Synchronous NORMAL (good balance of safety and speed)
      - Journal size limit (prevent unbounded WAL growth)
    """
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA journal_mode=WAL")
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.execute("PRAGMA synchronous=NORMAL")
    cursor.execute("PRAGMA journal_size_limit=67108864")  # 64MB
    cursor.execute("PRAGMA cache_size=-64000")  # 64MB cache
    cursor.close()


def get_async_engine() -> AsyncEngine:
    """
    Return the shared async engine instance.

    Creates the engine lazily on first call using current settings.
    Automatically detects SQLite vs PostgreSQL and applies the
    appropriate configuration.

    Returns:
        AsyncEngine: SQLAlchemy async engine.

    Raises:
        ValueError: If DATABASE_URL is not configured.
    """
    global _engine

    if _engine is not None:
        return _engine

    settings = get_settings()

    if not settings.DATABASE_URL:
        raise ValueError(
            "DATABASE_URL is not configured. "
            "Set the DATABASE_URL environment variable. "
            "Default: sqlite+aiosqlite:///./database/nyaya.db"
        )

    if settings.is_sqlite:
        # SQLite: no connection pool (StaticPool for single-file DB)
        _engine = create_async_engine(
            settings.DATABASE_URL,
            echo=settings.DB_ECHO,
            connect_args={"check_same_thread": False},
        )
        # Register SQLite PRAGMA configuration
        event.listen(
            _engine.sync_engine,
            "connect",
            _configure_sqlite_connection,
        )
        logger.info("Database engine created: SQLite (WAL mode, FK enabled)")

    else:
        # PostgreSQL: connection pooling with configurable limits
        _engine = create_async_engine(
            settings.DATABASE_URL,
            pool_size=settings.DB_POOL_SIZE,
            max_overflow=settings.DB_MAX_OVERFLOW,
            pool_timeout=settings.DB_POOL_TIMEOUT,
            pool_pre_ping=True,
            echo=settings.DB_ECHO,
            connect_args={
                "statement_cache_size": 0,  # pgbouncer compatibility
            },
        )
        logger.info("Database engine created: PostgreSQL (pool_size=%d)", settings.DB_POOL_SIZE)

    return _engine


async def dispose_engine() -> None:
    """
    Dispose the engine and close all connections.

    Called during application shutdown to cleanly release database resources.
    """
    global _engine
    if _engine is not None:
        await _engine.dispose()
        _engine = None
        logger.info("Database engine disposed")
