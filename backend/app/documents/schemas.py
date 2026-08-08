"""
VADP Document Schemas
==========================

Pydantic schemas for Document responses.
"""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class DocumentResponseSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    case_id: str
    uploaded_by: str
    file_name: str
    file_type: str | None = None
    file_size: int | None = None
    content_hash: str
    is_verified: bool
    created_at: datetime


class DocumentListResponseSchema(BaseModel):
    items: list[DocumentResponseSchema]
    total: int
