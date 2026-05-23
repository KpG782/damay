"""SlowAPI rate limiter setup.

- 60/min default for public endpoints
- 600/min for authenticated endpoints

Rate-limit key is the JWT subject when present, else the client IP.
"""

from __future__ import annotations

from fastapi import Request
from slowapi import Limiter
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address
from starlette.responses import JSONResponse

from damay_api.middleware.request_id import current_request_id


def _key_func(request: Request) -> str:
    # Prefer authenticated subject so each organizer gets their own bucket.
    organizer_id = getattr(request.state, "organizer_id", None)
    if organizer_id:
        return f"org:{organizer_id}"
    return get_remote_address(request)


limiter = Limiter(key_func=_key_func, default_limits=["60/minute"])

PUBLIC_LIMIT = "60/minute"
AUTH_LIMIT = "600/minute"


def rate_limit_handler(_: Request, exc: RateLimitExceeded) -> JSONResponse:
    return JSONResponse(
        status_code=429,
        content={
            "error": {
                "code": "RATE_LIMITED",
                "message": f"Rate limit exceeded: {exc.detail}",
                "request_id": current_request_id(),
            }
        },
    )
