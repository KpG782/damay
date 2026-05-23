"""Shared test fixtures for the webhook + simulator tests.

We intentionally build a minimal FastAPI app here rather than importing
`damay_api.main` so this subagent's tests can run before backend-engineer
finalizes the top-level app wiring. Once `main.py` lands, this conftest
will be merged with the backend's by the orchestrator.
"""

from __future__ import annotations

from typing import AsyncIterator

import httpx
import pytest
import pytest_asyncio
from fastapi import FastAPI

from damay_api.routers import webhooks
from damay_api.services.whatsapp import InMemoryStore


@pytest.fixture
def settings_fixture() -> webhooks.WebhookSettings:
    return webhooks.WebhookSettings(
        twilio_auth_token="test-auth-token",
        twilio_webhook_validation=True,
        node_env="development",
        feature_demo_mode=True,
    )


@pytest.fixture
def store() -> InMemoryStore:
    return InMemoryStore()


@pytest.fixture
def app(store: InMemoryStore, settings_fixture: webhooks.WebhookSettings) -> FastAPI:
    application = FastAPI()
    application.include_router(webhooks.router)
    application.dependency_overrides[webhooks.get_store] = lambda: store
    application.dependency_overrides[webhooks.get_settings] = lambda: settings_fixture
    return application


@pytest_asyncio.fixture
async def client(app: FastAPI) -> AsyncIterator[httpx.AsyncClient]:
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(
        transport=transport, base_url="https://api.test"
    ) as ac:
        yield ac


# ---------------------------------------------------------------------------
# Seed helpers
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
