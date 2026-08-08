"""
Alembic Migration Environment
==============================

Configures Alembic to use async SQLAlchemy with the VADP database.
The database URL is loaded from application settings (environment variables),
NOT from alembic.ini — this ensures a single source of truth.

Supports both:
  - Online migrations (connected to a live database)
  - Offline migrations (generates SQL scripts without a database connection)
"""

from __future__ import annotations

import asyncio
from logging.config import fileConfig

from alembic import context
from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config, create_async_engine

from app.config import get_settings
from app.db.base import Base

# Import all models here so Alembic can detect them for autogeneration.
# As modules are built, their models will be imported here:
# from app.auth.models import *       # noqa: F401, F403
# from app.cases.models import *      # noqa: F401, F403
# from app.documents.models import *  # noqa: F401, F403
# from app.evidence.models import *   # noqa: F401, F403
# from app.ai.models import *         # noqa: F401, F403
# from app.ledger.models import *     # noqa: F401, F403
# from app.zero_trust.models import * # noqa: F401, F403

# Alembic Config object
config = context.config

# Set up Python logging from alembic.ini
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Target metadata for autogeneration
target_metadata = Base.metadata


def get_database_url() -> str:
    """Get the database URL from application settings."""
    settings = get_settings()
    url = settings.DATABASE_URL
    if not url:
        raise ValueError(
            "DATABASE_URL is not set. "
            "Configure it in your .env file or environment variables."
        )
    return url


def run_migrations_offline() -> None:
    """
    Run migrations in 'offline' mode.

    Generates SQL scripts based on the target metadata without
    requiring a live database connection. Useful for generating
    migration SQL for review before applying.
    """
    url = get_database_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
        compare_server_default=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    """Run migrations using a synchronous connection wrapper."""
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        compare_type=True,
        compare_server_default=True,
    )

    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    """
    Run migrations in 'online' mode using an async engine.

    Creates an async engine, connects, and runs migrations
    within a synchronous callback on the connection.
    """
    url = get_database_url()
    connectable = create_async_engine(
        url,
        poolclass=pool.NullPool,
        connect_args={"statement_cache_size": 0},
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


def run_migrations_online() -> None:
    """Entry point for online migrations — runs the async migration loop."""
    asyncio.run(run_async_migrations())


# Determine which mode to run in
if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
