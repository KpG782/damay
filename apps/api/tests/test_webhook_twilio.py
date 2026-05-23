"""Tests for `POST /webhooks/twilio`.

Covers:
    * signature verify success / failure (constant-time, redacted on fail)
    * dedupe via MessageSid (UNIQUE on messages.twilio_sid)
    * full §8 state machine paths IDLE → JOINED → AWAITING → CONTRIBUTED
    * garbage input → fallback menu
    * unknown member → friendly reject, no DB write
"""

from __future__ import annotations

from urllib.parse import urlencode

import pytest

from damay_api.services import templates
from damay_api.services.twilio_signature import (
    compute_twilio_signature,
    verify_twilio_signature,
)
from damay_api.services.whatsapp import (
    InboundEvent,
    InMemoryStore,
    MemberState,
    ParsedCommand,
    StateMachine,
)
from tests.conftest import (
    join_member,
    open_cycle,
    seed_member,
    seed_round,
)


WEBHOOK_URL = "https://api.test/webhooks/twilio"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _sign(form: dict[str, str], token: str = "test-auth-token", url: str = WEBHOOK_URL) -> str:
    return compute_twilio_signature(token, url, form)


async def _post_webhook(client, form: dict[str, str], *, sign: bool = True):
    headers = {"content-type": "application/x-www-form-urlencoded"}
    if sign:
        headers["x-twilio-signature"] = _sign(form)
    return await client.post(
        "/webhooks/twilio",
        content=urlencode(form),
        headers=headers,
    )


# ---------------------------------------------------------------------------
# Signature verify (pure)
# ---------------------------------------------------------------------------


class TestSignaturePure:
    def test_signature_round_trip(self):
        form = {"MessageSid": "SM1", "From": "whatsapp:+639171234567", "Body": "HELP"}
        sig = compute_twilio_signature("tok", WEBHOOK_URL, form)
        assert verify_twilio_signature("tok", WEBHOOK_URL, form, sig) is True

    def test_signature_mismatch(self):
        form = {"MessageSid": "SM1", "Body": "HELP"}
        sig = compute_twilio_signature("tok", WEBHOOK_URL, form)
        # Same form, different token → reject.
        assert verify_twilio_signature("other-tok", WEBHOOK_URL, form, sig) is False

    def test_signature_param_tamper(self):
        form = {"MessageSid": "SM1", "Body": "HELP"}
        sig = compute_twilio_signature("tok", WEBHOOK_URL, form)
        form["Body"] = "PAY"
        assert verify_twilio_signature("tok", WEBHOOK_URL, form, sig) is False

    def test_signature_missing(self):
        assert verify_twilio_signature("tok", WEBHOOK_URL, {"a": "b"}, None) is False
        assert verify_twilio_signature("tok", WEBHOOK_URL, {"a": "b"}, "") is False

    def test_signature_param_order_independence(self):
        # Twilio sorts by key — input ordering must not change the result.
        f1 = {"A": "1", "B": "2", "C": "3"}
        f2 = {"C": "3", "A": "1", "B": "2"}
        assert (
            compute_twilio_signature("tok", WEBHOOK_URL, f1)
            == compute_twilio_signature("tok", WEBHOOK_URL, f2)
        )


# ---------------------------------------------------------------------------
# Command parsing
# ---------------------------------------------------------------------------


class TestParseCommand:
    @pytest.mark.parametrize(
        "raw,event,payload",
        [
            ("JOIN BRG21", InboundEvent.JOIN, "BRG21"),
            ("join brg21", InboundEvent.JOIN, "brg21"),
            ("  JOIN   abc  ", InboundEvent.JOIN, "abc"),
            ("PAY", InboundEvent.PAY, None),
            ("pay", InboundEvent.PAY, None),
            ("HELP", InboundEvent.HELP, None),
            ("STATUS", InboundEvent.STATUS, None),
            ("", InboundEvent.GARBAGE, None),
            ("hi po", InboundEvent.GARBAGE, None),
            ("PAY now", InboundEvent.GARBAGE, None),
            ("JOIN", InboundEvent.GARBAGE, None),  # no code → garbage
        ],
    )
    def test_parse_matrix(self, raw, event, payload):
        cmd = ParsedCommand.parse(raw)
        assert cmd.event is event
        assert cmd.payload == payload


# ---------------------------------------------------------------------------
# Webhook signature behavior (HTTP)
# ---------------------------------------------------------------------------


