"""Auth dependency: missing token, bad token, valid token."""

import pytest


@pytest.mark.asyncio
async def test_protected_endpoint_requires_auth(client):
    r = await client.get("/v1/rounds")
    assert r.status_code == 401
    body = r.json()
    assert body["error"]["code"] == "UNAUTHENTICATED"


@pytest.mark.asyncio
async def test_protected_endpoint_rejects_bad_token(client):
    r = await client.get(
        "/v1/rounds", headers={"Authorization": "Bearer not-a-real-token"}
    )
    assert r.status_code == 401
    assert r.json()["error"]["code"] == "UNAUTHENTICATED"


@pytest.mark.asyncio
async def test_protected_endpoint_accepts_valid_token(client, auth_headers):
    r = await client.get("/v1/rounds", headers=auth_headers)
    assert r.status_code == 200
    body = r.json()
    assert "data" in body
