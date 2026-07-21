"""
Unit & API Integration tests for Case Management Module.
"""

from __future__ import annotations

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
class TestCasesAPI:
    """Test suite for /api/v1/cases endpoints."""

    async def test_file_and_retrieve_case(self, async_client: AsyncClient) -> None:
        # 1. Register Citizen User
        reg_res = await async_client.post(
            "/api/v1/auth/register",
            json={
                "email": "citizen.sharma@nyaya.in",
                "password": "Password123!",
                "full_name": "A. K. Sharma",
                "role": "citizen",
            },
        )
        token = reg_res.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # 2. File a new case
        case_payload = {
            "title": "Sharma vs Union Territory Property Dispute",
            "description": "Dispute concerning land parcel acquisition under Municipal Act.",
            "case_type": "Civil",
            "priority": "high",
            "parties": [
                {"party_name": "A. K. Sharma", "party_type": "petitioner"},
                {"party_name": "Municipal Corporation", "party_type": "respondent"},
            ],
        }
        create_res = await async_client.post("/api/v1/cases", json=case_payload, headers=headers)
        assert create_res.status_code == 201
        case_data = create_res.json()
        assert case_data["title"] == "Sharma vs Union Territory Property Dispute"
        assert case_data["status"] == "filed"
        assert len(case_data["parties"]) == 2
        assert len(case_data["events"]) == 1

        case_id = case_data["id"]

        # 3. Retrieve case details by ID
        get_res = await async_client.get(f"/api/v1/cases/{case_id}", headers=headers)
        assert get_res.status_code == 200
        assert get_res.json()["case_number"] == case_data["case_number"]

        # 4. Update status to under_review
        update_res = await async_client.put(
            f"/api/v1/cases/{case_id}",
            json={"status": "under_review"},
            headers=headers,
        )
        assert update_res.status_code == 200
        assert update_res.json()["status"] == "under_review"
        assert len(update_res.json()["events"]) == 2  # status_changed event logged
