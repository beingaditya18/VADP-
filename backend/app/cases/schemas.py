"""
VADP Case Management Schemas
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
    metadata_: dict[str, Any] = Field(default_factory=dict, alias="metadata_")
    created_at: datetime
    updated_at: datetime
    parties: list[CasePartyResponseSchema] = Field(default_factory=list)
    events: list[CaseEventResponseSchema] = Field(default_factory=list)


class CaseListResponseSchema(BaseModel):
    items: list[CaseResponseSchema]
    total: int
    page: int
    page_size: int
    total_pages: int


class HearingScheduleCreateSchema(BaseModel):
    case_id: str
    scheduled_date: str = Field(..., description="ISO datetime string e.g. 2026-08-15T10:30:00Z")
    courtroom: str = Field(default="Courtroom 1")
    hearing_type: str = Field(default="Initial Hearing")
    purpose: str | None = None
    judge_notes: str | None = None


class HearingScheduleResponseSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    case_id: str
    scheduled_date: str
    courtroom: str
    hearing_type: str
    status: str
    purpose: str | None = None
    judge_notes: str | None = None
    scheduled_by: str
    created_at: datetime


class CaseTimelineNodeSchema(BaseModel):
    id: str
    timestamp: str
    milestone_type: str  # FILING, EVIDENCE, HEARING, RULING, STATUS_CHANGE
    title: str
    description: str
    actor_id: str | None = None
    badge_color: str
    metadata: dict[str, Any] = Field(default_factory=dict)


class CaseTimelineResponseSchema(BaseModel):
    case_id: str
    case_number: str
    total_milestones: int
    timeline: list[CaseTimelineNodeSchema]


class MegaCaseSummarySchema(BaseModel):
    case_id: str
    case_number: str
    title: str
    executive_summary: str
    key_legal_disputes: list[str]
    plaintiff_arguments: list[str]
    defense_arguments: list[str]
    critical_evidence_summary: list[str]
    applicable_statutes: list[str]
    recommended_judicial_next_steps: list[str]
    confidence_score: float


class PrecedentRadarItemSchema(BaseModel):
    citation: str
    case_title: str
    relevance_score: float
    status: str  # APPLICABLE, OVERRULED, DISTINGUISHED, CONTRADICTORY
    summary: str
    court_jurisdiction: str


class PrecedentRadarResponseSchema(BaseModel):
    case_id: str
    analyzed_at: datetime
    total_precedents_analyzed: int
    contradiction_count: int
    items: list[PrecedentRadarItemSchema]


class BailOutcomeFactorSchema(BaseModel):
    feature: str
    impact_score: float  # e.g., +0.25 or -0.15
    direction: str  # POSITIVE, NEGATIVE
    description: str


class BailOutcomeEstimatorSchema(BaseModel):
    case_id: str
    bail_grant_probability: float  # 0 to 100%
    sentencing_risk_level: str  # LOW, MEDIUM, HIGH
    shap_factors: list[BailOutcomeFactorSchema]
    explanation: str
