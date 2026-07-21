"""
Nyaya-ZTA Audit Ledger Schemas
==============================

Pydantic schemas for Ledger Blocks, Entries, Inclusion Proofs, and Chain Verification results.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class LedgerEntryCreateSchema(BaseModel):
    entry_type: str = Field(..., description="e.g. 'case_access', 'document_upload', 'policy_change'")
    action: str = Field(..., description="Detailed description of action performed")
    resource_type: str | None = None
    resource_id: str | None = None
    entry_data: dict[str, Any] = Field(default_factory=dict)


class LedgerEntryResponseSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    block_id: str | None = None
    entry_type: str
    actor_id: str | None = None
    action: str
    resource_type: str | None = None
    resource_id: str | None = None
    data_hash: str
    entry_data: dict[str, Any]
    timestamp: datetime
    created_at: datetime


class LedgerBlockResponseSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    block_index: int
    timestamp: datetime
    previous_hash: str
    data_hash: str
    merkle_root: str | None = None
    block_hash: str
    signature: str | None = None
    nonce: int
    entries_count: int
    created_at: datetime
    entries: list[LedgerEntryResponseSchema] = Field(default_factory=list)


class MerkleProofNodeSchema(BaseModel):
    position: str  # 'left' or 'right'
    hash: str


class MerkleProofResponseSchema(BaseModel):
    entry_id: str
    entry_hash: str
    block_index: int
    merkle_root: str
    proof_path: list[MerkleProofNodeSchema]
    is_valid: bool


class ChainVerificationResponseSchema(BaseModel):
    is_valid: bool
    total_blocks: int
    verified_blocks: int
    first_invalid_block: int | None = None
    verification_time_ms: float
    details: str