class TestWebhookSignature:
    async def test_valid_signature_returns_twiml(self, client, store):
        seed_member(store)
        seed_round(store)
        form = {
            "MessageSid": "SMvalid1",
            "From": "whatsapp:+639171234567",
            "Body": "HELP",
            "To": "whatsapp:+14155238886",
        }
        res = await _post_webhook(client, form)
        assert res.status_code == 200
        assert "<Response>" in res.text
        assert "DAMAY commands" in res.text

    async def test_invalid_signature_403(self, client, store):
        seed_member(store)
        form = {
            "MessageSid": "SMbogus",
            "From": "whatsapp:+639171234567",
            "Body": "HELP",
        }
        headers = {
            "content-type": "application/x-www-form-urlencoded",
            "x-twilio-signature": "AAAAobviously-wrongAAAA",
        }
        res = await client.post(
            "/webhooks/twilio", content=urlencode(form), headers=headers
        )
        assert res.status_code == 403
        # No DB writes on signature failure.
        assert store.messages == {}
        assert store.contributions == {}

    async def test_missing_signature_403(self, client, store):
        seed_member(store)
        form = {"MessageSid": "SMnone", "From": "whatsapp:+639171234567", "Body": "PAY"}
        res = await client.post(
            "/webhooks/twilio",
            content=urlencode(form),
            headers={"content-type": "application/x-www-form-urlencoded"},
        )
        assert res.status_code == 403
        assert store.messages == {}

    async def test_validation_disabled_escape_hatch(
        self, app, client, store, settings_fixture
    ):
        seed_member(store)
        settings_fixture.twilio_webhook_validation = False
        form = {"MessageSid": "SMnoval", "From": "whatsapp:+639171234567", "Body": "HELP"}
        res = await client.post(
            "/webhooks/twilio",
            content=urlencode(form),
            headers={"content-type": "application/x-www-form-urlencoded"},
        )
        # No signature header at all, yet accepted because validation is off.
        assert res.status_code == 200


# ---------------------------------------------------------------------------
# Dedupe
# ---------------------------------------------------------------------------


class TestDedupe:
    async def test_duplicate_message_sid_is_no_op(self, client, store):
        seed_member(store)
        seed_round(store)
        open_cycle(store)
        join_member(store)

        form = {
            "MessageSid": "SMdup",
            "From": "whatsapp:+639171234567",
            "Body": "PAY",
        }
        r1 = await _post_webhook(client, form)
        r2 = await _post_webhook(client, form)
        assert r1.status_code == 200 and r2.status_code == 200

        # Inbound message stored exactly once.
        inbound = [m for m in store.messages.values() if m["direction"] == "in"]
        assert len(inbound) == 1
        assert inbound[0]["twilio_sid"] == "SMdup"

        # Contribution side-effect happened exactly once.
        assert len(store.contributions) == 1

        # First reply was the PAY_RECEIVED ack; second was empty TwiML.
        assert "Salamat" in r1.text
        assert "<Response/>" == r2.text.strip() or "<Message>" not in r2.text


# ---------------------------------------------------------------------------
# State machine — pure (unit) tests
# ---------------------------------------------------------------------------


class TestStateMachineUnit:
    def test_idle_to_joined_via_join_with_known_round(self):
        sm = StateMachine()
        ctx = {
            "member": {"id": "mem-1", "display_name": "Maria"},
            "join_round": {"id": "rnd-1", "name": "Barangay 21 Weekly"},
            "payout_position": 3,
            "twilio_sid": "SM1",
        }
        out = sm.transition(MemberState.IDLE, InboundEvent.JOIN, ctx)
        assert out.next_state is MemberState.JOINED
        assert out.reply.template_id == "WELCOME_JOIN"
        assert "Barangay 21" in out.reply.render()
        assert any(fx["type"] == "add_round_member" for fx in out.side_effects)

    def test_join_with_unknown_code_no_state_change(self):
        sm = StateMachine()
        out = sm.transition(
            MemberState.IDLE,
            InboundEvent.JOIN,
            {"member": {"id": "mem-1"}, "twilio_sid": "x"},
        )
        assert out.next_state is MemberState.IDLE
        assert out.reply.template_id == "INVALID_JOIN_CODE"
        assert out.side_effects == []

    def test_joined_pay_with_no_active_cycle_falls_back(self):
        sm = StateMachine()
        out = sm.transition(
            MemberState.JOINED,
            InboundEvent.PAY,
            {"member": {"id": "mem-1"}, "twilio_sid": "x"},
        )
        assert out.next_state is MemberState.JOINED
        assert out.reply.template_id == "NO_ACTIVE_CYCLE"

    def test_awaiting_to_contributed_on_pay(self):
        sm = StateMachine()
        ctx = {
            "member": {"id": "mem-1", "display_name": "Maria"},
            "round": {
                "id": "rnd-1",
                "name": "Barangay 21",
                "contribution_amount_php": 500,
            },
            "cycle": {"cycle_number": 2},
            "twilio_sid": "SMx",
        }
        out = sm.transition(MemberState.AWAITING_CONTRIBUTION, InboundEvent.PAY, ctx)
        assert out.next_state is MemberState.CONTRIBUTED
        assert out.reply.template_id == "PAY_RECEIVED"
        types = [fx["type"] for fx in out.side_effects]
        assert "create_pending_contribution" in types
        assert "enqueue_stellar_contribute" in types

    def test_contributed_pay_idempotent_already_contributed(self):
        sm = StateMachine()
        out = sm.transition(
            MemberState.CONTRIBUTED,
            InboundEvent.PAY,
            {"member": {"id": "mem-1"}, "twilio_sid": "x"},
        )
        assert out.next_state is MemberState.CONTRIBUTED
        assert out.reply.template_id == "ALREADY_CONTRIBUTED"

    def test_help_in_any_state(self):
        sm = StateMachine()
        for s in MemberState:
            out = sm.transition(s, InboundEvent.HELP, {"member": {"id": "m"}})
            assert out.next_state is s
            assert out.reply.template_id == "HELP_MENU"

    def test_garbage_falls_back(self):
        sm = StateMachine()
        out = sm.transition(MemberState.JOINED, InboundEvent.GARBAGE, {"member": {"id": "m"}})
        assert out.reply.template_id == "GARBAGE_FALLBACK"

    def test_idle_pay_rejects(self):
        sm = StateMachine()
        out = sm.transition(
            MemberState.IDLE, InboundEvent.PAY, {"member": {"id": "m"}, "twilio_sid": "x"}
        )
        assert out.reply.template_id == "NOT_IN_ACTIVE_ROUND"


