"""GET /healthz — deep liveness check.

Pings DB, Soroban RPC, Twilio in parallel with 1s timeouts. Any *required*
failure ⇒ 503. Skipped checks (mock mode) don't fail.
"""

from __future__ import annotations

import asyncio
from datetime import datetime, timezone
from typing import Literal

from fastapi import APIRouter, Request, Response, status

from damay_api.middleware.rate_limit import PUBLIC_LIMIT, limiter

from damay_api import __version__
from damay_api.deps import SettingsDep, StellarDep, SupabaseDep, TwilioDep
from damay_api.middleware.request_id import current_request_id
from damay_api.models.responses import HealthChecks, HealthResponse

router = APIRouter(tags=["health"])

CheckStatus = Literal["ok", "fail", "skipped"]


async def _with_timeout(coro, default: CheckStatus = "fail", timeout: float = 1.0):
    try:
        ok = await asyncio.wait_for(coro, timeout=timeout)
        return "ok" if ok else default
    except asyncio.TimeoutError:
        return "fail"
    except Exception:
        return "fail"


@router.get("/healthz", response_model=HealthResponse)
@limiter.limit(PUBLIC_LIMIT)
async def healthz(
    request: Request,
    response: Response,
    settings: SettingsDep,
    supabase: SupabaseDep,
    stellar: StellarDep,
    twilio: TwilioDep,
) -> HealthResponse:
    db_task = _with_timeout(supabase.ping())
    if settings.stellar_mock_mode:
        stellar_status: CheckStatus = "skipped"
        stellar_task = None
    else:
        stellar_task = _with_timeout(stellar.soroban_health())
    if settings.twilio_mock_mode:
        twilio_status: CheckStatus = "skipped"
        twilio_task = None
    else:
        twilio_task = _with_timeout(twilio.ping())

    tasks = [t for t in (db_task, stellar_task, twilio_task) if t is not None]
    results = await asyncio.gather(*tasks)
    it = iter(results)
    db_status: CheckStatus = next(it)
    if stellar_task is not None:
        stellar_status = next(it)
    if twilio_task is not None:
        twilio_status = next(it)

    checks = HealthChecks(db=db_status, stellar=stellar_status, twilio=twilio_status)

    # DB failure is the only hard fail.
    hard_fail = db_status == "fail"
    if hard_fail:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        overall: Literal["ok", "degraded", "down"] = "down"
    elif "fail" in (stellar_status, twilio_status):
        overall = "degraded"
    else:
        overall = "ok"

    return HealthResponse(
        status=overall,
        checks=checks,
        timestamp=datetime.now(timezone.utc),
        version=__version__,
        request_id=current_request_id(),
    )
