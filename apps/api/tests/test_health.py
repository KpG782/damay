"""Healthz behavior in mock mode."""

import pytest


@pytest.mark.asyncio
async def test_healthz_returns_200_in_mock_mode(client):
    r = await client.get("/healthz")
    assert r.status_code == 200
    body = r.json()
    assert body["status"] in ("ok", "degraded")
    assert body["checks"]["db"] == "ok"  # mock supabase pings as ok
    assert body["checks"]["stellar"] == "skipped"
    assert body["checks"]["twilio"] == "skipped"
    assert body["version"]
    assert body["requestId"] is not None or body.get("request_id") is not None


@pytest.mark.asyncio
async def test_request_id_header_propagation(client):
    r = await client.get("/healthz", headers={"X-Request-ID": "req_abc123"})
    assert r.status_code == 200
    assert r.headers["x-request-id"] == "req_abc123"
