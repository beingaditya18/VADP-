"""
VADP Audit Ledger Router
=============================

REST API endpoints for tamper-evident audit ledger:
  - POST /api/v1/ledger/entries
  - POST /api/v1/ledger/blocks/seal
  - GET  /api/v1/ledger/blocks
  - GET  /api/v1/ledger/entries/{id}/proof
  - GET  /api/v1/ledger/verify
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user, require_role
from app.auth.models import User
from app.db.session import get_db_session
from app.ledger.schemas import (
    ChainVerificationResponseSchema,
    LedgerBlockResponseSchema,
    LedgerEntryCreateSchema,
    LedgerEntryResponseSchema,
    MerkleProofResponseSchema,
)
from app.ledger.service import LedgerService

router = APIRouter(prefix="/ledger", tags=["ledger"])


@router.post(
    "/entries",
    response_model=LedgerEntryResponseSchema,
    status_code=status.HTTP_201_CREATED,
    summary="Record audit entry",
    description="Record an auditable system action (e.g. case access, document upload, policy change).",
)
async def record_audit_entry(
    schema: LedgerEntryCreateSchema,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> LedgerEntryResponseSchema:
    service = LedgerService(db)
    return await service.record_entry(schema, actor_id=current_user.id)


@router.post(
    "/blocks/seal",
    response_model=LedgerBlockResponseSchema | None,
    status_code=status.HTTP_200_OK,
    summary="Seal block manually",
    description="Manually seal pending unblocked audit entries into a new immutable LedgerBlock (Admin only).",
    dependencies=[Depends(require_role("admin"))],
)
async def seal_block(
    db: AsyncSession = Depends(get_db_session),
) -> LedgerBlockResponseSchema | None:
    service = LedgerService(db)
    return await service.seal_current_block()


@router.get(
    "/blocks",
    response_model=list[LedgerBlockResponseSchema],
    status_code=status.HTTP_200_OK,
    summary="List ledger blocks",
    description="Retrieve all blocks in the audit hash chain.",
)
async def list_blocks(
    db: AsyncSession = Depends(get_db_session),
) -> list[LedgerBlockResponseSchema]:
    service = LedgerService(db)
    return await service.list_blocks()


@router.get(
    "/entries/{entry_id}/proof",
    response_model=MerkleProofResponseSchema,
    status_code=status.HTTP_200_OK,
    summary="Get Merkle inclusion proof",
    description="Generate Merkle inclusion proof for a specific audit entry within its block.",
)
async def get_merkle_proof(
    entry_id: str,
    db: AsyncSession = Depends(get_db_session),
) -> MerkleProofResponseSchema:
    service = LedgerService(db)
    return await service.generate_merkle_proof(entry_id)


@router.get(
    "/verify",
    response_model=ChainVerificationResponseSchema,
    status_code=status.HTTP_200_OK,
    summary="Verify chain integrity",
    description="Perform full forensic audit verifying SHA-256 hash chaining, Merkle roots, and ECDSA digital signatures.",
)
async def verify_chain_integrity(
    db: AsyncSession = Depends(get_db_session),
) -> ChainVerificationResponseSchema:
    service = LedgerService(db)
    return await service.verify_chain_integrity()
