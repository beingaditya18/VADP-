"""
VADP Off-Chain Evidence Vault
====================================

BSA 2023 §63(4) Dual-Custody Off-Chain Evidence Vault with Merkle Anchor.

Architecture:
  - SQLite table `evidence_vault` stores SHA-256 hashes of evidence documents
  - RFC 6962 Merkle tree anchors all leaf hashes into a single Merkle root
  - Each leaf stores: document SHA-256, Merkle leaf hash, proof path, BSA seal
  - Dual-custody enforcement: every entry requires two authorizing officers
    (custody_officer_1: role='judge', custody_officer_2: role='clerk')

Verification Contract Fields:
  Field 5: merkle_leaf_hash  — RFC 6962 leaf hash of document SHA-256
  Field 6: merkle_root       — Accumulated Merkle root at seal time

BSA 2023 §63(4) Compliance:
  - Dual-custody seal with two named officers
  - ISO-8601 UTC timestamp for each sealing event
  - Immutable append-only vault (no UPDATE/DELETE)
  - Full audit trail with proof path for every document
"""

from __future__ import annotations

import hashlib
import json
import sqlite3
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

# Reuse existing Merkle tree implementation
import sys

BACKEND_DIR = Path(__file__).resolve().parent.parent.parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.ledger.merkle_tree import MerkleTree

# ── Constants ──────────────────────────────────────────────────────────────

NSSC_THRESHOLD = 0.82  # NSSC score below which escalation is mandatory
VAULT_DB_FILENAME = "evidence_vault.db"


# ── Off-Chain Evidence Vault ───────────────────────────────────────────────


