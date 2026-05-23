"""Reputation read flow + score math."""

from datetime import datetime, timedelta, timezone

import pytest

from damay_api.services.reputation import compute_score


def test_score_pure_function():
    now = datetime.now(timezone.utc)
    events = [
        {"event_type": "contribution", "weight": 1, "created_at": now.isoformat()},
        {"event_type": "contribution", "weight": 1, "created_at": now.isoformat()},
        {"event_type": "default", "weight": 1, "created_at": now.isoformat()},
        {"event_type": "payout", "weight": 1, "created_at": now.isoformat()},
    ]
    # 10 + 10 - 25 + 1 = -4
    assert compute_score(events, now=now) == -4


def test_score_decay():
    now = datetime.now(timezone.utc)
    old = (now - timedelta(days=90)).isoformat()
    events = [{"event_type": "contribution", "weight": 1, "created_at": old}]
    # ~3 decay periods → 10 * 0.99^3 ≈ 9.7 → floor → 9
    assert compute_score(events, now=now) == 9


@pytest.mark.asyncio
async def test_reputation_endpoint_member_not_found(client, auth_headers):
    r = await client.get(
        "/v1/reputation/00000000-0000-0000-0000-000000000999", headers=auth_headers
    )
    assert r.status_code == 404
    assert r.json()["error"]["code"] == "MEMBER_NOT_FOUND"
