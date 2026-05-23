"""Request-ID middleware.

Generates / propagates ``X-Request-ID`` and attaches it to ``request.state``
and to a contextvar that the structlog processor reads, so every log line
during a request carries the same correlation ID.
"""

from __future__ import annotations

import contextvars
import uuid

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

REQUEST_ID_HEADER = "X-Request-ID"
request_id_ctx: contextvars.ContextVar[str | None] = contextvars.ContextVar(
    "request_id", default=None
)


def current_request_id() -> str | None:
    """Return the request id for the current async task / context."""
    return request_id_ctx.get()


def _new_request_id() -> str:
    return f"req_{uuid.uuid4().hex[:24]}"


class RequestIdMiddleware(BaseHTTPMiddleware):
    """Stamp every request + response with a stable ``X-Request-ID``."""

    async def dispatch(self, request: Request, call_next):  # type: ignore[override]
        incoming = request.headers.get(REQUEST_ID_HEADER)
        rid = incoming if incoming else _new_request_id()
        token = request_id_ctx.set(rid)
        request.state.request_id = rid
        try:
            response: Response = await call_next(request)
        finally:
            request_id_ctx.reset(token)
        response.headers[REQUEST_ID_HEADER] = rid
        return response
