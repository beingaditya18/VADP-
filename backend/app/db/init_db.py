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

logger = logging.getLogger(__name__)


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

    logger.info("Database table initialization complete.")
