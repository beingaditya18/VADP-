"""
VADP Audit Ledger Service
==============================

Business logic for recording audit events, sealing blocks, ECDSA signing,
computing Merkle inclusion proofs, and verifying total chain integrity.
"""

from __future__ import annotations

import json
import time
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.core.exceptions import LedgerIntegrityError, NotFoundError
from app.core.logging import get_logger
from app.ledger.hash_chain import HashChain
from app.ledger.merkle_tree import MerkleTree
from app.ledger.models import LedgerBlock, LedgerEntry
from app.ledger.repository import LedgerRepository
from app.ledger.schemas import (
    ChainVerificationResponseSchema,
    LedgerBlockResponseSchema,
    LedgerEntryCreateSchema,
    LedgerEntryResponseSchema,
    MerkleProofNodeSchema,
    MerkleProofResponseSchema,
)
from app.ledger.signatures import LedgerSigner

logger = get_logger(__name__)


def format_iso_timestamp(dt: datetime) -> str:
    """Format datetime consistently to ISO 8601 UTC string."""
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc).replace(microsecond=0).isoformat()


class LedgerService:
    """Service managing tamper-evident audit ledger operations."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.repo = LedgerRepository(db)
        self.signer = LedgerSigner()
        self.settings = get_settings()

    async def record_entry(
        self, schema: LedgerEntryCreateSchema, actor_id: str | None = None
    ) -> LedgerEntryResponseSchema:
        """
        Record a new audit action and check if auto-seal threshold is met.
        """
        now = datetime.now(timezone.utc)
        entry_data_json = json.dumps(schema.entry_data, sort_keys=True)
        data_hash = HashChain.calculate_entry_data_hash(
            schema.entry_type, actor_id, schema.action, entry_data_json
        )

        entry = LedgerEntry(
            entry_type=schema.entry_type,
            actor_id=actor_id,
            action=schema.action,
            resource_type=schema.resource_type,
            resource_id=schema.resource_id,
            data_hash=data_hash,
            entry_data=schema.entry_data,
            timestamp=now,
        )

        created_entry = await self.repo.create_entry(entry)
        logger.info(
            "Recorded audit entry",
            extra={"entry_id": created_entry.id, "type": created_entry.entry_type},
        )

        # Check if auto-seal threshold is reached
        if self.settings.LEDGER_AUTO_FINALIZE:
            unblocked = await self.repo.get_unblocked_entries(
                limit=self.settings.LEDGER_BLOCK_SIZE + 1
            )
            if len(unblocked) >= self.settings.LEDGER_BLOCK_SIZE:
                await self.seal_current_block()

        return LedgerEntryResponseSchema.model_validate(created_entry)

    async def seal_current_block(self) -> LedgerBlockResponseSchema | None:
        """
        Seal unblocked audit entries into a new immutable LedgerBlock.
        Computes Merkle root, SHA-256 block hash, and signs with ECDSA key.
        """
        entries = await self.repo.get_unblocked_entries(
            limit=self.settings.LEDGER_BLOCK_SIZE
        )
        if not entries:
            return None

        # Fetch tip block
        latest_block = await self.repo.get_latest_block()
        new_index = (latest_block.block_index + 1) if latest_block else 0
        previous_hash = (
            latest_block.block_hash if latest_block else HashChain.GENESIS_PREVIOUS_HASH
        )

        now = datetime.now(timezone.utc).replace(microsecond=0)
        now_str = format_iso_timestamp(now)

        # Compute Merkle Root of entries
        leaf_hashes = [e.data_hash for e in entries]
        merkle_root = MerkleTree.compute_root(leaf_hashes)

        # Combined data hash of leaves
        combined_data_hash = MerkleTree.hash_data("".join(leaf_hashes))

        # Compute block hash
        block_hash = HashChain.calculate_block_hash(
            block_index=new_index,
            timestamp_str=now_str,
            previous_hash=previous_hash,
            data_hash=combined_data_hash,
            merkle_root=merkle_root,
        )

        # Sign block hash using ECDSA private key
        signature = self.signer.sign_block(block_hash)

        block = LedgerBlock(
            block_index=new_index,
            timestamp=now,
            timestamp_iso=now_str,
            previous_hash=previous_hash,
            data_hash=combined_data_hash,
            merkle_root=merkle_root,
            block_hash=block_hash,
            signature=signature,
            entries_count=len(entries),
        )

        sealed_block = await self.repo.create_block(block, list(entries))
        logger.info(
            "Sealed new ledger block",
            extra={
                "index": sealed_block.block_index,
                "hash": sealed_block.block_hash[:8],
            },
        )
        return LedgerBlockResponseSchema.model_validate(sealed_block)

    async def list_blocks(self) -> list[LedgerBlockResponseSchema]:
        """List all blocks in the audit chain."""
        blocks = await self.repo.get_all_blocks()
        return [LedgerBlockResponseSchema.model_validate(b) for b in blocks]

    async def generate_merkle_proof(self, entry_id: str) -> MerkleProofResponseSchema:
        """
        Generate Merkle inclusion proof for an entry inside its sealed block.
        """
        entry = await self.repo.get_entry_by_id(entry_id)
        if not entry or not entry.block:
            raise NotFoundError(
                message="Entry is either not found or not yet sealed into a block."
            )

        block = entry.block
        ordered_entries = sorted(block.entries, key=lambda e: e.timestamp)
        leaf_hashes = [e.data_hash for e in ordered_entries]

        # Find entry index in block
        target_idx = -1
        for idx, e in enumerate(ordered_entries):
            if e.id == entry.id:
                target_idx = idx
                break

        if target_idx == -1:
            raise NotFoundError(message="Entry index not found in block.")

        proof_path = MerkleTree.generate_proof(leaf_hashes, target_idx)
        is_valid = MerkleTree.verify_proof(
            entry.data_hash, proof_path, block.merkle_root or ""
        )

        proof_nodes = [
            MerkleProofNodeSchema(position=p["position"], hash=p["hash"])
            for p in proof_path
        ]

        return MerkleProofResponseSchema(
            entry_id=entry.id,
            entry_hash=entry.data_hash,
            block_index=block.block_index,
            merkle_root=block.merkle_root or "",
            proof_path=proof_nodes,
            is_valid=is_valid,
        )

    async def verify_chain_integrity(self) -> ChainVerificationResponseSchema:
        """
        Forensic audit verification of entire block chain from genesis (index 0) to tip.
        Verifies:
          1. Previous hash linkage
          2. SHA-256 block hash recalculation
          3. Merkle root recalculation
          4. ECDSA digital signature validity
        """
        start_time = time.perf_counter()
        blocks = await self.repo.get_all_blocks()

        if not blocks:
            elapsed = (time.perf_counter() - start_time) * 1000
            return ChainVerificationResponseSchema(
                is_valid=True,
                total_blocks=0,
                verified_blocks=0,
                verification_time_ms=elapsed,
                details="Empty ledger chain is trivially valid.",
            )

        expected_prev_hash = HashChain.GENESIS_PREVIOUS_HASH
        verified_count = 0

        for block in blocks:
            # 1. Previous hash check
            if block.previous_hash != expected_prev_hash:
                elapsed = (time.perf_counter() - start_time) * 1000
                return ChainVerificationResponseSchema(
                    is_valid=False,
                    total_blocks=len(blocks),
                    verified_blocks=verified_count,
                    first_invalid_block=block.block_index,
                    verification_time_ms=elapsed,
                    details=f"TAMPERING DETECTED at Block #{block.block_index}: Previous hash mismatch!",
                )

            # 2. Merkle Root recalculation
            ordered_entries = sorted(block.entries, key=lambda e: e.timestamp)
            leaf_hashes = [e.data_hash for e in ordered_entries]
            recomputed_merkle = MerkleTree.compute_root(leaf_hashes)

            if block.merkle_root and block.merkle_root != recomputed_merkle:
                elapsed = (time.perf_counter() - start_time) * 1000
                return ChainVerificationResponseSchema(
                    is_valid=False,
                    total_blocks=len(blocks),
                    verified_blocks=verified_count,
                    first_invalid_block=block.block_index,
                    verification_time_ms=elapsed,
                    details=f"TAMPERING DETECTED at Block #{block.block_index}: Merkle Root mismatch!",
                )

            # 3. Block Hash recalculation
            recomputed_data_hash = MerkleTree.hash_data("".join(leaf_hashes))
            ts_str = block.timestamp_iso or format_iso_timestamp(block.timestamp)
            recomputed_block_hash = HashChain.calculate_block_hash(
                block_index=block.block_index,
                timestamp_str=ts_str,
                previous_hash=block.previous_hash,
                data_hash=recomputed_data_hash,
                merkle_root=block.merkle_root or "",
                nonce=block.nonce,
            )

            if block.block_hash != recomputed_block_hash:
                elapsed = (time.perf_counter() - start_time) * 1000
                return ChainVerificationResponseSchema(
                    is_valid=False,
                    total_blocks=len(blocks),
                    verified_blocks=verified_count,
                    first_invalid_block=block.block_index,
                    verification_time_ms=elapsed,
                    details=f"TAMPERING DETECTED at Block #{block.block_index}: Block hash mismatch!",
                )

            # 4. ECDSA Signature verification
            if block.signature and not self.signer.verify_signature(
                block.block_hash, block.signature
            ):
                elapsed = (time.perf_counter() - start_time) * 1000
                return ChainVerificationResponseSchema(
                    is_valid=False,
                    total_blocks=len(blocks),
                    verified_blocks=verified_count,
                    first_invalid_block=block.block_index,
                    verification_time_ms=elapsed,
                    details=f"TAMPERING DETECTED at Block #{block.block_index}: Invalid ECDSA signature!",
                )

            expected_prev_hash = block.block_hash
            verified_count += 1

        elapsed = (time.perf_counter() - start_time) * 1000
        return ChainVerificationResponseSchema(
            is_valid=True,
            total_blocks=len(blocks),
            verified_blocks=verified_count,
            verification_time_ms=elapsed,
            details=f"All {verified_count} blocks in audit ledger verified successfully. Zero tampering detected.",
        )
