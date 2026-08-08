"""
Migration for PostgreSQL pgvector extension and HNSW vector index
Revision ID: 0003_pgvector_migration
Revises: 0002_add_vadp_verification_contracts
Create Date: 2026-08-05
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = '0003_pgvector_migration'
down_revision = '0002_add_vadp_verification_contracts'
branch_labels = None
depends_on = None


def upgrade():
    # Enable pgvector extension
    op.execute("CREATE EXTENSION IF NOT EXISTS vector;")
    
    # Add vector column to document_chunks table if upgrading to PostgreSQL
    bind = op.get_bind()
    if bind.dialect.name == 'postgresql':
        op.execute("ALTER TABLE document_chunks ADD COLUMN IF NOT EXISTS embedding vector(384);")
        op.execute("CREATE INDEX IF NOT EXISTS idx_document_chunks_vector_hnsw ON document_chunks USING hnsw (embedding vector_cosine_ops);")


def downgrade():
    bind = op.get_bind()
    if bind.dialect.name == 'postgresql':
        op.execute("DROP INDEX IF EXISTS idx_document_chunks_vector_hnsw;")
        op.execute("ALTER TABLE document_chunks DROP COLUMN IF EXISTS embedding;")
