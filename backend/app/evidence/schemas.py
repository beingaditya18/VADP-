"""
Nyaya-ZTA Evidence Schemas
==========================

Pydantic schemas for Evidence registration, integrity verification, and response.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class EvidenceCreateSchema(BaseModel):
    document_id: str
    case_id: str
    evidence_type: str = Field(..., description="e.g. 'forensic', 'affidavit', 'digital_log'")


class EvidenceVerificationResultSchema(BaseModel):
    is_valid: bool
    status: str  # 'verified' or 'tampered'
    expected_hash: str
    computed_hash: str
    verification_time: datetime
    message: str


class EvidenceResponseSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    document_id: str
    case_id: str
    evidence_type: str
    verification_status: str
    integrity_hash: str
    verified_by: str | None = None
    verified_at: datetime | None = None
    chain_of_custody: list[dict[str, Any]] = Field(default_factory=list)
    created_at: datetime
