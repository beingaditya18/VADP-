"""Add VADP Verification Contracts and Contract Events

Revision ID: 0002_vadp_contracts
Revises: 0001_initial_schema
Create Date: 2026-07-24

VADP (Verifiable AI Decision Provenance) Schema Extension:
  - verification_contracts: Central VADP artifact binding all provenance components
  - contract_events: Decision provenance timeline events within a contract lifecycle

Database Portability:
  - UUID stored as String(36) — SQLite + PostgreSQL compatible
  - JSON (not JSONB) — works on both engines
  - No server-side defaults — Python generates all values
  - Additive migration — no existing tables are modified
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0002_vadp_contracts"
down_revision: Union[str, None] = "0001_initial_schema"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ── Verification Contracts ──────────────────────────────
    op.create_table(
        "verification_contracts",
        # Identity
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("contract_version", sa.String(20), nullable=False, server_default="1.0.0"),
        # Binding References
        sa.Column("case_id", sa.String(36), sa.ForeignKey("cases.id", ondelete="CASCADE"), nullable=False),
        sa.Column("recommendation_id", sa.String(36), sa.ForeignKey("ai_recommendations.id", ondelete="CASCADE"), nullable=False),
        # Authorization Provenance
        sa.Column("authorization_decision_id", sa.String(36), sa.ForeignKey("access_decisions.id"), nullable=True),
        sa.Column("authorization_policy_id", sa.String(36), sa.ForeignKey("access_policies.id"), nullable=True),
        sa.Column("authorization_result", sa.String(20), nullable=False, server_default="allow"),
        sa.Column("authorization_reason", sa.Text(), nullable=True),
        # Evidence Provenance
        sa.Column("evidence_hashes", sa.JSON(), nullable=False),
        sa.Column("evidence_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("evidence_verified", sa.Integer(), nullable=False, server_default="0"),
        # RAG Provenance
        sa.Column("rag_query_id", sa.String(36), sa.ForeignKey("rag_queries.id"), nullable=True),
        sa.Column("rag_citations", sa.JSON(), nullable=False),
        sa.Column("rag_retrieval_metadata", sa.JSON(), nullable=False),
        # SHAP Explainability
        sa.Column("shap_values", sa.JSON(), nullable=False),
        sa.Column("feature_importance", sa.JSON(), nullable=False),
        sa.Column("contributing_factors", sa.JSON(), nullable=False),
        # Trust Score
        sa.Column("trust_score", sa.Float(), nullable=False),
        sa.Column("trust_breakdown", sa.JSON(), nullable=False),
        # Risk Assessment
        sa.Column("risk_score", sa.Float(), nullable=False),
        sa.Column("risk_level", sa.String(20), nullable=False),
        sa.Column("risk_features", sa.JSON(), nullable=False),
        # Human Review
        sa.Column("human_review_status", sa.String(50), nullable=False, server_default="pending_review"),
        sa.Column("reviewed_by", sa.String(36), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("review_action", sa.String(50), nullable=True),
        sa.Column("review_notes", sa.Text(), nullable=True),
        # Cryptographic Integrity
        sa.Column("contract_hash", sa.String(128), nullable=False),
        sa.Column("digital_signature", sa.String(512), nullable=True),
        sa.Column("signing_algorithm", sa.String(50), nullable=True, server_default="ECDSA-P256-SHA256"),
        # Merkle Inclusion
        sa.Column("merkle_leaf_hash", sa.String(128), nullable=True),
        sa.Column("ledger_block_id", sa.String(36), sa.ForeignKey("ledger_blocks.id"), nullable=True),
        sa.Column("merkle_proof", sa.JSON(), nullable=True),
        # Completeness Invariant
        sa.Column("completeness_status", sa.String(50), nullable=False, server_default="incomplete"),
        sa.Column("completeness_checks", sa.JSON(), nullable=False),
        # Audit Timestamps
        sa.Column("generated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("finalized_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("invalidated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("invalidation_reason", sa.Text(), nullable=True),
        # Standard Mixins
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_vc_case_id", "verification_contracts", ["case_id"])
    op.create_index("ix_vc_recommendation_id", "verification_contracts", ["recommendation_id"], unique=True)
    op.create_index("ix_vc_contract_hash", "verification_contracts", ["contract_hash"])
    op.create_index("ix_vc_completeness", "verification_contracts", ["completeness_status"])
    op.create_index("ix_vc_human_review", "verification_contracts", ["human_review_status"])
    op.create_index("ix_vc_generated_at", "verification_contracts", ["generated_at"])

    # ── Contract Events (Decision Provenance Timeline) ──────
    op.create_table(
        "contract_events",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("contract_id", sa.String(36), sa.ForeignKey("verification_contracts.id", ondelete="CASCADE"), nullable=False),
        sa.Column("event_type", sa.String(100), nullable=False),
        sa.Column("event_order", sa.Integer(), nullable=False),
        sa.Column("actor_id", sa.String(36), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("event_data", sa.JSON(), nullable=False),
        sa.Column("event_hash", sa.String(128), nullable=False),
        sa.Column("parent_hash", sa.String(128), nullable=True),
        sa.Column("timestamp", sa.DateTime(timezone=True), nullable=False),
        sa.Column("duration_ms", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_ce_contract_id", "contract_events", ["contract_id"])
    op.create_index("ix_ce_event_type", "contract_events", ["event_type"])
    op.create_index("ix_ce_event_order", "contract_events", ["contract_id", "event_order"])


def downgrade() -> None:
    op.drop_table("contract_events")
    op.drop_table("verification_contracts")
