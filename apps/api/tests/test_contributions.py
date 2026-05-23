"""Contribution flow in mock mode — verifies a stellar_jobs row is queued."""

import pytest

from damay_api.clients.supabase import get_supabase
from damay_api.config import get_settings


async def _create_round_with_member(client, auth_headers):
    r = await client.post(
        "/v1/rounds",
        json={
            "name": "Test Round",
            "contributionAmountPhp": 500,
            "memberCount": 3,
            "frequency": "weekly",
            "startDate": "2026-06-01",
        },
        headers=auth_headers,
    )
    assert r.status_code == 201
    round_id = r.json()["id"]

    r = await client.post(
        "/v1/members",
        json={"whatsappE164": "+639171234567", "displayName": "Maria Santos"},
        headers=auth_headers,
    )
    assert r.status_code == 201
    member_id = r.json()["id"]

    r = await client.post(
        f"/v1/rounds/{round_id}/members",
        json={"memberId": member_id, "payoutPosition": 1},
        headers=auth_headers,
    )
    assert r.status_code == 201, r.text
    return round_id, member_id


@pytest.mark.asyncio
async def test_post_contribution_enqueues_stellar_job(client, auth_headers):
    round_id, member_id = await _create_round_with_member(client, auth_headers)

    r = await client.post(
        "/v1/contributions",
        json={
            "roundId": round_id,
            "memberId": member_id,
            "cycleNumber": 1,
            "amountPhp": 500,
        },
        headers=auth_headers,
    )
    assert r.status_code == 202, r.text
    body = r.json()
    assert body["status"] == "pending"
    assert body["contributionId"]
    assert body["jobId"]

    # Verify a stellar_jobs row was actually written.
    supabase = await get_supabase(get_settings())
    jobs = await supabase.select("stellar_jobs", filters={"job_type": "contribute"})
    assert len(jobs) == 1
    assert jobs[0]["status"] == "queued"


@pytest.mark.asyncio
async def test_post_contribution_is_naturally_idempotent_on_round_member_cycle(
    client, auth_headers
):
    round_id, member_id = await _create_round_with_member(client, auth_headers)

    body = {
        "roundId": round_id,
        "memberId": member_id,
        "cycleNumber": 1,
        "amountPhp": 500,
    }
    r1 = await client.post("/v1/contributions", json=body, headers=auth_headers)
    r2 = await client.post("/v1/contributions", json=body, headers=auth_headers)
    assert r1.status_code == 202
    assert r2.status_code == 202
    # Same contribution row returned
    assert r1.json()["contributionId"] == r2.json()["contributionId"]
