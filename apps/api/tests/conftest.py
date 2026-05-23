"""Shared pytest fixtures.

Two app/client fixture sets coexist:

* ``app`` / ``client`` build a full ``damay_api`` FastAPI via ``main.create_app``.
  Used by backend-engineer's tests for rounds, members, contributions,
  reputation, idempotency, rate-limit, auth, health.

* ``webhook_app`` / ``webhook_client`` build a minimal app containing only
  the whatsapp-integrator's webhooks router with overridable
  ``WhatsAppStore`` / ``WebhookSettings``. Their webhook + simulator tests
  reference these via ``app`` / ``client`` shadows declared locally if they
  need the legacy names — but to preserve the original test files
  unchanged we keep ``app`` / ``client`` as request-scoped to the full app
  by default, and provide ``webhook_app`` / ``webhook_client`` to those
  tests via fixture aliasing below.
"""

from __future__ import annotations

import os
from contextlib import asynccontextmanager
from datetime import datetime, timedelta, timezone
from typing import AsyncIterator

import httpx
import pytest
import pytest_asyncio
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from jose import jwt

# Force mock mode + test env BEFORE importing the app.
os.environ.setdefault("NODE_ENV", "test")
os.environ.setdefault("REPUTATION_CONTRACT_ID", "")
os.environ.setdefault("PALUWAGAN_CONTRACT_ID", "")
os.environ.setdefault("SUPABASE_URL", "")
os.environ.setdefault("SUPABASE_SERVICE_ROLE_KEY", "")
os.environ.setdefault("TWILIO_ACCOUNT_SID", "")
os.environ.setdefault("TWILIO_AUTH_TOKEN", "")
os.environ.setdefault("SUPABASE_JWT_SECRET", "test-jwt-secret-please-change")
os.environ.setdefault("FEATURE_DEMO_MODE", "true")
# Match the constant the webhook tests sign against
# (tests use https://api.test/webhooks/twilio as the signing URL).
os.environ.setdefault("WEBHOOK_PUBLIC_BASE_URL", "https://api.test")
# Tests use a non-empty token to exercise verification; webhook
# validation is left enabled so signature paths are real.
os.environ["TWILIO_AUTH_TOKEN"] = "test-auth-token"
os.environ.setdefault("TWILIO_WEBHOOK_VALIDATION", "true")

from damay_api.clients.stellar import reset_stellar_singleton  # noqa: E402
from damay_api.clients.supabase import reset_supabase_singleton  # noqa: E402
from damay_api.clients.twilio import reset_twilio_singleton  # noqa: E402
from damay_api.config import get_settings  # noqa: E402
from damay_api.routers import webhooks  # noqa: E402
from damay_api.services.whatsapp import InMemoryStore  # noqa: E402
from damay_api.middleware.rate_limit import limiter  # noqa: E402

ORGANIZER_ID = "00000000-0000-0000-0000-000000000001"


@pytest.fixture(autouse=True)
def _reset_singletons():
    get_settings.cache_clear()
    reset_supabase_singleton()
    reset_stellar_singleton()
    reset_twilio_singleton()
    try:
        limiter.reset()
    except Exception:
        pass
    yield
    get_settings.cache_clear()
    reset_supabase_singleton()
    reset_stellar_singleton()
    reset_twilio_singleton()
    try:
        limiter.reset()
    except Exception:
        pass


def make_jwt(sub: str = ORGANIZER_ID, secret: str | None = None) -> str:
    secret = secret or os.environ["SUPABASE_JWT_SECRET"]
    payload = {
        "sub": sub,
        "email": "ken@example.com",
        "iat": datetime.now(timezone.utc),
        "exp": datetime.now(timezone.utc) + timedelta(hours=1),
    }
    return jwt.encode(payload, secret, algorithm="HS256")


@pytest.fixture
def auth_headers() -> dict[str, str]:
    return {"Authorization": f"Bearer {make_jwt()}"}


# ---------------------------------------------------------------------------
# Webhook-only app (used by whatsapp-integrator's tests).
# Detected via the presence of `settings_fixture` / `store` in the test file.
# ---------------------------------------------------------------------------


@pytest.fixture
def settings_fixture() -> webhooks.WebhookSettings:
    return webhooks.WebhookSettings(
        twilio_auth_token="test-auth-token",
        twilio_webhook_validation=True,
        node_env="development",
        feature_demo_mode=True,
        webhook_public_base_url="https://api.test",
    )


@pytest.fixture
def store() -> InMemoryStore:
    return InMemoryStore()


def _build_webhook_app(store: InMemoryStore, settings: webhooks.WebhookSettings) -> FastAPI:
    application = FastAPI()
    application.include_router(webhooks.router)
    application.dependency_overrides[webhooks.get_store] = lambda: store
    application.dependency_overrides[webhooks.get_settings] = lambda: settings
    return application


# ---------------------------------------------------------------------------
# Main app fixtures (preferred). Tests that asked for legacy webhook-only
# behaviour get a back-compat shim: if the test references `store` and
# `settings_fixture`, the `app`/`client` fixtures resolve to webhook-only.
# ---------------------------------------------------------------------------


@pytest_asyncio.fixture
async def app(request) -> AsyncIterator[FastAPI]:
    # Heuristic: webhook tests request both `store` and `settings_fixture`.
    fixturenames = getattr(request, "fixturenames", [])
    if "store" in set(fixturenames):
        st = request.getfixturevalue("store")
        sf = request.getfixturevalue("settings_fixture")
        yield _build_webhook_app(st, sf)
        return

    from main import create_app

    yield create_app()


@asynccontextmanager
async def _lifespan(application: FastAPI):
    cm = application.router.lifespan_context(application)
    await cm.__aenter__()
    try:
        yield
    finally:
        await cm.__aexit__(None, None, None)


@pytest_asyncio.fixture
async def client(app: FastAPI) -> AsyncIterator[httpx.AsyncClient]:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        async with _lifespan(app):
            yield ac


# ---------------------------------------------------------------------------
# Seed helpers used by whatsapp-integrator tests.
# ---------------------------------------------------------------------------


def seed_member(
    store: InMemoryStore,
    *,
    whatsapp_e164: str = "+639171234567",
    display_name: str = "Maria",
    member_id: str = "mem-1",
) -> dict:
    member = {
        "id": member_id,
        "whatsapp_e164": whatsapp_e164,
        "display_name": display_name,
        "stellar_account": None,
    }
    store.members[whatsapp_e164] = member
    return member


def seed_round(
    store: InMemoryStore,
    *,
    code: str = "BRG21",
    round_id: str = "rnd-1",
    name: str = "Barangay 21 Weekly",
    amount: int = 500,
    member_count: int = 6,
    status: str = "active",
) -> dict:
    r = {
        "id": round_id,
        "code": code,
        "name": name,
        "contribution_amount_php": amount,
        "member_count": member_count,
        "status": status,
    }
    store.rounds_by_code[code.upper()] = r
    store.rounds_by_id[round_id] = r
    return r


def open_cycle(
    store: InMemoryStore, *, round_id: str = "rnd-1", cycle_number: int = 1
) -> dict:
    cycle = {"cycle_number": cycle_number, "round_id": round_id}
    store.cycles[round_id] = cycle
    return cycle


def join_member(
    store: InMemoryStore,
    *,
    round_id: str = "rnd-1",
    member_id: str = "mem-1",
    position: int = 1,
) -> None:
    store.round_members[(round_id, member_id)] = {
        "round_id": round_id,
        "member_id": member_id,
        "payout_position": position,
    }
