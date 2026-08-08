"""
VADP Evidence Service
==========================

Business logic for evidence registration, custody tracking, hash verification,
blockchain anchoring, and BSA 2023 Section 63(4) certificate generation.
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
from app.evidence.blockchain_anchor import (
    BlockchainAnchorEngine,
    BlockchainTransactionReceipt,
    BSACertificate63,
)
from app.evidence.models import EvidenceRecord
from app.evidence.schemas import (
    EvidenceCreateSchema,
    EvidenceResponseSchema,
    EvidenceVerificationResultSchema,
)
from app.evidence.verifier import EvidenceVerifier

logger = get_logger(__name__)


class EvidenceService:
    """Service managing evidence records, custody verification, and blockchain anchoring."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.doc_repo = DocumentRepository(db)
        self.case_repo = CaseRepository(db)

    async def create_evidence(
        self, schema: EvidenceCreateSchema, actor_id: str
    ) -> EvidenceResponseSchema:
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

        logger.info(
            "Registered evidence record",
            extra={"evidence_id": evidence.id, "hash": doc.content_hash},
        )
        return EvidenceResponseSchema.model_validate(evidence)

    async def verify_evidence(
        self, evidence_id: str, verifier_id: str
    ) -> EvidenceVerificationResultSchema:
        """
        Execute cryptographic hash check of stored file against recorded evidence hash.
        """
        result_stmt = await self.db.execute(
            select(EvidenceRecord).where(EvidenceRecord.id == evidence_id)
        )
        evidence = result_stmt.scalar_one_or_none()
        if not evidence:
            raise NotFoundError(message="Evidence record not found.")

        doc = await self.doc_repo.get_by_id(evidence.document_id)
        if not doc:
            raise NotFoundError(message="Associated document file not found.")

        # Run verification check
        ver_result = await EvidenceVerifier.verify_file_integrity(
            doc.storage_path, evidence.integrity_hash
        )

        # Update evidence record in DB
        now = datetime.now(timezone.utc)
        evidence.verification_status = ver_result.status
        evidence.verified_by = verifier_id
        evidence.verified_at = now

        # Append to chain of custody
        custody = list(evidence.chain_of_custody)
        custody.append(
            {
                "timestamp": now.isoformat(),
                "actor_id": verifier_id,
                "action": "integrity_verified",
                "status": ver_result.status,
                "computed_hash": ver_result.computed_hash,
            }
        )
        evidence.chain_of_custody = custody
        await self.db.flush()

        return ver_result

    async def anchor_to_blockchain(
        self, evidence_id: str
    ) -> BlockchainTransactionReceipt:
        """
        Anchor an evidence record to the blockchain ledger.
        """
        result_stmt = await self.db.execute(
            select(EvidenceRecord).where(EvidenceRecord.id == evidence_id)
        )
        evidence = result_stmt.scalar_one_or_none()
        if not evidence:
            raise NotFoundError(message="Evidence record not found.")

        receipt = BlockchainAnchorEngine.anchor_to_blockchain(
            evidence_id=evidence.id,
            integrity_hash=evidence.integrity_hash,
        )

        custody = list(evidence.chain_of_custody)
        custody.append(
            {
                "timestamp": receipt.anchored_at_iso,
                "action": "blockchain_anchored",
                "tx_hash": receipt.tx_hash,
                "block_number": receipt.block_number,
            }
        )
        evidence.chain_of_custody = custody
        await self.db.flush()

        logger.info(
            "Anchored evidence to blockchain",
            extra={"evidence_id": evidence.id, "tx_hash": receipt.tx_hash},
        )
        return receipt

    async def generate_bsa_certificate(self, evidence_id: str) -> BSACertificate63:
        """
        Generate Section 63(4) BSA 2023 Electronic Evidence Certificate.
        """
        result_stmt = await self.db.execute(
            select(EvidenceRecord).where(EvidenceRecord.id == evidence_id)
        )
        evidence = result_stmt.scalar_one_or_none()
        if not evidence:
            raise NotFoundError(message="Evidence record not found.")

        receipt = BlockchainAnchorEngine.anchor_to_blockchain(
            evidence_id=evidence.id,
            integrity_hash=evidence.integrity_hash,
        )

        cert = BlockchainAnchorEngine.generate_bsa_certificate(
            case_id=evidence.case_id,
            evidence_id=evidence.id,
            document_id=evidence.document_id,
            evidence_type=evidence.evidence_type,
            integrity_hash=evidence.integrity_hash,
        )
        cert.anchored_tx_hash = receipt.tx_hash
        return cert

    async def list_case_evidence(self, case_id: str) -> list[EvidenceResponseSchema]:
        """List all evidence records for a case."""
        result = await self.db.execute(
            select(EvidenceRecord)
            .where(EvidenceRecord.case_id == case_id)
            .order_by(EvidenceRecord.created_at.desc())
        )
        records = result.scalars().all()
        return [EvidenceResponseSchema.model_validate(r) for r in records]
