"""
VADP Evidence Provenance Unit Tests
========================================

Unit tests for EvidenceProvenanceEngine.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock

from app.evidence.provenance import (
    EvidenceChainVerificationResult,
    EvidenceProvenanceEngine,
)
from app.vadp.schemas import EvidenceProvenanceItem


class TestEvidenceProvenanceEngine:
    """Test evidence provenance extraction and chain verification."""

    @pytest.mark.asyncio
    async def test_get_case_evidence_provenance_empty(self):
        db_mock = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        db_mock.execute.return_value = mock_result

        engine = EvidenceProvenanceEngine(db_mock)
        items = await engine.get_case_evidence_provenance("case-123")
        assert items == []

    @pytest.mark.asyncio
    async def test_evidence_summary(self):
        db_mock = AsyncMock()
        rec1 = MagicMock(verification_status="verified")
        rec2 = MagicMock(verification_status="pending")
        rec3 = MagicMock(verification_status="tampered")

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [rec1, rec2, rec3]
        db_mock.execute.return_value = mock_result

        engine = EvidenceProvenanceEngine(db_mock)
        summary = await engine.get_evidence_summary("case-123")

        assert summary["total"] == 3
        assert summary["verified"] == 1
        assert summary["pending"] == 1
        assert summary["tampered"] == 1
