"""Tests for `POST /dev/simulate-message`.

The simulator must:
    * run end-to-end through the same handler as the live webhook
    * be 404 when NODE_ENV=production AND FEATURE_DEMO_MODE != true
    * be reachable when EITHER NODE_ENV != production OR FEATURE_DEMO_MODE=true
"""

from __future__ import annotations

import pytest

from tests.conftest import (
    join_member,
    open_cycle,
    seed_member,
    seed_round,
)


class TestSimulateEnabled:
    async def test_simulate_join_runs_full_flow(self, client, store):
        seed_member(store)
        seed_round(store)
        payload = {"whatsapp_e164": "+639171234567", "body": "JOIN BRG21"}
        res = await client.post("/dev/simulate-message", json=payload)
        assert res.status_code == 200
        assert "Welcome sa Barangay 21" in res.text
        # round_members row created via simulator (proves same handler path).
        assert ("rnd-1", "mem-1") in store.round_members

    async def test_simulate_pay_runs_full_flow(self, client, store):
        seed_member(store)
        seed_round(store)
        join_member(store)
        open_cycle(store, cycle_number=1)
        payload = {"whatsapp_e164": "+639171234567", "body": "PAY"}
        res = await client.post("/dev/simulate-message", json=payload)
        assert res.status_code == 200
        assert "Salamat" in res.text
        assert ("rnd-1", "mem-1", 1) in store.contributions

    async def test_synthetic_sid_is_unique_per_call(self, client, store):
        seed_member(store)
        # Two HELP calls should both succeed; dedupe is keyed on synth sid.
        payload = {"whatsapp_e164": "+639171234567", "body": "HELP"}
        r1 = await client.post("/dev/simulate-message", json=payload)
        r2 = await client.post("/dev/simulate-message", json=payload)
        assert r1.status_code == 200 and r2.status_code == 200
        # Two inbound + two outbound rows.
        inbound = [m for m in store.messages.values() if m["direction"] == "in"]
        outbound = [m for m in store.messages.values() if m["direction"] == "out"]
        assert len(inbound) == 2
        assert len(outbound) == 2
        # All synthetic ids carry the `sim-` prefix per spec.
        for m in inbound:
            assert m["twilio_sid"].startswith("sim-")

    async def test_simulate_missing_e164_400(self, client, store):
        res = await client.post("/dev/simulate-message", json={"body": "HELP"})
        assert res.status_code == 400


class TestSimulateDisabledInProd:
    async def test_returns_404_when_prod_and_demo_off(
        self, client, settings_fixture
    ):
        settings_fixture.node_env = "production"
        settings_fixture.feature_demo_mode = False
        res = await client.post(
            "/dev/simulate-message",
            json={"whatsapp_e164": "+639171234567", "body": "HELP"},
        )
        assert res.status_code == 404

    async def test_still_enabled_in_prod_when_demo_flag_set(
        self, client, store, settings_fixture
    ):
        seed_member(store)
        settings_fixture.node_env = "production"
        settings_fixture.feature_demo_mode = True
        res = await client.post(
            "/dev/simulate-message",
            json={"whatsapp_e164": "+639171234567", "body": "HELP"},
        )
        assert res.status_code == 200
        assert "DAMAY commands" in res.text
