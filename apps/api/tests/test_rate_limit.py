"""SlowAPI: 60/min public — the 61st request inside a minute should 429.

We exercise the public /healthz limit. Authenticated routes get a much higher
ceiling (600/min) which would be impractical to exhaust in a unit test.
"""

import pytest


@pytest.mark.asyncio
async def test_public_rate_limit_returns_429(client):
    # Hit healthz 61 times in a tight loop. Local SlowAPI uses in-memory storage.
    last_status = 200
    for _ in range(61):
        r = await client.get("/healthz")
        last_status = r.status_code
        if last_status == 429:
            break
    assert last_status == 429, "expected to be rate-limited within 61 requests"
    body = r.json()
    assert body["error"]["code"] == "RATE_LIMITED"