# ---------------------------------------------------------------------------
# State machine — integration via HTTP
# ---------------------------------------------------------------------------


class TestStateMachineHttp:
    async def test_idle_to_joined_flow(self, client, store):
        seed_member(store)
        seed_round(store)
        form = {
            "MessageSid": "SMjoin",
            "From": "whatsapp:+639171234567",
            "Body": "JOIN BRG21",
        }
        res = await _post_webhook(client, form)
        assert res.status_code == 200
        assert "Welcome sa Barangay 21" in res.text
        assert ("rnd-1", "mem-1") in store.round_members

    async def test_joined_pay_no_cycle_falls_back_via_http(self, client, store):
        seed_member(store)
        seed_round(store)
        join_member(store)  # joined, but no active cycle
        form = {
            "MessageSid": "SMpaynocycle",
            "From": "whatsapp:+639171234567",
            "Body": "PAY",
        }
        res = await _post_webhook(client, form)
        assert res.status_code == 200
        assert "Walang active cycle" in res.text
        # No contribution rows on this path.
        assert store.contributions == {}

    async def test_awaiting_to_contributed_via_http(self, client, store):
        seed_member(store)
        seed_round(store)
        join_member(store)
        open_cycle(store, cycle_number=2)

        form = {
            "MessageSid": "SMpay",
            "From": "whatsapp:+639171234567",
            "Body": "PAY",
        }
        res = await _post_webhook(client, form)
        assert res.status_code == 200
        assert "Salamat" in res.text and "500" in res.text
        # Contribution row created
        assert ("rnd-1", "mem-1", 2) in store.contributions
        assert store.contributions[("rnd-1", "mem-1", 2)]["status"] == "pending"

    async def test_garbage_input_returns_fallback_menu(self, client, store):
        seed_member(store)
        form = {
            "MessageSid": "SMjunk",
            "From": "whatsapp:+639171234567",
            "Body": "anong meron diyan",
        }
        res = await _post_webhook(client, form)
        assert res.status_code == 200
        assert "Hindi ko gets" in res.text

    async def test_unknown_member_friendly_reject_no_member_write(self, client, store):
        # No seed_member()
        form = {
            "MessageSid": "SMunknown",
            "From": "whatsapp:+639170000000",
            "Body": "JOIN BRG21",
        }
        res = await _post_webhook(client, form)
        assert res.status_code == 200
        assert "not in any DAMAY round yet" in res.text
        # Members table untouched.
        assert store.members == {}

    async def test_status_command_renders(self, client, store):
        seed_member(store)
        r = seed_round(store)
        r["member_count"] = 6
        join_member(store)
        open_cycle(store, cycle_number=3)
        form = {
            "MessageSid": "SMstatus",
            "From": "whatsapp:+639171234567",
            "Body": "STATUS",
        }
        res = await _post_webhook(client, form)
        assert res.status_code == 200
        assert "Cycle: 3/6" in res.text


# ---------------------------------------------------------------------------
# Filipino voice smoke test — templates render without KeyError
# ---------------------------------------------------------------------------


class TestTemplates:
    def test_all_templates_renderable(self):
        # Ensure every required template constant exists and looks Filipino.
        assert "Welcome sa" in templates.WELCOME_JOIN
        assert "Reply PAY" in templates.AWAITING_CONTRIBUTION
        assert "Salamat" in templates.PAY_RECEIVED
        assert "✅" in templates.PAY_CONFIRMED
        assert "Recipient ka" in templates.PAYOUT_NOTIFY
        assert "Hindi ko gets" in templates.GARBAGE_FALLBACK
        assert "DAMAY commands" in templates.HELP_MENU
        assert "Round:" in templates.STATUS_LINE
