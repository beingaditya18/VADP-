"""
VADP Hash Chain Module
===========================

SHA-256 block hash chaining logic.
Block Hash = SHA256(index + timestamp + previous_hash + data_hash + merkle_root + nonce)
Genesis Block has index=0, previous_hash='0'*64
"""

from __future__ import annotations

import hashlib


class HashChain:
    """Hash chaining utility."""

    GENESIS_PREVIOUS_HASH = "0" * 64

    @staticmethod
    def calculate_block_hash(
        block_index: int,
        timestamp_str: str,
        previous_hash: str,
        data_hash: str,
        merkle_root: str,
        nonce: int = 0,
    ) -> str:
        """
        Compute SHA-256 block hash.
        """
        payload = f"{block_index}:{timestamp_str}:{previous_hash}:{data_hash}:{merkle_root}:{nonce}"
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()

    @staticmethod
    def calculate_entry_data_hash(
        entry_type: str, actor_id: str | None, action: str, entry_data_json: str
    ) -> str:
        """
        Compute entry data hash.
        """
        payload = f"{entry_type}:{actor_id or 'system'}:{action}:{entry_data_json}"
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()
