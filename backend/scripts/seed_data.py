"""
Nyaya-ZTA Synthetic Legal Data & Demo Database Seeder
=====================================================

Populates SQLite3 database with realistic jurisdiction-agnostic synthetic judicial data:
  - Users across all 4 roles (Citizen, Lawyer, Judge, Admin)
  - Sample Access Control Policies (ABAC)
  - Cases with parties, events, and document upload records
  - Evidence integrity verification records
  - Sealed audit ledger blocks with ECDSA signatures
"""

from __future__ import annotations

import asyncio
from datetime import datetime, timezone
from pathlib import Path

from app.auth.models import User
from app.auth.repository import UserRepository
from app.authorization.service import AuthorizationService
from app.authorization.schemas import PolicyCreateSchema
from app.cases.models import Case, CaseEvent, CaseParty
from app.cases.repository import CaseRepository
from app.core.security import hash_password
from app.db.init_db import init_db
from app.db.session import get_session_factory
from app.evidence.models import EvidenceRecord
from app.ledger.schemas import LedgerEntryCreateSchema
from app.ledger.service import LedgerService


async def seed_synthetic_data() -> None:
    print("[SEED] Initializing Nyaya-ZTA Database & Tables...")
    await init_db()

    session_factory = get_session_factory()
    async with session_factory() as db:
        user_repo = UserRepository(db)
        case_repo = CaseRepository(db)
        ledger_service = LedgerService(db)

        print("[SEED] Seeding Users...")
        # Check if users already exist
        admin_user = await user_repo.get_by_email("admin@nyaya.gov.in")
        if not admin_user:
            admin_user = User(
                email="admin@nyaya.gov.in",
                hashed_password=hash_password("AdminPassword123!"),
                full_name="Chief System Administrator",
                role="admin",
                is_active=True,
            )
            db.add(admin_user)

        judge_user = await user_repo.get_by_email("judge.sharma@nyaya.gov.in")
        if not judge_user:
            judge_user = User(
                email="judge.sharma@nyaya.gov.in",
                hashed_password=hash_password("JudgePassword123!"),
                full_name="Justice A. K. Sharma",
                role="judge",
                is_active=True,
            )
            db.add(judge_user)

        lawyer_user = await user_repo.get_by_email("advocate.verma@nyaya.in")
        if not lawyer_user:
            lawyer_user = User(
                email="advocate.verma@nyaya.in",
                hashed_password=hash_password("LawyerPassword123!"),
                full_name="Advocate R. Verma",
                role="lawyer",
                is_active=True,
                bar_number="MAH/5678/2020",
            )
            db.add(lawyer_user)

        citizen_user = await user_repo.get_by_email("citizen.kumar@nyaya.in")
        if not citizen_user:
            citizen_user = User(
                email="citizen.kumar@nyaya.in",
                hashed_password=hash_password("CitizenPassword123!"),
                full_name="Rajesh Kumar",
                role="citizen",
                is_active=True,
            )
            db.add(citizen_user)

        await db.flush()

        authz_service = AuthorizationService(db)

        print("[SEED] Seeding Default Zero-Trust Access Control Policies...")
        existing_policies = await authz_service.list_policies()
        if not existing_policies:
            p1 = PolicyCreateSchema(
                policy_name="Judge Full Case Review Policy",
                description="Judges have full read/write permission on assigned cases when device is trusted.",
                allowed_roles=["judge", "admin"],
                resource_type="case",
                action="read",
                conditions={"device_trust_level": {"$gte": "medium"}},
                priority=100,
            )
            p2 = PolicyCreateSchema(
                policy_name="Lawyer Case Access Policy",
                description="Lawyers can access cases where they are assigned as legal counsel.",
                allowed_roles=["lawyer", "admin"],
                resource_type="case",
                action="read",
                conditions={"is_assigned_lawyer": True},
                priority=90,
            )
            await authz_service.create_policy(p1)
            await authz_service.create_policy(p2)

        print("[SEED] Seeding Synthetic Legal Cases...")
        c1 = Case(
            case_number="NYA-CIV-2026-0001",
            title="Kumar vs UT Land Acquisition Authority",
            description="Petition challenging municipal parcel acquisition without prior statutory notice under Municipal Act.",
            case_type="Civil",
            status="under_review",
            priority="high",
            filed_by=citizen_user.id,
            assigned_judge=judge_user.id,
            assigned_lawyer=lawyer_user.id,
            filing_date=datetime.now(timezone.utc),
        )
        db.add(c1)
        await db.flush()

        p_petitioner = CaseParty(case_id=c1.id, party_name="Rajesh Kumar", party_type="petitioner", user_id=citizen_user.id)
        p_respondent = CaseParty(case_id=c1.id, party_name="UT Land Acquisition Board", party_type="respondent")
        db.add(p_petitioner)
        db.add(p_respondent)

        ev_filing = CaseEvent(
            case_id=c1.id,
            event_type="case_filed",
            description="Petition filed electronically by Rajesh Kumar.",
            performed_by=citizen_user.id,
            event_data={"case_type": "Civil"},
        )
        db.add(ev_filing)

        print("[SEED] Seeding Tamper-Evident Audit Ledger...")
        await ledger_service.record_entry(
            LedgerEntryCreateSchema(
                entry_type="case_access",
                action=f"Filed initial petition case NYA-CIV-2026-0001",
                resource_type="case",
                resource_id=c1.id,
            ),
            actor_id=citizen_user.id,
        )

        await ledger_service.record_entry(
            LedgerEntryCreateSchema(
                entry_type="policy_evaluation",
                action="Evaluated Judge bench assignment access policy",
                resource_type="case",
                resource_id=c1.id,
            ),
            actor_id=judge_user.id,
        )

        # Seal block
        await ledger_service.seal_current_block()

        await db.commit()
        print("[SEED] Synthetic Legal Data Seeded Successfully!")


if __name__ == "__main__":
    asyncio.run(seed_synthetic_data())
