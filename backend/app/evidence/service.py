"""
Nyaya-ZTA Evidence Service
==========================

Business logic for evidence registration, custody tracking, and hash verification.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.cases.repository import CaseRepository
from app.core.exceptions import NotFoundError
from app.core.logging import get_logger
from app.documents.repository import DocumentRepository
from app.evidence.models import EvidenceRecord
from app.evidence.schemas import (
    EvidenceCreateSchema,
    EvidenceResponseSchema,
    EvidenceVerificationResultSchema,
)
from app.evidence.verifier import EvidenceVerifier

logger = get_logger(__name__)


class EvidenceService:
    """Service managing evidence records and custody verification."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.doc_repo = DocumentRepository(db)
        self.case_repo = CaseRepository(db)

    async def create_evidence(self, schema: EvidenceCreateSchema, actor_id: str) -> EvidenceResponseSchema:
        """
        Register a document as formal case evidence with initial custody log.
        """
        doc = await self.doc_repo.get_by_id(schema.document_id)
        if not doc:
            raise NotFoundError(message="Document not found.")

        now = datetime.now(timezone.utc).isoformat()
        initial_custody = [
            {
                "timestamp": now,
                "actor_id": actor_id,
                "action": "evidence_registered",
                "details": f"Registered document '{doc.file_name}' as {schema.evidence_type} evidence",
                "hash": doc.content_hash,
            }
        ]

        evidence = EvidenceRecord(
            document_id=schema.document_id,
            case_id=schema.case_id,
            evidence_type=schema.evidence_type,
            verification_status="pending",
            integrity_hash=doc.content_hash,
            chain_of_custody=initial_custody,
        )
        self.db.add(evidence)
        await self.db.flush()
        await self.db.refresh(evidence)

        logger.info("Registered evidence record", extra={"evidence_id": evidence.id, "hash": doc.content_hash})
        return EvidenceResponseSchema.model_validate(evidence)

    async def verify_evidence(self, evidence_id: str, verifier_id: str) -> EvidenceVerificationResultSchema:
        """
        Execute cryptographic hash check of stored file against recorded evidence hash.
        """
        result_stmt = await self.db.execute(select(EvidenceRecord).where(EvidenceRecord.id == evidence_id))
        evidence = result_stmt.scalar_one_or_none()
        if not evidence:
            raise NotFoundError(message="Evidence record not found.")

        doc = await self.doc_repo.get_by_id(evidence.document_id)
        if not doc:
            raise NotFoundError(message="Associated document file not found.")

        # Run verification check
        ver_result = await EvidenceVerifier.verify_file_integrity(doc.storage_path, evidence.integrity_hash)

        # Update evidence record in DB
        now = datetime.now(timezone.utc)
        evidence.verification_status = ver_result.status
        evidence.verified_by = verifier_id
        evidence.verified_at = now

        # Append to chain of custody
        custody = list(evidence.chain_of_custody)
        custody.append({
            "timestamp": now.isoformat(),
            "actor_id": verifier_id,
            "action": "integrity_verified",
            "status": ver_result.status,
            "computed_hash": ver_result.computed_hash,
        })
        evidence.chain_of_custody = custody
        await self.db.flush()

        return ver_result

    async def list_case_evidence(self, case_id: str) -> list[EvidenceResponseSchema]:
        """List all evidence records for a case."""
        result = await self.db.execute(
            select(EvidenceRecord).where(EvidenceRecord.case_id == case_id).order_by(EvidenceRecord.created_at.desc())
        )
        records = result.scalars().all()
        return [EvidenceResponseSchema.model_validate(r) for r in records]
