"""
Nyaya-ZTA Case Management Schemas
=================================

Pydantic schemas for case filings, updates, timeline events, and pagination.
"""

from __future__ import annotations

from datetime import date, datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class CaseStatusEnum(str, Enum):
    FILED = "filed"
    UNDER_REVIEW = "under_review"
    HEARING = "hearing"
    JUDGMENT = "judgment"
    CLOSED = "closed"
    APPEALED = "appealed"


class CasePriorityEnum(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class PartyTypeEnum(str, Enum):
    PETITIONER = "petitioner"
    RESPONDENT = "respondent"
    WITNESS = "witness"
    INTERVENER = "intervener"


class CasePartyCreateSchema(BaseModel):
    party_name: str = Field(..., min_length=2, max_length=255)
    party_type: PartyTypeEnum
    user_id: str | None = None


class CasePartyResponseSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    case_id: str
    party_name: str
    party_type: str
    user_id: str | None = None
    created_at: datetime


class CaseEventCreateSchema(BaseModel):
    event_type: str = Field(..., min_length=2, max_length=100)
    description: str | None = None
    event_data: dict[str, Any] = Field(default_factory=dict)


class CaseEventResponseSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    case_id: str
    event_type: str
    description: str | None = None
    performed_by: str | None = None
    event_data: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime


class CaseCreateSchema(BaseModel):
    title: str = Field(..., min_length=5, max_length=500)
    description: str | None = None
    case_type: str = Field(..., min_length=2, max_length=100)
    priority: CasePriorityEnum = Field(default=CasePriorityEnum.MEDIUM)
    court_id: str | None = None
    parties: list[CasePartyCreateSchema] = Field(default_factory=list)


class CaseUpdateSchema(BaseModel):
    title: str | None = Field(default=None, min_length=5, max_length=500)
    description: str | None = None
    status: CaseStatusEnum | None = None
    priority: CasePriorityEnum | None = None
    assigned_judge: str | None = None
    assigned_lawyer: str | None = None
    next_hearing_date: date | None = None


class CaseResponseSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    case_number: str
    title: str
    description: str | None = None
    case_type: str
    status: CaseStatusEnum
    priority: CasePriorityEnum
    filed_by: str
    assigned_judge: str | None = None
    assigned_lawyer: str | None = None
    court_id: str | None = None
    filing_date: date
    next_hearing_date: date | None = None
    created_at: datetime
    updated_at: datetime
    parties: list[CasePartyResponseSchema] = Field(default_factory=list)
    events: list[CaseEventResponseSchema] = Field(default_factory=list)


class CaseListResponseSchema(BaseModel):
    items: list[CaseResponseSchema]
    total: int
    page: int
    page_size: number if False else int  # int
    total_pages: int
