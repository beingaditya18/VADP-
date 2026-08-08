"""
VADP Evidence Schemas
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


class PDFTamperAnomalySchema(BaseModel):
    code: str
    severity: str
    description: str


class PDFMetadataInfoSchema(BaseModel):
    title: str | None = None
    author: str | None = None
    producer: str | None = None
    creator: str | None = None
    creation_date: str | None = None
    mod_date: str | None = None
    page_count: int = 1


class ForensicPDFResultSchema(BaseModel):
    is_valid: bool
    status: str
    authenticity_score: float
    computed_hash: str
    expected_hash: str | None = None
    hash_matched: bool
    metadata: PDFMetadataInfoSchema
    revision_count: int
    anomalies: list[PDFTamperAnomalySchema] = Field(default_factory=list)
    verification_time: datetime
    summary: str


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


class RedactEvidenceRequestSchema(BaseModel):
    evidence_data: dict[str, Any] = Field(..., description="Key-value dictionary of evidence fields")
    keys_to_redact: list[str] = Field(..., description="List of sensitive keys to redact (e.g. ['victim_name', 'age'])")


class RedactEvidenceResponseSchema(BaseModel):
    original_merkle_root: str
    redacted_merkle_root: str
    root_invariant: bool
    redacted_evidence_data: dict[str, Any]
    redacted_keys: list[str]
    blinded_commitments: dict[str, str]
    message: str


class ZKProveRequestSchema(BaseModel):
    private_evidence_hash: str
    merkle_root: str
    merkle_path: list[tuple[str, str]] = Field(..., description="List of (sibling_hash, direction) tuples")


class ZKProveResponseSchema(BaseModel):
    proof_system: str
    circuit_name: str
    public_inputs: dict[str, Any]
    pi_a: list[str]
    pi_b: list[list[str]]
    pi_c: list[str]
    verification_key_id: str
    proving_time_ms: float


class ZKVerifyRequestSchema(BaseModel):
    proof: ZKProveResponseSchema
    expected_root: str


class ZKVerifyResponseSchema(BaseModel):
    is_valid: bool
    verification_time_ms: float
    message: str


