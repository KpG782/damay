"""DAMAY member-side WhatsApp state machine.

Per CLAUDE.md §8:

    IDLE
      └─ "JOIN <code>"  → JOINED  (lookup round, add to round_members)
           └─ system "AWAITING_CONTRIBUTION" prompt at cycle start
                └─ "PAY"  → CONTRIBUTED (enqueue Soroban contribute job)
                     └─ when this member is payout recipient → PAYOUT_NOTIFIED → IDLE

Design rules:

* **No implicit state.** The machine is a pure class with an explicit
  `transition(current_state, event, ctx)` method. State is *derived* on
  every inbound message from the most recent `round_members` row and the
  most recent `contributions` row for the active round — never cached.

* **Replay safe.** Dedupe is performed at the router layer via
  `messages.twilio_sid` UNIQUE; this module assumes its handler is only
  invoked once per `MessageSid`.

* **Store abstraction.** All DB access is funnelled through the
  `WhatsAppStore` Protocol so this module is testable without Supabase and
  swappable for the backend-engineer's eventual Supabase client.

* **Templates only here-by-reference.** All outbound copy lives in
  `templates.py` and is rendered by the router; this module returns
  template ids + format kwargs, not pre-rendered strings, so the router
  can decide TwiML vs. queued-outbound.
"""

from __future__ import annotations

import enum
import logging
import re
from dataclasses import dataclass, field
from typing import Any, Protocol

from damay_api.services import templates

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------


class MemberState(str, enum.Enum):
    """Member's position in the per-round lifecycle."""

    IDLE = "IDLE"
    JOINED = "JOINED"
    AWAITING_CONTRIBUTION = "AWAITING_CONTRIBUTION"
    CONTRIBUTED = "CONTRIBUTED"
    PAYOUT_NOTIFIED = "PAYOUT_NOTIFIED"


class InboundEvent(str, enum.Enum):
    """Parsed inbound message types."""

    JOIN = "JOIN"
    PAY = "PAY"
    STATUS = "STATUS"
    HELP = "HELP"
    GARBAGE = "GARBAGE"


# Strict command regex — matches CLAUDE.md §8 contract.
# Case-insensitive; must be a full match (no trailing junk).
_COMMAND_RE = re.compile(r"^(?:JOIN\s+(\S+)|PAY|HELP|STATUS)\s*$", re.IGNORECASE)


# Sentinel: position is unknown until the round_members row is inserted.
# The router patches the rendered reply after applying the side effect.
PENDING_POSITION = "—"


# ---------------------------------------------------------------------------
# Value objects
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class ParsedCommand:
    event: InboundEvent
    payload: str | None = None  # e.g. join code for JOIN

    @classmethod
    def parse(cls, raw: str) -> "ParsedCommand":
        if not raw:
            return cls(InboundEvent.GARBAGE)
        text = raw.strip()
        m = _COMMAND_RE.match(text)
        if not m:
            return cls(InboundEvent.GARBAGE)
        head = text.split(None, 1)[0].upper()
        if head == "JOIN":
            return cls(InboundEvent.JOIN, payload=m.group(1))
        if head == "PAY":
            return cls(InboundEvent.PAY)
        if head == "STATUS":
            return cls(InboundEvent.STATUS)
        if head == "HELP":
            return cls(InboundEvent.HELP)
        return cls(InboundEvent.GARBAGE)


@dataclass
class Reply:
    """Outbound reply intent. Router decides TwiML vs. queued send."""

    template_id: str
    kwargs: dict[str, Any] = field(default_factory=dict)

    def render(self) -> str:
        body = getattr(templates, self.template_id)
        if self.kwargs:
            return body.format(**self.kwargs)
        return body


