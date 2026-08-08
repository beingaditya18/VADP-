"""Initial complete schema — SQLite compatible

Revision ID: 0001
Revises: None
Create Date: 2026-07-21

Database Portability:
  - UUID stored as String(36) — works on both SQLite and PostgreSQL
  - JSON instead of JSONB — works on both engines
  - No server-side UUID generation — Python generates UUIDs
  - Timestamps use ISO strings on SQLite, native on PostgreSQL
  - All foreign keys use String(36) references
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0001_initial_schema"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ── Users ────────────────────────────────────────────────
    op.create_table(
        "users",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("email", sa.String(320), nullable=False, unique=True),
        sa.Column("hashed_password", sa.String(255), nullable=False),
        sa.Column("full_name", sa.String(255), nullable=False),
        sa.Column("role", sa.String(50), nullable=False),
        sa.Column("bar_number", sa.String(100), nullable=True),
        sa.Column("court_id", sa.String(36), nullable=True),
        sa.Column("is_active", sa.Boolean(), default=True, nullable=False),
        sa.Column("is_verified", sa.Boolean(), default=False, nullable=False),
        sa.Column("metadata_", sa.JSON(), default=dict, nullable=False),
        sa.Column("last_login_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("idx_users_email", "users", ["email"])
    op.create_index("idx_users_role", "users", ["role"])
    op.create_index("idx_users_is_active", "users", ["is_active"])

    # ── Sessions ─────────────────────────────────────────────
    op.create_table(
        "sessions",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("user_id", sa.String(36), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("refresh_token_hash", sa.String(255), nullable=False),
        sa.Column("device_info", sa.JSON(), default=dict, nullable=False),
        sa.Column("ip_address", sa.String(45), nullable=True),
        sa.Column("user_agent", sa.String(500), nullable=True),
        sa.Column("is_active", sa.Boolean(), default=True, nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("idx_sessions_user_id", "sessions", ["user_id"])
    op.create_index("idx_sessions_active", "sessions", ["is_active"])

    # ── User Devices ─────────────────────────────────────────
    op.create_table(
        "user_devices",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("user_id", sa.String(36), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("device_fingerprint", sa.String(512), nullable=False),
        sa.Column("device_name", sa.String(255), nullable=True),
        sa.Column("trust_level", sa.Float(), default=0.0, nullable=False),
        sa.Column("last_verified_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("is_trusted", sa.Boolean(), default=False, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("idx_user_devices_user_id", "user_devices", ["user_id"])

    # ── Cases ────────────────────────────────────────────────
    op.create_table(
        "cases",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("case_number", sa.String(100), nullable=False, unique=True),
        sa.Column("title", sa.String(500), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("case_type", sa.String(100), nullable=False),
        sa.Column("status", sa.String(50), default="filed", nullable=False),
        sa.Column("priority", sa.String(20), default="medium", nullable=False),
        sa.Column("filed_by", sa.String(36), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("assigned_judge", sa.String(36), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("assigned_lawyer", sa.String(36), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("court_id", sa.String(36), nullable=True),
        sa.Column("filing_date", sa.Date(), nullable=False),
        sa.Column("next_hearing_date", sa.Date(), nullable=True),
        sa.Column("metadata_", sa.JSON(), default=dict, nullable=False),
        sa.Column("is_deleted", sa.Boolean(), default=False, nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("idx_cases_status", "cases", ["status"])
    op.create_index("idx_cases_filed_by", "cases", ["filed_by"])
    op.create_index("idx_cases_assigned_judge", "cases", ["assigned_judge"])
    op.create_index("idx_cases_case_type", "cases", ["case_type"])
    op.create_index("idx_cases_is_deleted", "cases", ["is_deleted"])
    op.create_index("idx_cases_case_number", "cases", ["case_number"])

    # ── Case Parties ─────────────────────────────────────────
    op.create_table(
        "case_parties",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("case_id", sa.String(36), sa.ForeignKey("cases.id", ondelete="CASCADE"), nullable=False),
        sa.Column("user_id", sa.String(36), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("party_name", sa.String(255), nullable=False),
        sa.Column("party_type", sa.String(50), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("idx_case_parties_case_id", "case_parties", ["case_id"])

    # ── Case Events ──────────────────────────────────────────
    op.create_table(
        "case_events",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("case_id", sa.String(36), sa.ForeignKey("cases.id", ondelete="CASCADE"), nullable=False),
        sa.Column("event_type", sa.String(100), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("performed_by", sa.String(36), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("event_data", sa.JSON(), default=dict, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("idx_case_events_case_id", "case_events", ["case_id"])
    op.create_index("idx_case_events_type", "case_events", ["event_type"])

    # ── Documents ────────────────────────────────────────────
    op.create_table(
        "documents",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("case_id", sa.String(36), sa.ForeignKey("cases.id", ondelete="CASCADE"), nullable=False),
        sa.Column("uploaded_by", sa.String(36), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("file_name", sa.String(500), nullable=False),
        sa.Column("file_type", sa.String(100), nullable=True),
        sa.Column("file_size", sa.BigInteger(), nullable=True),
        sa.Column("storage_path", sa.String(1000), nullable=False),
        sa.Column("content_hash", sa.String(128), nullable=False),
        sa.Column("is_verified", sa.Boolean(), default=False, nullable=False),
        sa.Column("metadata_", sa.JSON(), default=dict, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("idx_documents_case_id", "documents", ["case_id"])
    op.create_index("idx_documents_uploaded_by", "documents", ["uploaded_by"])
    op.create_index("idx_documents_content_hash", "documents", ["content_hash"])

    # ── Evidence Records ─────────────────────────────────────
    op.create_table(
        "evidence_records",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("document_id", sa.String(36), sa.ForeignKey("documents.id", ondelete="CASCADE"), nullable=False),
        sa.Column("case_id", sa.String(36), sa.ForeignKey("cases.id", ondelete="CASCADE"), nullable=False),
        sa.Column("evidence_type", sa.String(100), nullable=False),
        sa.Column("verification_status", sa.String(50), default="pending", nullable=False),
        sa.Column("integrity_hash", sa.String(128), nullable=False),
        sa.Column("verified_by", sa.String(36), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("verified_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("chain_of_custody", sa.JSON(), default=list, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("idx_evidence_case_id", "evidence_records", ["case_id"])
    op.create_index("idx_evidence_document_id", "evidence_records", ["document_id"])

    # ── Document Chunks (RAG) ────────────────────────────────
    op.create_table(
        "document_chunks",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("document_id", sa.String(36), sa.ForeignKey("documents.id", ondelete="CASCADE"), nullable=False),
        sa.Column("chunk_index", sa.Integer(), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("embedding_id", sa.String(255), nullable=True),
        sa.Column("token_count", sa.Integer(), nullable=True),
        sa.Column("metadata_", sa.JSON(), default=dict, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("idx_chunks_document_id", "document_chunks", ["document_id"])
    op.create_table(
        "_unique_doc_chunk",
        sa.Column("document_id", sa.String(36), nullable=False),
        sa.Column("chunk_index", sa.Integer(), nullable=False),
        sa.UniqueConstraint("document_id", "chunk_index", name="uq_document_chunk_index"),
    )
    op.drop_table("_unique_doc_chunk")
    # Note: UniqueConstraint applied inline above doesn't work with op.create_table
    # We add it directly on document_chunks instead:
    # SQLite doesn't support ADD CONSTRAINT, so we handle uniqueness at the app level

    # ── RAG Queries ──────────────────────────────────────────
    op.create_table(
        "rag_queries",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("user_id", sa.String(36), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("case_id", sa.String(36), sa.ForeignKey("cases.id"), nullable=True),
        sa.Column("query_text", sa.Text(), nullable=False),
        sa.Column("response_text", sa.Text(), nullable=True),
        sa.Column("citations", sa.JSON(), default=list, nullable=False),
        sa.Column("processing_time_ms", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("idx_rag_queries_user_id", "rag_queries", ["user_id"])
    op.create_index("idx_rag_queries_case_id", "rag_queries", ["case_id"])

    # ── AI Recommendations ───────────────────────────────────
    op.create_table(
        "ai_recommendations",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("case_id", sa.String(36), sa.ForeignKey("cases.id", ondelete="CASCADE"), nullable=False),
        sa.Column("recommendation_type", sa.String(100), nullable=False),
        sa.Column("recommendation_text", sa.Text(), nullable=False),
        sa.Column("confidence_score", sa.Float(), nullable=False),
        sa.Column("trust_score", sa.Float(), nullable=False),
        sa.Column("risk_score", sa.Float(), nullable=False),
        sa.Column("model_version", sa.String(100), nullable=True),
        sa.Column("llm_provider", sa.String(100), nullable=True),
        sa.Column("prompt_tokens", sa.Integer(), nullable=True),
        sa.Column("completion_tokens", sa.Integer(), nullable=True),
        sa.Column("processing_time_ms", sa.Integer(), nullable=True),
        sa.Column("status", sa.String(50), default="pending", nullable=False),
        sa.Column("reviewed_by", sa.String(36), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("metadata_", sa.JSON(), default=dict, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("idx_ai_rec_case_id", "ai_recommendations", ["case_id"])
    op.create_index("idx_ai_rec_status", "ai_recommendations", ["status"])

    # ── AI Explanations ──────────────────────────────────────
    op.create_table(
        "ai_explanations",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("recommendation_id", sa.String(36), sa.ForeignKey("ai_recommendations.id", ondelete="CASCADE"), nullable=False),
        sa.Column("explanation_type", sa.String(100), nullable=False),
        sa.Column("shap_values", sa.JSON(), nullable=True),
        sa.Column("feature_importance", sa.JSON(), nullable=True),
        sa.Column("natural_language_explanation", sa.Text(), nullable=True),
        sa.Column("contributing_factors", sa.JSON(), default=list, nullable=False),
        sa.Column("citations", sa.JSON(), default=list, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("idx_ai_expl_rec_id", "ai_explanations", ["recommendation_id"])

    # ── Ledger Blocks ────────────────────────────────────────
    op.create_table(
        "ledger_blocks",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("block_index", sa.BigInteger(), nullable=False, unique=True),
        sa.Column("timestamp", sa.DateTime(timezone=True), nullable=False),
        sa.Column("timestamp_iso", sa.String(64), nullable=True),
        sa.Column("previous_hash", sa.String(128), nullable=False),
        sa.Column("data_hash", sa.String(128), nullable=False),
        sa.Column("merkle_root", sa.String(128), nullable=True),
        sa.Column("block_hash", sa.String(128), nullable=False),
        sa.Column("signature", sa.String(512), nullable=True),
        sa.Column("nonce", sa.BigInteger(), default=0, nullable=False),
        sa.Column("entries_count", sa.Integer(), default=0, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("idx_ledger_blocks_index", "ledger_blocks", ["block_index"])
    op.create_index("idx_ledger_blocks_hash", "ledger_blocks", ["block_hash"])

    # ── Ledger Entries ───────────────────────────────────────
    op.create_table(
        "ledger_entries",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("block_id", sa.String(36), sa.ForeignKey("ledger_blocks.id"), nullable=True),
        sa.Column("entry_type", sa.String(100), nullable=False),
        sa.Column("actor_id", sa.String(36), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("action", sa.String(255), nullable=False),
        sa.Column("resource_type", sa.String(100), nullable=True),
        sa.Column("resource_id", sa.String(36), nullable=True),
        sa.Column("data_hash", sa.String(128), nullable=False),
        sa.Column("entry_data", sa.JSON(), nullable=False),
        sa.Column("timestamp", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("idx_ledger_entries_block_id", "ledger_entries", ["block_id"])
    op.create_index("idx_ledger_entries_actor_id", "ledger_entries", ["actor_id"])
    op.create_index("idx_ledger_entries_type", "ledger_entries", ["entry_type"])
    op.create_index("idx_ledger_entries_resource", "ledger_entries", ["resource_type", "resource_id"])

    # ── Access Policies (Zero Trust) ─────────────────────────
    op.create_table(
        "access_policies",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("policy_name", sa.String(255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("resource_type", sa.String(100), nullable=False),
        sa.Column("action", sa.String(100), nullable=False),
        sa.Column("conditions", sa.JSON(), nullable=False),
        sa.Column("allowed_roles", sa.JSON(), default=list, nullable=False),
        sa.Column("priority", sa.Integer(), default=0, nullable=False),
        sa.Column("is_active", sa.Boolean(), default=True, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("idx_access_policies_resource", "access_policies", ["resource_type", "action"])
    op.create_index("idx_access_policies_active", "access_policies", ["is_active"])

    # ── Access Decisions (Zero Trust) ────────────────────────
    op.create_table(
        "access_decisions",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("user_id", sa.String(36), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("resource_type", sa.String(100), nullable=False),
        sa.Column("resource_id", sa.String(36), nullable=True),
        sa.Column("action", sa.String(100), nullable=False),
        sa.Column("decision", sa.String(20), nullable=False),
        sa.Column("policy_id", sa.String(36), sa.ForeignKey("access_policies.id"), nullable=True),
        sa.Column("context", sa.JSON(), default=dict, nullable=False),
        sa.Column("risk_score", sa.Float(), nullable=True),
        sa.Column("trust_score", sa.Float(), nullable=True),
        sa.Column("reason", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("idx_access_dec_user_id", "access_decisions", ["user_id"])
    op.create_index("idx_access_dec_resource", "access_decisions", ["resource_type", "resource_id"])

    # ── Trust Assessments (Zero Trust) ───────────────────────
    op.create_table(
        "trust_assessments",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("user_id", sa.String(36), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("session_id", sa.String(36), sa.ForeignKey("sessions.id"), nullable=True),
        sa.Column("device_id", sa.String(36), sa.ForeignKey("user_devices.id"), nullable=True),
        sa.Column("trust_score", sa.Float(), nullable=False),
        sa.Column("risk_score", sa.Float(), nullable=False),
        sa.Column("factors", sa.JSON(), nullable=False),
        sa.Column("assessment_type", sa.String(50), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("idx_trust_assess_user_id", "trust_assessments", ["user_id"])

    # ── Notifications ────────────────────────────────────────
    op.create_table(
        "notifications",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("user_id", sa.String(36), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("notification_type", sa.String(50), nullable=False),
        sa.Column("is_read", sa.Boolean(), default=False, nullable=False),
        sa.Column("resource_type", sa.String(100), nullable=True),
        sa.Column("resource_id", sa.String(36), nullable=True),
        sa.Column("metadata_", sa.JSON(), default=dict, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("idx_notifications_user_read", "notifications", ["user_id", "is_read"])
    op.create_index("idx_notifications_type", "notifications", ["notification_type"])

    # ── Search History ───────────────────────────────────────
    op.create_table(
        "search_history",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("user_id", sa.String(36), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("query_text", sa.Text(), nullable=False),
        sa.Column("search_type", sa.String(50), nullable=False),
        sa.Column("filters", sa.JSON(), default=dict, nullable=False),
        sa.Column("results_count", sa.Integer(), default=0, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("idx_search_history_user_id", "search_history", ["user_id"])

    # ── Jurisdiction Configuration ───────────────────────────
    op.create_table(
        "jurisdiction_configs",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("jurisdiction_code", sa.String(50), nullable=False, unique=True),
        sa.Column("jurisdiction_name", sa.String(255), nullable=False),
        sa.Column("country", sa.String(100), nullable=False),
        sa.Column("case_types", sa.JSON(), nullable=False),
        sa.Column("court_hierarchy", sa.JSON(), nullable=False),
        sa.Column("applicable_acts", sa.JSON(), default=list, nullable=False),
        sa.Column("legal_categories", sa.JSON(), default=list, nullable=False),
        sa.Column("is_active", sa.Boolean(), default=True, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("jurisdiction_configs")
    op.drop_table("search_history")
    op.drop_table("notifications")
    op.drop_table("trust_assessments")
    op.drop_table("access_decisions")
    op.drop_table("access_policies")
    op.drop_table("ledger_entries")
    op.drop_table("ledger_blocks")
    op.drop_table("ai_explanations")
    op.drop_table("ai_recommendations")
    op.drop_table("rag_queries")
    op.drop_table("document_chunks")
    op.drop_table("evidence_records")
    op.drop_table("documents")
    op.drop_table("case_events")
    op.drop_table("case_parties")
    op.drop_table("cases")
    op.drop_table("user_devices")
    op.drop_table("sessions")
    op.drop_table("users")
