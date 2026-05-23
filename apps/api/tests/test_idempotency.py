"""Idempotency middleware: replay returns stored response, conflict on changed body."""

import pytest


@pytest.mark.asyncio
async def test_idempotent_post_replay(client, auth_headers):
    headers = {**auth_headers, "Idempotency-Key": "test-key-1"}
    payload = {
        "name": "Idempotent Round",
        "contributionAmountPhp": 500,
        "memberCount": 4,
        "frequency": "weekly",
        "startDate": "2026-06-01",
    }
    r1 = await client.post("/v1/rounds", json=payload, headers=headers)
    r2 = await client.post("/v1/rounds", json=payload, headers=headers)
    assert r1.status_code == 201
    assert r2.status_code == 201
    # Same id — replay returned stored response
    assert r1.json()["id"] == r2.json()["id"]


@pytest.mark.asyncio
async def test_idempotency_conflict_on_changed_body(client, auth_headers):
    headers = {**auth_headers, "Idempotency-Key": "test-key-2"}
    base = {
        "name": "First",
        "contributionAmountPhp": 500,
        "memberCount": 4,
        "frequency": "weekly",
        "startDate": "2026-06-01",
    }
    r1 = await client.post("/v1/rounds", json=base, headers=headers)
    assert r1.status_code == 201
    different = {**base, "name": "Second"}
    r2 = await client.post("/v1/rounds", json=different, headers=headers)
    assert r2.status_code == 409
    assert r2.json()["error"]["code"] == "IDEMPOTENCY_CONFLICT"
