"""Supabase REST client.

Backed by ``httpx.AsyncClient`` against the PostgREST surface that Supabase
exposes at ``${SUPABASE_URL}/rest/v1``. Service-role key only — backend never
uses the anon key. All writes go through here so RLS is bypassed via the
service-role JWT.

In tests / dev where Supabase isn't configured (``settings.supabase_mock_mode``)
this class falls back to an in-memory store so the API stays bootable.
"""

from __future__ import annotations

import asyncio
import copy
import uuid
from datetime import datetime, timezone
from typing import Any

import httpx
import pybreaker
import structlog
from tenacity import (
    AsyncRetrying,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential_jitter,
)

from damay_api.config import Settings

logger = structlog.get_logger("damay.supabase")


class SupabaseError(Exception):
    """Raised when Supabase returns a non-2xx response or is unreachable."""


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class InMemoryTable:
    """Trivial table for mock mode + tests."""

    def __init__(self, primary_keys: tuple[str, ...] = ("id",)) -> None:
        self.primary_keys = primary_keys
        self.rows: list[dict[str, Any]] = []

    def _pk(self, row: dict[str, Any]) -> tuple[Any, ...]:
        return tuple(row.get(k) for k in self.primary_keys)


class SupabaseClient:
    """Thin async REST client with retries + circuit breaker."""

    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.mock = settings.supabase_mock_mode
        self._mock_tables: dict[str, InMemoryTable] = {
            "organizers": InMemoryTable(),
            "members": InMemoryTable(),
            "rounds": InMemoryTable(),
            "round_members": InMemoryTable(primary_keys=("round_id", "member_id")),
            "contributions": InMemoryTable(),
            "payouts": InMemoryTable(),
            "messages": InMemoryTable(),
            "reputation_events": InMemoryTable(),
            "idempotency_keys": InMemoryTable(primary_keys=("key", "route")),
            "stellar_jobs": InMemoryTable(),
        }
        self._breaker = pybreaker.CircuitBreaker(fail_max=5, reset_timeout=30)
        self._client: httpx.AsyncClient | None = None
        if not self.mock:
            self._client = httpx.AsyncClient(
                base_url=f"{settings.supabase_url.rstrip('/')}/rest/v1",
                headers={
                    "apikey": settings.supabase_service_role_key,
                    "Authorization": f"Bearer {settings.supabase_service_role_key}",
                    "Content-Type": "application/json",
                    "Prefer": "return=representation",
                },
                timeout=httpx.Timeout(connect=2.0, read=5.0, write=5.0, pool=5.0),
            )

    async def aclose(self) -> None:
        if self._client is not None:
            await self._client.aclose()

    # ------------------------------------------------------------------
    # Healthcheck
    # ------------------------------------------------------------------
    async def ping(self) -> bool:
        if self.mock:
            return True
        assert self._client is not None
        try:
            r = await self._client.get("/", timeout=1.0)
            return r.status_code < 500
        except Exception:
            return False

    # ------------------------------------------------------------------
    # Core CRUD
    # ------------------------------------------------------------------
    async def insert(self, table: str, row: dict[str, Any]) -> dict[str, Any]:
        row = self._with_id(table, row)
        if self.mock:
            return self._mock_insert(table, row)
        return await self._http_insert(table, row)

    async def upsert(
        self,
        table: str,
        row: dict[str, Any],
        on_conflict: str | None = None,
    ) -> dict[str, Any]:
        if self.mock:
            return self._mock_upsert(table, row, on_conflict)
        return await self._http_upsert(table, row, on_conflict)

    async def select(
        self,
        table: str,
        filters: dict[str, Any] | None = None,
        order: str | None = None,
        limit: int | None = None,
    ) -> list[dict[str, Any]]:
        filters = filters or {}
        if self.mock:
            return self._mock_select(table, filters, order, limit)
        return await self._http_select(table, filters, order, limit)

    async def select_one(
        self, table: str, filters: dict[str, Any]
    ) -> dict[str, Any] | None:
        rows = await self.select(table, filters=filters, limit=1)
        return rows[0] if rows else None

    async def update(
        self, table: str, filters: dict[str, Any], patch: dict[str, Any]
    ) -> list[dict[str, Any]]:
        if self.mock:
            return self._mock_update(table, filters, patch)
        return await self._http_update(table, filters, patch)

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    @staticmethod
    def _with_id(table: str, row: dict[str, Any]) -> dict[str, Any]:
        row = copy.deepcopy(row)
        now = _now_iso()
        if table == "round_members":
            row.setdefault("joined_at", now)
            return row
        if table == "idempotency_keys":
            row.setdefault("created_at", now)
            return row
        if "id" not in row:
            row["id"] = str(uuid.uuid4())
        row.setdefault("created_at", now)
        if table != "reputation_events":
            row.setdefault("updated_at", now)
        return row

    # ------------------------------------------------------------------
    # Mock implementations
    # ------------------------------------------------------------------
    def _table(self, name: str) -> InMemoryTable:
        if name not in self._mock_tables:
            self._mock_tables[name] = InMemoryTable()
        return self._mock_tables[name]

    def _mock_insert(self, table: str, row: dict[str, Any]) -> dict[str, Any]:
        tbl = self._table(table)
        # uniqueness on PK
        if any(tbl._pk(r) == tbl._pk(row) for r in tbl.rows):
            raise SupabaseError(f"duplicate primary key on {table}")
        tbl.rows.append(row)
        return copy.deepcopy(row)

    def _mock_upsert(
        self, table: str, row: dict[str, Any], on_conflict: str | None
    ) -> dict[str, Any]:
        tbl = self._table(table)
        row = copy.deepcopy(row)
        keys = on_conflict.split(",") if on_conflict else list(tbl.primary_keys)
        for existing in tbl.rows:
            if all(existing.get(k) == row.get(k) for k in keys):
                existing.update(row)
                return copy.deepcopy(existing)
        return self._mock_insert(table, self._with_id(table, row))

    def _mock_select(
        self,
        table: str,
        filters: dict[str, Any],
        order: str | None,
        limit: int | None,
    ) -> list[dict[str, Any]]:
        tbl = self._table(table)
        rows = [r for r in tbl.rows if all(r.get(k) == v for k, v in filters.items())]
        if order:
            field = order.lstrip("-")
            rows.sort(key=lambda r: r.get(field) or "", reverse=order.startswith("-"))
        if limit:
            rows = rows[:limit]
        return [copy.deepcopy(r) for r in rows]

    def _mock_update(
        self, table: str, filters: dict[str, Any], patch: dict[str, Any]
    ) -> list[dict[str, Any]]:
        tbl = self._table(table)
        updated: list[dict[str, Any]] = []
        for r in tbl.rows:
            if all(r.get(k) == v for k, v in filters.items()):
                r.update(patch)
                r["updated_at"] = _now_iso()
                updated.append(copy.deepcopy(r))
        return updated

    # ------------------------------------------------------------------
    # HTTP implementations
    # ------------------------------------------------------------------
    async def _retrying(self):
        return AsyncRetrying(
            stop=stop_after_attempt(3),
            wait=wait_exponential_jitter(initial=0.1, max=2.0),
            retry=retry_if_exception_type((httpx.TransportError, httpx.HTTPStatusError)),
            reraise=True,
        )

    async def _request(
        self, method: str, path: str, *, params: Any = None, json: Any = None
    ) -> httpx.Response:
        assert self._client is not None

        async def call() -> httpx.Response:
            r = await self._client.request(method, path, params=params, json=json)
            if r.status_code >= 500:
                raise httpx.HTTPStatusError("server error", request=r.request, response=r)
            return r

        retryer = await self._retrying()
        try:
            async for attempt in retryer:
                with attempt:
                    return await self._breaker.call_async(call)
        except pybreaker.CircuitBreakerError as e:
            raise SupabaseError(f"circuit open: {e}") from e
        except Exception as e:
            raise SupabaseError(str(e)) from e
        raise SupabaseError("unreachable")

    async def _http_insert(self, table: str, row: dict[str, Any]) -> dict[str, Any]:
        r = await self._request("POST", f"/{table}", json=row)
        if r.status_code >= 400:
            raise SupabaseError(f"{table} insert failed: {r.status_code} {r.text}")
        data = r.json()
        return data[0] if isinstance(data, list) and data else data

    async def _http_upsert(
        self, table: str, row: dict[str, Any], on_conflict: str | None
    ) -> dict[str, Any]:
        params = {"on_conflict": on_conflict} if on_conflict else None
        assert self._client is not None
        client = self._client
        headers = {"Prefer": "resolution=merge-duplicates,return=representation"}
        r = await client.post(f"/{table}", params=params, json=row, headers=headers)
        if r.status_code >= 400:
            raise SupabaseError(f"{table} upsert failed: {r.status_code} {r.text}")
        data = r.json()
        return data[0] if isinstance(data, list) and data else data

    async def _http_select(
        self,
        table: str,
        filters: dict[str, Any],
        order: str | None,
        limit: int | None,
    ) -> list[dict[str, Any]]:
        params: dict[str, Any] = {"select": "*"}
        for k, v in filters.items():
            params[k] = f"eq.{v}"
        if order:
            params["order"] = order.lstrip("-") + (".desc" if order.startswith("-") else ".asc")
        if limit:
            params["limit"] = str(limit)
        r = await self._request("GET", f"/{table}", params=params)
        if r.status_code >= 400:
            raise SupabaseError(f"{table} select failed: {r.status_code} {r.text}")
        return r.json()

    async def _http_update(
        self, table: str, filters: dict[str, Any], patch: dict[str, Any]
    ) -> list[dict[str, Any]]:
        params = {k: f"eq.{v}" for k, v in filters.items()}
        r = await self._request("PATCH", f"/{table}", params=params, json=patch)
        if r.status_code >= 400:
            raise SupabaseError(f"{table} update failed: {r.status_code} {r.text}")
        return r.json()


_singleton_lock = asyncio.Lock()
_singleton: SupabaseClient | None = None


async def get_supabase(settings: Settings) -> SupabaseClient:
    global _singleton
    async with _singleton_lock:
        if _singleton is None:
            _singleton = SupabaseClient(settings)
        return _singleton


def reset_supabase_singleton() -> None:
    """Test hook to clear the cached client between cases."""
    global _singleton
    _singleton = None
