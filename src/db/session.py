"""
VADP Database Session Management
======================================

Provides async session factories and FastAPI dependency injection
for database sessions. Each request gets its own session with
automatic commit/rollback on success/failure.

Usage in FastAPI routes:
    from app.db.session import get_db_session

    @router.get("/items")
    async def list_items(db: AsyncSession = Depends(get_db_session)):
        result = await db.execute(select(Item))
        return result.scalars().all()
"""

from __future__ import annotations

from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
)

from app.db.engine import get_async_engine

_session_factory: async_sessionmaker[AsyncSession] | None = None


def get_session_factory() -> async_sessionmaker[AsyncSession]:
    """
    Return the shared async session factory.

    Creates the factory lazily on first call, bound to the async engine.
    The factory is reused for the lifetime of the application process.
    """
    global _session_factory

    if _session_factory is not None:
        return _session_factory

    engine = get_async_engine()

    _session_factory = async_sessionmaker(
        bind=engine,
        class_=AsyncSession,
        expire_on_commit=False,  # prevent lazy-load issues after commit
        autocommit=False,
        autoflush=False,
    )

    return _session_factory


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """
    FastAPI dependency that yields an async database session.

    The session is automatically committed on successful completion
    of the request, or rolled back if an exception occurs.

    Yields:
        AsyncSession: A scoped database session for the current request.
    """
    factory = get_session_factory()

    async with factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