@dataclass
class TransitionResult:
    """Pure output of `StateMachine.transition`. No I/O performed yet."""

    next_state: MemberState
    reply: Reply
    # Side-effects the router/handler must perform after a successful
    # transition. Kept as primitive dicts so this module stays I/O-free.
    side_effects: list[dict[str, Any]] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Store protocol (implemented by backend-engineer's supabase client OR by the
# in-memory fake used in tests + /dev/simulate-message demo flows)
# ---------------------------------------------------------------------------


class WhatsAppStore(Protocol):
    """Minimal data access surface required by the state machine + handler."""

    async def get_member_by_whatsapp(self, whatsapp_e164: str) -> dict[str, Any] | None: ...

    async def get_round_by_code(self, code: str) -> dict[str, Any] | None: ...

    async def get_active_round_for_member(self, member_id: str) -> dict[str, Any] | None: ...

    async def get_round_member(
        self, round_id: str, member_id: str
    ) -> dict[str, Any] | None: ...

    async def add_round_member(
        self, round_id: str, member_id: str
    ) -> dict[str, Any]: ...

    async def get_active_cycle(self, round_id: str) -> dict[str, Any] | None:
        """Return the open cycle for the round, or None if no active cycle."""

    async def get_contribution(
        self, round_id: str, member_id: str, cycle_number: int
    ) -> dict[str, Any] | None: ...

    async def create_pending_contribution(
        self,
        round_id: str,
        member_id: str,
        cycle_number: int,
        amount_php: int,
        source_message_sid: str,
    ) -> dict[str, Any]: ...

    async def record_message(
        self,
        twilio_sid: str,
        direction: str,
        body: str,
        member_id: str | None,
    ) -> bool:
        """Insert a `messages` row. Returns True on insert, False on dedupe hit."""

    async def get_latest_contribution_for_member(
        self, round_id: str, member_id: str
    ) -> dict[str, Any] | None: ...


# ---------------------------------------------------------------------------
# State derivation
# ---------------------------------------------------------------------------


async def derive_state(store: WhatsAppStore, member_id: str) -> tuple[MemberState, dict[str, Any] | None]:
    """Derive member state on-demand from latest round_members + contributions.

    Returns (state, active_round_context). `active_round_context` is None
    when the member has no active round.

    State derivation rules (in priority order):
        1. No active round membership  → IDLE
        2. Active round, no active cycle, no latest contribution → JOINED
        3. Active cycle open AND no contribution row for it → AWAITING_CONTRIBUTION
        4. Contribution row exists for current cycle and confirmed payout
           recipient == this member → PAYOUT_NOTIFIED
        5. Contribution row exists for current cycle → CONTRIBUTED
    """
    active = await store.get_active_round_for_member(member_id)
    if active is None:
        return MemberState.IDLE, None

    round_id: str = active["round_id"]
    cycle = await store.get_active_cycle(round_id)
    if cycle is None:
        return MemberState.JOINED, active

    cycle_number: int = cycle["cycle_number"]
    contribution = await store.get_contribution(round_id, member_id, cycle_number)
    if contribution is None:
        return MemberState.AWAITING_CONTRIBUTION, {**active, "cycle": cycle}

    # If this member is the cycle's payout recipient and payout went out,
    # they sit at PAYOUT_NOTIFIED briefly; the cycle-rollover compactor flips
    # them back to IDLE for the next cycle. For demo purposes we treat the
    # transient state as CONTRIBUTED unless explicitly flagged.
    if cycle.get("payout_recipient_id") == member_id and cycle.get("payout_sent"):
        return MemberState.PAYOUT_NOTIFIED, {**active, "cycle": cycle, "contribution": contribution}

    return MemberState.CONTRIBUTED, {**active, "cycle": cycle, "contribution": contribution}


# ---------------------------------------------------------------------------
# State machine
# ---------------------------------------------------------------------------


class StateMachine:
    """Explicit transition table — no implicit state, no fallthroughs."""

    def transition(
        self,
        current: MemberState,
        event: InboundEvent,
        ctx: dict[str, Any],
    ) -> TransitionResult:
        """Compute next state + reply for a (state, event) pair.

        `ctx` is the derivation context (round, cycle, contribution, member,
        join_lookup_result, etc). The router populates it before calling.

        This is a *pure* function: no DB, no Twilio, no logging beyond debug.
        Side effects are returned as a list of dicts for the caller.
        """
        # --- universal commands first --------------------------------------
        if event is InboundEvent.HELP:
            return TransitionResult(current, Reply("HELP_MENU"))

        if event is InboundEvent.STATUS:
            return self._status(current, ctx)

        if event is InboundEvent.GARBAGE:
            return TransitionResult(current, Reply("GARBAGE_FALLBACK"))

        # --- state-aware commands ------------------------------------------
        if event is InboundEvent.JOIN:
            return self._on_join(current, ctx)

        if event is InboundEvent.PAY:
            return self._on_pay(current, ctx)

        # Defensive: should be unreachable because InboundEvent is closed.
        return TransitionResult(current, Reply("GARBAGE_FALLBACK"))

    # ------------------------------------------------------------------
    # Per-event helpers
    # ------------------------------------------------------------------

    def _on_join(self, current: MemberState, ctx: dict[str, Any]) -> TransitionResult:
        target_round = ctx.get("join_round")
        if target_round is None:
            # Round lookup failed in the router. Reply with friendly error;
            # state does not change.
            return TransitionResult(current, Reply("INVALID_JOIN_CODE"))

        # Re-join is a no-op acknowledgement — never duplicate round_members.
        if ctx.get("already_in_round"):
            return TransitionResult(
                MemberState.JOINED,
                Reply(
                    "WELCOME_JOIN",
                    {
                        "round_name": target_round["name"],
                        "position": ctx.get("payout_position", PENDING_POSITION),
                    },
                ),
            )

        side_effects: list[dict[str, Any]] = [
            {
                "type": "add_round_member",
                "round_id": target_round["id"],
                "member_id": ctx["member"]["id"],
            }
        ]
        # Position is unknown until the router applies the add_round_member
        # side effect. We seed with a sentinel; the router overwrites
        # `reply.kwargs["position"]` post-insert.
        return TransitionResult(
            MemberState.JOINED,
            Reply(
                "WELCOME_JOIN",
                {
                    "round_name": target_round["name"],
                    "position": ctx.get("payout_position", PENDING_POSITION),
                },
            ),
            side_effects=side_effects,
        )

    def _on_pay(self, current: MemberState, ctx: dict[str, Any]) -> TransitionResult:
        if current is MemberState.IDLE:
            return TransitionResult(current, Reply("NOT_IN_ACTIVE_ROUND"))

        if current is MemberState.JOINED:
            # Round joined but no cycle yet open.
            return TransitionResult(current, Reply("NO_ACTIVE_CYCLE"))

        if current is MemberState.CONTRIBUTED or current is MemberState.PAYOUT_NOTIFIED:
            return TransitionResult(current, Reply("ALREADY_CONTRIBUTED"))

        # AWAITING_CONTRIBUTION → CONTRIBUTED (the interesting path)
        round_ = ctx["round"]
        cycle = ctx["cycle"]
        member = ctx["member"]
        side_effects = [
            {
                "type": "create_pending_contribution",
                "round_id": round_["id"],
                "member_id": member["id"],
                "cycle_number": cycle["cycle_number"],
                "amount_php": round_["contribution_amount_php"],
                "source_message_sid": ctx["twilio_sid"],
            },
            {
                "type": "enqueue_stellar_contribute",
                "round_id": round_["id"],
                "member_id": member["id"],
                "cycle_number": cycle["cycle_number"],
            },
        ]
        return TransitionResult(
            MemberState.CONTRIBUTED,
            Reply(
                "PAY_RECEIVED",
                {
                    "name": member.get("display_name") or "ka",
                    "amount": round_["contribution_amount_php"],
                },
            ),
            side_effects=side_effects,
        )

    def _status(self, current: MemberState, ctx: dict[str, Any]) -> TransitionResult:
        round_ = ctx.get("round")
        if round_ is None:
            return TransitionResult(current, Reply("NOT_IN_ACTIVE_ROUND"))

        cycle = ctx.get("cycle") or {}
        next_recipient = (cycle.get("next_recipient_name")
                          or ctx.get("next_recipient_name")
                          or "TBD")
        return TransitionResult(
            current,
            Reply(
                "STATUS_LINE",
                {
                    "round_name": round_["name"],
                    "cycle": cycle.get("cycle_number", 0),
                    "total": round_.get("member_count", 0),
                    "member_status": current.value,
                    "next_recipient": next_recipient,
                },
            ),
        )


# ---------------------------------------------------------------------------
# In-memory store (used by tests + the /dev/simulate-message demo path)
# ---------------------------------------------------------------------------


class InMemoryStore:
    """Tiny in-memory implementation of `WhatsAppStore`.

    NOT suitable for production. Backend-engineer's Supabase client replaces
    this in the live app via FastAPI dependency-injection.
    """

    def __init__(self) -> None:
        self.members: dict[str, dict[str, Any]] = {}  # whatsapp_e164 → member
        self.rounds_by_code: dict[str, dict[str, Any]] = {}
        self.rounds_by_id: dict[str, dict[str, Any]] = {}
        self.round_members: dict[tuple[str, str], dict[str, Any]] = {}
        self.cycles: dict[str, dict[str, Any]] = {}  # round_id → active cycle
        self.contributions: dict[tuple[str, str, int], dict[str, Any]] = {}
        self.messages: dict[str, dict[str, Any]] = {}  # twilio_sid → row
        self.stellar_jobs: list[dict[str, Any]] = []
        self.dead_letter: list[dict[str, Any]] = []

    # ----- WhatsAppStore -------------------------------------------------

    async def get_member_by_whatsapp(self, whatsapp_e164: str) -> dict[str, Any] | None:
        return self.members.get(whatsapp_e164)

    async def get_round_by_code(self, code: str) -> dict[str, Any] | None:
        return self.rounds_by_code.get(code.upper())

    async def get_active_round_for_member(self, member_id: str) -> dict[str, Any] | None:
        for (rid, mid), rm in self.round_members.items():
            if mid != member_id:
                continue
            r = self.rounds_by_id[rid]
            if r["status"] == "active":
                return {"round_id": rid, "round": r, **rm}
        # Fall back to any round_membership at all so JOINED makes sense.
        for (rid, mid), rm in self.round_members.items():
            if mid == member_id:
                return {"round_id": rid, "round": self.rounds_by_id[rid], **rm}
        return None

    async def get_round_member(self, round_id: str, member_id: str) -> dict[str, Any] | None:
        return self.round_members.get((round_id, member_id))

    async def add_round_member(self, round_id: str, member_id: str) -> dict[str, Any]:
        position = sum(1 for (rid, _mid) in self.round_members if rid == round_id) + 1
        row = {
            "round_id": round_id,
            "member_id": member_id,
            "payout_position": position,
        }
        self.round_members[(round_id, member_id)] = row
        return row

    async def get_active_cycle(self, round_id: str) -> dict[str, Any] | None:
        return self.cycles.get(round_id)

    async def get_contribution(
        self, round_id: str, member_id: str, cycle_number: int
    ) -> dict[str, Any] | None:
        return self.contributions.get((round_id, member_id, cycle_number))

    async def create_pending_contribution(
        self,
        round_id: str,
        member_id: str,
        cycle_number: int,
        amount_php: int,
        source_message_sid: str,
    ) -> dict[str, Any]:
        key = (round_id, member_id, cycle_number)
        row = {
            "id": f"con-{len(self.contributions) + 1}",
            "round_id": round_id,
            "member_id": member_id,
            "cycle_number": cycle_number,
            "amount_php": amount_php,
            "status": "pending",
            "source_message_sid": source_message_sid,
        }
        # idempotent insert
        self.contributions.setdefault(key, row)
        return self.contributions[key]

    async def record_message(
        self,
        twilio_sid: str,
        direction: str,
        body: str,
        member_id: str | None,
    ) -> bool:
        if twilio_sid in self.messages:
            return False
        self.messages[twilio_sid] = {
            "twilio_sid": twilio_sid,
            "direction": direction,
            "body": body,
            "member_id": member_id,
        }
        return True

    async def get_latest_contribution_for_member(
        self, round_id: str, member_id: str
    ) -> dict[str, Any] | None:
        rows = [
            v for (rid, mid, _c), v in self.contributions.items()
            if rid == round_id and mid == member_id
        ]
        if not rows:
            return None
        return max(rows, key=lambda r: r["cycle_number"])


# ---------------------------------------------------------------------------
# Outbound retry helper (used by worker code for async payout notifications)
# ---------------------------------------------------------------------------


async def send_with_retry(
    send_fn,
    *,
    to: str,
    body: str,
    max_attempts: int = 3,
    base_delay: float = 0.5,
    dead_letter_sink: list[dict[str, Any]] | None = None,
) -> bool:
    """Send an outbound WhatsApp message with bounded exponential-backoff retry.

    `send_fn` is an awaitable callable matching the backend's
    `clients.twilio.send_whatsapp(to, body)` shape. On exhaustion we write to
    `dead_letter_sink` so the organizer dashboard can surface the failure;
    the persistent dead-letter table (if added) is managed by the worker layer.
    """
    import asyncio

    last_error: Exception | None = None
    for attempt in range(1, max_attempts + 1):
        try:
            await send_fn(to=to, body=body)
            return True
        except Exception as exc:  # noqa: BLE001 — Twilio SDK raises many types
            last_error = exc
            logger.warning(
                "twilio_outbound_failed",
                extra={"attempt": attempt, "error": repr(exc)},
            )
            if attempt < max_attempts:
                await asyncio.sleep(base_delay * (2 ** (attempt - 1)))

    if dead_letter_sink is not None:
        dead_letter_sink.append(
            {"to": to, "body": body, "error": repr(last_error)}
        )
    logger.error(
        "twilio_outbound_dead_letter",
        extra={"to_suffix": to[-4:] if to else "", "error": repr(last_error)},
    )
    return False
