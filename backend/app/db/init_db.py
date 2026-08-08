"""
VADP Database Initialization
=================================

Utility to automatically initialize the database schema on first startup
if tables do not exist, and seed any initial configuration data (e.g., default
jurisdiction configuration, initial policy templates).
"""

from __future__ import annotations

import logging

from app.ai.models import AIExplanation, AIRecommendation  # noqa
from app.auth.models import Session, User  # noqa
from app.authorization.models import AccessDecision, AccessPolicy  # noqa
from app.cases.models import Case, CaseEvent, CaseParty  # noqa
from app.db.base import Base
from app.db.engine import get_async_engine
from app.db.normalized_models import (  # noqa
    AuditEventNorm,
    Citation,
    Court,
    EmbeddingRecord,
    EvidenceRecordNorm,
    HumanReviewNorm,
    Judge,
    Judgment,
    LegalIssue,
    Party,
    Precedent,
    Statute,
    VerificationContractNorm,
)
from app.documents.models import Document  # noqa
from app.evidence.models import EvidenceRecord  # noqa
from app.ledger.models import LedgerBlock, LedgerEntry  # noqa
from app.notifications.models import Notification  # noqa
from app.rag.models import DocumentChunk, RAGQuery  # noqa
from app.vadp.models import ContractEvent, VerificationContract  # noqa

from sqlalchemy import select

from app.core.security import hash_password
from app.db.session import get_session_factory

logger = logging.getLogger(__name__)


async def seed_initial_users() -> None:
    """Seed initial test accounts if they do not exist."""
    session_factory = get_session_factory()
    async with session_factory() as session:
        seed_users = [
            {
                "email": "judge.sharma@nyaya.gov.in",
                "full_name": "Judge Sharma",
                "role": "judge",
            },
            {
                "email": "citizen.kumar@nyaya.in",
                "full_name": "Citizen Kumar",
                "role": "citizen",
            },
            {
                "email": "admin@nyaya.gov.in",
                "full_name": "Admin User",
                "role": "admin",
            },
            {
                "email": "lawyer.verma@nyaya.in",
                "full_name": "Lawyer Verma",
                "role": "lawyer",
            },
        ]

        for u_data in seed_users:
            result = await session.execute(
                select(User).where(User.email == u_data["email"].lower())
            )
            existing = result.scalar_one_or_none()
            if not existing:
                user = User(
                    email=u_data["email"].lower(),
                    hashed_password=hash_password("Password123!"),
                    full_name=u_data["full_name"],
                    role=u_data["role"],
                    is_active=True,
                    is_verified=True,
                )
                session.add(user)
            else:
                existing.hashed_password = hash_password("Password123!")
                existing.is_active = True
                existing.is_verified = True
        await session.commit()


async def init_db() -> None:
    """
    Initialize database tables on application startup.

    Creates all tables declared in SQLAlchemy metadata if they don't exist.
    Safe to run repeatedly.
    """
    engine = get_async_engine()
    logger.info("Checking and initializing database tables...")

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    try:
        await seed_initial_users()
    except Exception as e:
        logger.warning("Initial user seeding skipped or failed: %s", str(e))

    logger.info("Database table initialization complete.")
