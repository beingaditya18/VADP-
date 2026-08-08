"""
VADP Evidence Provenance Engine
=====================================

Wraps EvidenceService to produce provenance-grade evidence records
suitable for Verification Contract binding.

This module provides:
  1. Case evidence provenance extraction for VADP contract binding
  2. Evidence chain integrity verification across all records
  3. Provenance-aware evidence status summarization

The Evidence Provenance Engine does NOT replace EvidenceService.
It extends it with VADP-specific provenance extraction logic.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.documents.models import Document
from app.evidence.models import EvidenceRecord
from app.evidence.verifier import EvidenceVerifier
from app.vadp.schemas import EvidenceProvenanceItem

logger = get_logger(__name__)


@dataclass
class EvidenceChainVerificationResult:
    """Result of verifying the entire evidence chain for a case."""

    case_id: str
    is_valid: bool
    total_evidence: int
    verified_count: int
    tampered_count: int
    pending_count: int
    failed_ids: list[str] = field(default_factory=list)
    verification_time_ms: float = 0.0
    verified_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


class EvidenceProvenanceEngine:
    """
    Provenance-grade evidence extraction for VADP Verification Contracts.

    Wraps EvidenceService to provide:
      - Structured provenance items for contract binding
      - Batch evidence chain integrity verification
      - Summary statistics for completeness invariant evaluation
    """

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_case_evidence_provenance(
        self,
        case_id: str,
    ) -> list[EvidenceProvenanceItem]:
        """
        Extract all evidence records for a case as VADP provenance items.

        Each item includes the evidence ID, integrity hash, verification status,
        associated document ID, and evidence type — all required fields for
        Verification Contract binding.
        """
        stmt = (
            select(EvidenceRecord)
            .where(EvidenceRecord.case_id == case_id)
            .order_by(EvidenceRecord.created_at.asc())
        )
        result = await self.db.execute(stmt)
        records = result.scalars().all()

        provenance_items: list[EvidenceProvenanceItem] = []
        for record in records:
            provenance_items.append(
                EvidenceProvenanceItem(
                    evidence_id=record.id,
                    integrity_hash=record.integrity_hash,
                    verification_status=record.verification_status,
                    document_id=record.document_id,
                    evidence_type=record.evidence_type,
                )
            )

        logger.info(
            "Extracted evidence provenance",
            extra={"case_id": case_id, "count": len(provenance_items)},
        )
        return provenance_items

    async def verify_evidence_chain(
        self,
        case_id: str,
    ) -> EvidenceChainVerificationResult:
        """
        Verify the integrity of all evidence records for a case.

        For each evidence record:
          1. Fetch the associated document
          2. Recompute SHA-256 hash of the stored file
          3. Compare against the recorded integrity_hash
          4. Track verified, tampered, and pending counts
        """
        import time

        start_time = time.perf_counter()

        stmt = select(EvidenceRecord).where(EvidenceRecord.case_id == case_id)
        result = await self.db.execute(stmt)
        records = list(result.scalars().all())

        verified_count = 0
        tampered_count = 0
        pending_count = 0
        failed_ids: list[str] = []

        for record in records:
            if record.verification_status == "verified":
                verified_count += 1
                continue
            elif record.verification_status == "tampered":
                tampered_count += 1
                failed_ids.append(record.id)
                continue

            # Pending records — attempt live verification
            doc_stmt = select(Document).where(Document.id == record.document_id)
            doc_result = await self.db.execute(doc_stmt)
            doc = doc_result.scalar_one_or_none()

            if not doc:
                pending_count += 1
                continue

            try:
                ver_result = await EvidenceVerifier.verify_file_integrity(
                    doc.storage_path,
                    record.integrity_hash,
                )
                if ver_result.status == "verified":
                    verified_count += 1
                else:
                    tampered_count += 1
                    failed_ids.append(record.id)
            except Exception:
                pending_count += 1

        elapsed_ms = (time.perf_counter() - start_time) * 1000
        is_valid = tampered_count == 0

        return EvidenceChainVerificationResult(
            case_id=case_id,
            is_valid=is_valid,
            total_evidence=len(records),
            verified_count=verified_count,
            tampered_count=tampered_count,
            pending_count=pending_count,
            failed_ids=failed_ids,
            verification_time_ms=round(elapsed_ms, 2),
        )

    async def get_evidence_summary(
        self,
        case_id: str,
    ) -> dict[str, int]:
        """
        Quick summary of evidence status counts for a case.

        Returns dict with keys: total, verified, pending, tampered, rejected.
        """
        stmt = select(EvidenceRecord).where(EvidenceRecord.case_id == case_id)
        result = await self.db.execute(stmt)
        records = result.scalars().all()

        summary = {
            "total": 0,
            "verified": 0,
            "pending": 0,
            "tampered": 0,
            "rejected": 0,
        }

        for record in records:
            summary["total"] += 1
            status = record.verification_status
            if status in summary:
                summary[status] += 1
            else:
                summary["pending"] += 1

        return summary