class EvidenceVault:
    """
    BSA 2023 §63(4) Off-Chain Evidence Vault.

    Stores SHA-256 document hashes in a local SQLite table with:
      - RFC 6962 Merkle leaf anchoring (Field 5)
      - Accumulated Merkle root (Field 6)
      - Dual-custody BSA seal (two officer IDs required)
      - Append-only audit log (no mutations allowed)
    """

    SCHEMA_SQL = """
    CREATE TABLE IF NOT EXISTS evidence_vault (
        id                  TEXT PRIMARY KEY,
        document_sha256     TEXT NOT NULL,
        merkle_leaf_hash    TEXT NOT NULL,
        merkle_root         TEXT NOT NULL,
        leaf_index          INTEGER NOT NULL,
        proof_path          TEXT NOT NULL,        -- JSON: [{position, hash}, ...]
        bsa_seal_timestamp  TEXT NOT NULL,        -- ISO-8601 UTC
        custody_officer_1   TEXT NOT NULL,        -- role: judge
        custody_officer_2   TEXT NOT NULL,        -- role: clerk
        document_id         TEXT,
        case_id             TEXT,
        description         TEXT,
        inserted_at         TEXT NOT NULL
    );

    CREATE INDEX IF NOT EXISTS idx_vault_sha256 ON evidence_vault (document_sha256);
    CREATE INDEX IF NOT EXISTS idx_vault_case   ON evidence_vault (case_id);
    CREATE INDEX IF NOT EXISTS idx_vault_leaf   ON evidence_vault (merkle_leaf_hash);
    """

    def __init__(self, db_path: Path | str | None = None) -> None:
        if db_path is None:
            vault_dir = BACKEND_DIR / "database"
            vault_dir.mkdir(parents=True, exist_ok=True)
            db_path = vault_dir / VAULT_DB_FILENAME

        self.db_path = Path(db_path)
        self._conn: sqlite3.Connection | None = None
        self._init_db()

    def _get_conn(self) -> sqlite3.Connection:
        if self._conn is None:
            self._conn = sqlite3.connect(str(self.db_path), check_same_thread=False)
            self._conn.row_factory = sqlite3.Row
        return self._conn

    def _init_db(self) -> None:
        """Create vault schema if it does not exist."""
        conn = self._get_conn()
        conn.executescript(self.SCHEMA_SQL)
        conn.commit()

    # ── Core Operations ────────────────────────────────────────────────

    def compute_document_sha256(self, document_bytes: bytes) -> str:
        """Compute SHA-256 hash of raw document bytes."""
        return hashlib.sha256(document_bytes).hexdigest()

    def _get_all_leaf_hashes(self) -> list[str]:
        """Retrieve all Merkle leaf hashes in insertion order."""
        conn = self._get_conn()
        rows = conn.execute(
            "SELECT merkle_leaf_hash FROM evidence_vault ORDER BY leaf_index ASC"
        ).fetchall()
        return [row["merkle_leaf_hash"] for row in rows]

    def seal_document(
        self,
        document_bytes: bytes,
        custody_officer_1: str,
        custody_officer_2: str,
        document_id: str | None = None,
        case_id: str | None = None,
        description: str | None = None,
    ) -> dict[str, Any]:
        """
        Seal a document in the vault with BSA §63(4) dual-custody authorization.

        Steps:
          1. Compute SHA-256 of document bytes
          2. Compute RFC 6962 leaf hash: SHA-256(0x00 || document_sha256)
          3. Append leaf to running Merkle tree and compute new root
          4. Generate Merkle inclusion proof for this leaf
          5. Insert immutable record with dual-custody BSA seal

        Returns:
            VaultEntry dict with Field 5 (merkle_leaf_hash) and Field 6 (merkle_root)
        """
        if not custody_officer_1 or not custody_officer_2:
            raise ValueError("BSA §63(4): dual-custody requires two officer IDs")
        if custody_officer_1 == custody_officer_2:
            raise ValueError(
                "BSA §63(4): dual-custody requires two *different* officers"
            )

        now = datetime.now(timezone.utc)
        entry_id = str(uuid.uuid4())

        # Step 1: SHA-256 of document
        doc_sha256 = self.compute_document_sha256(document_bytes)

        # Step 2: RFC 6962 leaf hash
        merkle_leaf_hash = MerkleTree.hash_leaf(doc_sha256)

        # Step 3: Compute new Merkle root with this leaf appended
        existing_leaves = self._get_all_leaf_hashes()
        all_leaves = existing_leaves + [merkle_leaf_hash]
        leaf_index = len(existing_leaves)
        merkle_root = MerkleTree.compute_root(all_leaves)

        # Step 4: Generate inclusion proof
        proof_path = MerkleTree.generate_proof(all_leaves, leaf_index)

        # Step 5: Insert immutable record
        conn = self._get_conn()
        conn.execute(
            """
            INSERT INTO evidence_vault
                (id, document_sha256, merkle_leaf_hash, merkle_root, leaf_index,
                 proof_path, bsa_seal_timestamp, custody_officer_1, custody_officer_2,
                 document_id, case_id, description, inserted_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                entry_id,
                doc_sha256,
                merkle_leaf_hash,
                merkle_root,
                leaf_index,
                json.dumps(proof_path),
                now.isoformat(),
                custody_officer_1,
                custody_officer_2,
                document_id,
                case_id,
                description,
                now.isoformat(),
            ),
        )
        conn.commit()

        vault_entry = {
            "id": entry_id,
            "document_sha256": doc_sha256,
            # Field 5: Merkle leaf hash (BSA §63(4) evidence anchor)
            "merkle_leaf_hash": merkle_leaf_hash,
            # Field 6: Merkle root at time of sealing
            "merkle_root": merkle_root,
            "leaf_index": leaf_index,
            "proof_path": proof_path,
            "bsa_seal_timestamp": now.isoformat(),
            "custody_officer_1": custody_officer_1,
            "custody_officer_2": custody_officer_2,
            "document_id": document_id,
            "case_id": case_id,
            "description": description,
        }
        return vault_entry

    def verify_document(
        self, document_bytes: bytes, expected_leaf_hash: str
    ) -> dict[str, Any]:
        """
        Verify a document against its stored vault entry.

        Steps:
          1. Recompute SHA-256 of provided bytes
          2. Recompute RFC 6962 leaf hash
          3. Compare against stored leaf hash
          4. Re-verify Merkle inclusion proof against stored root

        Returns:
            {
              "verified": bool,
              "hash_match": bool,
              "merkle_proof_valid": bool,
              "detail": str,
            }
        """
        recomputed_sha256 = self.compute_document_sha256(document_bytes)
        recomputed_leaf = MerkleTree.hash_leaf(recomputed_sha256)

        hash_match = recomputed_leaf == expected_leaf_hash
        if not hash_match:
            return {
                "verified": False,
                "hash_match": False,
                "merkle_proof_valid": False,
                "detail": f"Document hash mismatch: expected leaf {expected_leaf_hash[:16]}..., got {recomputed_leaf[:16]}...",
            }

        # Retrieve proof and root from vault
        conn = self._get_conn()
        row = conn.execute(
            "SELECT proof_path, merkle_root FROM evidence_vault WHERE merkle_leaf_hash = ?",
            (expected_leaf_hash,),
        ).fetchone()

        if not row:
            return {
                "verified": False,
                "hash_match": True,
                "merkle_proof_valid": False,
                "detail": "Leaf hash not found in vault — document was never sealed.",
            }

        proof_path = json.loads(row["proof_path"])
        stored_root = row["merkle_root"]

        proof_valid = MerkleTree.verify_proof(recomputed_leaf, proof_path, stored_root)
        return {
            "verified": hash_match and proof_valid,
            "hash_match": hash_match,
            "merkle_proof_valid": proof_valid,
            "stored_merkle_root": stored_root,
            "recomputed_leaf_hash": recomputed_leaf,
            "detail": "Document integrity verified against BSA §63(4) Merkle seal."
            if proof_valid
            else "Merkle proof verification failed — possible tamper or corruption.",
        }

    def get_entry(self, entry_id: str) -> dict[str, Any] | None:
        """Retrieve a vault entry by ID."""
        conn = self._get_conn()
        row = conn.execute(
            "SELECT * FROM evidence_vault WHERE id = ?", (entry_id,)
        ).fetchone()
        if not row:
            return None
        return dict(row)

    def list_entries(self, case_id: str | None = None) -> list[dict[str, Any]]:
        """List vault entries, optionally filtered by case_id."""
        conn = self._get_conn()
        if case_id:
            rows = conn.execute(
                "SELECT * FROM evidence_vault WHERE case_id = ? ORDER BY leaf_index ASC",
                (case_id,),
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT * FROM evidence_vault ORDER BY leaf_index ASC"
            ).fetchall()
        return [dict(row) for row in rows]

    def total_documents(self) -> int:
        """Return total number of sealed documents."""
        conn = self._get_conn()
        return conn.execute("SELECT COUNT(*) FROM evidence_vault").fetchone()[0]

    def current_merkle_root(self) -> str | None:
        """Return the current Merkle root (most recently computed)."""
        conn = self._get_conn()
        row = conn.execute(
            "SELECT merkle_root FROM evidence_vault ORDER BY leaf_index DESC LIMIT 1"
        ).fetchone()
        return row["merkle_root"] if row else None

    def close(self) -> None:
        """Close the database connection."""
        if self._conn:
            self._conn.close()
            self._conn = None
