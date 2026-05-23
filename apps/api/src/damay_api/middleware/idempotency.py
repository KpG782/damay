"""Idempotency middleware for POST endpoints.

If a request carries an ``Idempotency-Key`` header on a POST, the middleware:

1. Hashes the canonical request body.
2. Looks up ``(key, route)`` in the idempotency store.
3. If found with the same request_hash → returns the stored response verbatim.
4. If found with a different request_hash → 409 ``IDEMPOTENCY_CONFLICT``.
5. If not found → forwards the request and stores the response on 2xx.

Storage is pluggable: production uses the ``idempotency_keys`` Postgres table
(via the supabase client); tests use an in-memory dict.
"""

from __future__ import annotations

import hashlib
import json
from typing import Awaitable, Callable, Protocol

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from damay_api.middleware.logging import get_logger
from damay_api.middleware.request_id import current_request_id

IDEMPOTENCY_HEADER = "Idempotency-Key"


class IdempotencyStore(Protocol):
    async def get(self, key: str, route: str) -> dict | None: ...
    async def put(
        self,
        key: str,
        route: str,
        request_hash: str,
        response_status: int,
        response_body: dict,
    ) -> None: ...


class InMemoryIdempotencyStore:
    """Process-local store. Used by tests + as a fallback when Supabase is mocked."""

    def __init__(self) -> None:
        self._data: dict[tuple[str, str], dict] = {}

    async def get(self, key: str, route: str) -> dict | None:
        return self._data.get((key, route))

    async def put(
        self,
        key: str,
        route: str,
        request_hash: str,
        response_status: int,
        response_body: dict,
    ) -> None:
        self._data[(key, route)] = {
            "request_hash": request_hash,
            "response_status": response_status,
            "response_body": response_body,
        }

    def clear(self) -> None:
        self._data.clear()


def _hash_body(body: bytes) -> str:
    if not body:
        return hashlib.sha256(b"").hexdigest()
    try:
        parsed = json.loads(body)
        canonical = json.dumps(parsed, sort_keys=True, separators=(",", ":")).encode()
    except Exception:
        canonical = body
    return hashlib.sha256(canonical).hexdigest()


class IdempotencyMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, store: IdempotencyStore) -> None:
        super().__init__(app)
        self.store = store
        self.log = get_logger("damay.idempotency")

    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        if request.method != "POST":
            return await call_next(request)

        key = request.headers.get(IDEMPOTENCY_HEADER)
        if not key:
            return await call_next(request)

        route = request.url.path
        body_bytes = await request.body()
        req_hash = _hash_body(body_bytes)

        existing = await self.store.get(key, route)
        if existing is not None:
            if existing["request_hash"] != req_hash:
                self.log.warning("idempotency_conflict", key=key, route=route)
                return JSONResponse(
                    status_code=409,
                    content={
                        "error": {
                            "code": "IDEMPOTENCY_CONFLICT",
                            "message": "Idempotency key reused with different payload.",
                            "request_id": current_request_id(),
                        }
                    },
                )
            self.log.info("idempotency_replay", key=key, route=route)
            return JSONResponse(
                status_code=existing["response_status"],
                content=existing["response_body"],
            )

        # Re-inject body so downstream handlers can read it.
        async def receive() -> dict:
            return {"type": "http.request", "body": body_bytes, "more_body": False}

        request = Request(request.scope, receive=receive)
        response = await call_next(request)

        if 200 <= response.status_code < 300:
            # Buffer the response body to store + replay.
            chunks: list[bytes] = []
            async for chunk in response.body_iterator:  # type: ignore[attr-defined]
                chunks.append(chunk)
            body = b"".join(chunks)
            try:
                parsed = json.loads(body) if body else {}
            except json.JSONDecodeError:
                parsed = {}
            await self.store.put(key, route, req_hash, response.status_code, parsed)
            return Response(
                content=body,
                status_code=response.status_code,
                headers=dict(response.headers),
                media_type=response.media_type,
            )

        return response
