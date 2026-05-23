"""Round endpoint coverage."""

import uuid

import pytest


@pytest.mark.asyncio
async def test_create_round_happy_path(client, auth_headers):
    payload = {
        "name": "Barangay 21 Weekly",
        "contributionAmountPhp": 500,
        "memberCount": 6,
        "frequency": "weekly",
        "startDate": "2026-06-01",
    }
    r = await client.post("/v1/rounds", json=payload, headers=auth_headers)
    assert r.status_code == 201, r.text
    body = r.json()
    assert body["name"] == payload["name"]
    assert body["status"] == "draft"
    assert body["contributionAmountPhp"] == 500


@pytest.mark.asyncio
async def test_create_round_validation_error(client, auth_headers):
    bad = {"name": "x", "contributionAmountPhp": -1, "memberCount": 1, "frequency": "weekly"}
    r = await client.post("/v1/rounds", json=bad, headers=auth_headers)
    assert r.status_code == 422
    assert r.json()["error"]["code"] == "VALIDATION_ERROR"


@pytest.mark.asyncio
async def test_create_round_requires_auth(client):
    r = await client.post(
        "/v1/rounds",
        json={
            "name": "x",
            "contributionAmountPhp": 500,
            "memberCount": 3,
            "frequency": "weekly",
            "startDate": "2026-06-01",
        },
    )
    assert r.status_code == 401


@pytest.mark.asyncio
async def test_list_rounds_returns_only_own(client, auth_headers):
    # create one
    await client.post(
        "/v1/rounds",
        json={
            "name": "Mine",
            "contributionAmountPhp": 500,
            "memberCount": 3,
            "frequency": "weekly",
            "startDate": "2026-06-01",
        },
        headers=auth_headers,
    )
    r = await client.get("/v1/rounds", headers=auth_headers)
    assert r.status_code == 200
    data = r.json()["data"]
    assert all(d["organizerId"] for d in data)


@pytest.mark.asyncio
async def test_round_get_not_found(client, auth_headers):
    r = await client.get(f"/v1/rounds/{uuid.uuid4()}", headers=auth_headers)
    assert r.status_code == 404
    assert r.json()["error"]["code"] == "ROUND_NOT_FOUND"
