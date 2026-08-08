"""
VADP PDF Forensic Verifier
===============================

Advanced PDF forensic verification engine for judicial & administrative evidence inspection.
Checks:
  1. SHA-256 Hash Matching against Merkle Audit Ledger / Expected State
  2. Structural Revision Analysis (Multiple EOF trailer detection for incremental edits)
  3. Metadata Inspection (Author, Producer, Creation vs Modification Timestamps)
  4. Embedded Script & Malicious Payload Detection
  5. Authenticity Confidence Scoring (0-100%) and Tamper Risk Level
"""

from __future__ import annotations

import hashlib
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import aiofiles
from pydantic import BaseModel, Field


class PDFMetadataInfo(BaseModel):
    title: str | None = None
    author: str | None = None
    producer: str | None = None
    creator: str | None = None
    creation_date: str | None = None
    mod_date: str | None = None
    page_count: int = 1


class PDFTamperAnomaly(BaseModel):
    code: str
    severity: str  # 'LOW', 'MEDIUM', 'HIGH', 'CRITICAL'
    description: str


class ForensicPDFResult(BaseModel):
    is_valid: bool
    status: str  # 'GENUINE', 'SUSPICIOUS', 'TAMPERED'
    authenticity_score: float  # 0.0 to 100.0
    computed_hash: str
    expected_hash: str | None = None
    hash_matched: bool
    metadata: PDFMetadataInfo
    revision_count: int
    anomalies: list[PDFTamperAnomaly] = Field(default_factory=list)
    verification_time: datetime
    summary: str


class PDFVerifierEngine:
    """Forensic PDF Verification Engine."""

    @staticmethod
    async def analyze_pdf(
        file_path: str,
        expected_hash: str | None = None,
    ) -> ForensicPDFResult:
        now = datetime.now(timezone.utc)
        path = Path(file_path)

        if not path.exists():
            return ForensicPDFResult(
                is_valid=False,
                status="TAMPERED",
                authenticity_score=0.0,
                computed_hash="FILE_NOT_FOUND",
                expected_hash=expected_hash,
                hash_matched=False,
                metadata=PDFMetadataInfo(),
                revision_count=0,
                anomalies=[
                    PDFTamperAnomaly(
                        code="FILE_MISSING",
                        severity="CRITICAL",
                        description="Target PDF file does not exist on disk.",
                    )
                ],
                verification_time=now,
                summary="CRITICAL: PDF evidence file was missing or unreadable.",
            )

        # 1. Compute SHA-256 Hash
        sha256 = hashlib.sha256()
        async with aiofiles.open(file_path, "rb") as f:
            content = await f.read()
            sha256.update(content)
        computed_hash = sha256.hexdigest()

        hash_matched = True
        if expected_hash:
            hash_matched = computed_hash.lower() == expected_hash.lower()

        anomalies: list[PDFTamperAnomaly] = []
        score = 100.0

        # Check Hash mismatch
        if expected_hash and not hash_matched:
            score -= 60.0
            anomalies.append(
                PDFTamperAnomaly(
                    code="HASH_MISMATCH",
                    severity="CRITICAL",
                    description="SHA-256 content hash does not match recorded Merkle ledger entry!",
                )
            )

        # 2. Check PDF Header Validity
        if not content.startswith(b"%PDF-"):
            score -= 50.0
            anomalies.append(
                PDFTamperAnomaly(
                    code="INVALID_HEADER",
                    severity="CRITICAL",
                    description="File header does not begin with valid %PDF- magic bytes.",
                )
            )

        # 3. Analyze Revision Count (%EOF markers)
        eof_matches = re.findall(rb"%%EOF", content)
        revision_count = max(1, len(eof_matches))
        if revision_count > 1:
            score -= 15.0 * (revision_count - 1)
            anomalies.append(
                PDFTamperAnomaly(
                    code="MULTIPLE_REVISIONS",
                    severity="MEDIUM",
                    description=f"Detected {revision_count} incremental PDF revisions (possible post-filing edit or redaction).",
                )
            )

        # 4. Check for embedded JavaScript / OpenAction (potential tamper payload)
        if re.search(rb"/JavaScript|/JS\b", content, re.IGNORECASE):
            score -= 20.0
            anomalies.append(
                PDFTamperAnomaly(
                    code="EMBEDDED_JS",
                    severity="HIGH",
                    description="PDF contains active embedded JavaScript scripts.",
                )
            )

        if re.search(rb"/AA\b|/OpenAction\b", content, re.IGNORECASE):
            score -= 10.0
            anomalies.append(
                PDFTamperAnomaly(
                    code="AUTOMATED_ACTION",
                    severity="MEDIUM",
                    description="PDF contains automated triggers (OpenAction/AA).",
                )
            )

        # 5. Extract Metadata using Regex
        metadata = PDFMetadataInfo()

        title_match = re.search(rb"/Title\s*\((.*?)\)", content)
        if title_match:
            metadata.title = title_match.group(1).decode("latin1", errors="ignore")

        author_match = re.search(rb"/Author\s*\((.*?)\)", content)
        if author_match:
            metadata.author = author_match.group(1).decode("latin1", errors="ignore")

        producer_match = re.search(rb"/Producer\s*\((.*?)\)", content)
        if producer_match:
            metadata.producer = producer_match.group(1).decode(
                "latin1", errors="ignore"
            )

        creator_match = re.search(rb"/Creator\s*\((.*?)\)", content)
        if creator_match:
            metadata.creator = creator_match.group(1).decode("latin1", errors="ignore")

        created_match = re.search(rb"/CreationDate\s*\(D:(.*?)\)", content)
        if created_match:
            metadata.creation_date = created_match.group(1).decode(
                "latin1", errors="ignore"
            )

        mod_match = re.search(rb"/ModDate\s*\(D:(.*?)\)", content)
        if mod_match:
            metadata.mod_date = mod_match.group(1).decode("latin1", errors="ignore")

        # Estimate Page Count
        page_matches = re.findall(rb"/Type\s*/Page\b", content)
        if page_matches:
            metadata.page_count = max(1, len(page_matches))

        # Check Timestamp discrepancies
        if (
            metadata.creation_date
            and metadata.mod_date
            and metadata.creation_date != metadata.mod_date
        ):
            anomalies.append(
                PDFTamperAnomaly(
                    code="MODIFIED_AFTER_CREATION",
                    severity="LOW",
                    description="Modification timestamp differs from initial creation timestamp.",
                )
            )

        # Bound score between 0 and 100
        score = max(0.0, min(100.0, score))

        if score >= 85.0 and hash_matched:
            status = "GENUINE"
            summary = "AUTHENTIC: PDF integrity verified. No major structural tampering detected."
        elif score >= 50.0:
            status = "SUSPICIOUS"
            summary = f"SUSPICIOUS: PDF shows {len(anomalies)} structural anomalies (Score: {score:.1f}%)."
        else:
            status = "TAMPERED"
            summary = f"TAMPERING DETECTED: High likelihood of forgery or content manipulation (Score: {score:.1f}%)."

        return ForensicPDFResult(
            is_valid=(status == "GENUINE"),
            status=status,
            authenticity_score=score,
            computed_hash=computed_hash,
            expected_hash=expected_hash,
            hash_matched=hash_matched,
            metadata=metadata,
            revision_count=revision_count,
            anomalies=anomalies,
            verification_time=now,
            summary=summary,
        )
