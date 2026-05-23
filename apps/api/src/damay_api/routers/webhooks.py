"""Twilio WhatsApp webhook + dev simulator.

This router exposes two endpoints. The backend-engineer wires it into the
FastAPI app via:

    from damay_api.routers import webhooks
    app.include_router(webhooks.router)

The router itself declares its own prefixes:
    - inbound webhook: POST /webhooks/twilio
    - dev simulator:   POST /dev/simulate-message  (mounted conditionally)

The simulator is added at import time only when `NODE_ENV != "production"`
OR `FEATURE_DEMO_MODE=true`, so production builds physically cannot route
to it (return 404 from FastAPI).

All DB access is funnelled through the `WhatsAppStore` Protocol from
`services/whatsapp.py`. Tests override `get_store` and `get_settings` via
`app.dependency_overrides` — no monkey-patching required.
"""

from __future__ import annotations

import logging
import os
import uuid
from dataclasses import dataclass
from typing import Any, Awaitable, Callable

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from fastapi.responses import PlainTextResponse

from damay_api.services import templates
from damay_api.services.twilio_signature import verify_twilio_signature
from damay_api.services.whatsapp import (
    InMemoryStore,
    MemberState,
    ParsedCommand,
    Reply,
    StateMachine,
    TransitionResult,
    WhatsAppStore,
    derive_state,
)

logger = logging.getLogger(__name__)

# Router prefix is `/webhooks`; the dev endpoint sits under `/dev`.
# (Confirmation comment for the backend-engineer who wires include_router.)
router = APIRouter()


# ---------------------------------------------------------------------------
# Settings
# ---------------------------------------------------------------------------


@dataclass
class WebhookSettings:
    """Minimal settings surface this router needs.

    Backend-engineer's larger `Settings` object will subclass or compose this;
    tests construct it directly.
    """

    twilio_auth_token: str = ""
    twilio_webhook_validation: bool = True
    node_env: str = "development"
    feature_demo_mode: bool = True
    stellar_expert_url_template: str = (
        "https://stellar.expert/explorer/testnet/tx/{tx_hash}"
    )

    @classmethod
    def from_env(cls) -> "WebhookSettings":
        return cls(
            twilio_auth_token=os.environ.get("TWILIO_AUTH_TOKEN", ""),
            twilio_webhook_validation=(
                os.environ.get("TWILIO_WEBHOOK_VALIDATION", "true").lower() != "false"
            ),
            node_env=os.environ.get("NODE_ENV", "development"),
            feature_demo_mode=(
                os.environ.get("FEATURE_DEMO_MODE", "true").lower() == "true"
            ),
        )

    @property
    def dev_endpoints_enabled(self) -> bool:
        return self.node_env != "production" or self.feature_demo_mode


# ---------------------------------------------------------------------------
# Dependency providers (overridable from tests / main.py)
# ---------------------------------------------------------------------------


_default_store = InMemoryStore()


def get_settings() -> WebhookSettings:
    """Default provider; main.py and tests override via dependency_overrides."""
    return WebhookSettings.from_env()


def get_store() -> WhatsAppStore:
    """Default provider returns a singleton in-memory store.

    The backend-engineer overrides this in `main.py` to return a Supabase-
    backed store; tests override with their own fake fixture.
    """
    return _default_store


# ---------------------------------------------------------------------------
# TwiML helpers
# ---------------------------------------------------------------------------


def _twiml_response(body: str | None) -> Response:
    """Render a Twilio TwiML reply. Empty body → empty <Response/>."""
    if body is None or body == "":
        xml = "<Response/>"
    else:
        # Escape XML special chars to keep TwiML valid.
        safe = (
            body.replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
        )
        xml = f"<Response><Message>{safe}</Message></Response>"
    return Response(content=xml, media_type="application/xml", status_code=200)


# ---------------------------------------------------------------------------
# Inbound webhook
# ---------------------------------------------------------------------------


def _redact_body(body: str | None, n: int = 24) -> str:
    if not body:
        return ""
    return body[:n] + ("…" if len(body) > n else "")


def _abs_url(request: Request) -> str:
    """Reconstruct the URL Twilio used to sign the request.

    Honours `X-Forwarded-Proto` and `X-Forwarded-Host` so signature verify
    still works when the API sits behind a TLS-terminating reverse proxy
    (EasyPanel / Cloudflare).
    """
    proto = request.headers.get("x-forwarded-proto") or request.url.scheme
    host = request.headers.get("x-forwarded-host") or request.url.netloc
    path = request.url.path
    query = ("?" + request.url.query) if request.url.query else ""
    return f"{proto}://{host}{path}{query}"


async def _process_inbound(
    *,
    form: dict[str, str],
    store: WhatsAppStore,
    settings: WebhookSettings,
) -> Response:
    """Shared core for both the live webhook and `/dev/simulate-message`.

    Assumes signature has already been verified (or skipped) by the caller.
    """
    sid = form.get("MessageSid", "").strip()
    body = form.get("Body", "")
    from_e164 = form.get("From", "").replace("whatsapp:", "").strip()

    if not sid:
        # Malformed Twilio payload — log and tell Twilio 200 to avoid retry storm.
        logger.warning("twilio_payload_missing_sid")
        return _twiml_response(None)

    # ---- Resolve member (unknown member → friendly reject, no DB write) ----
    member = await store.get_member_by_whatsapp(from_e164) if from_e164 else None
    if member is None:
        # Still record the inbound message attempt (no member link) so we can
        # see junk traffic and dedupe properly.
        await store.record_message(sid, "in", body, member_id=None)
        return _twiml_response(templates.UNKNOWN_MEMBER)

    # ---- Dedupe via messages.twilio_sid UNIQUE -----------------------------
    inserted = await store.record_message(sid, "in", body, member_id=member["id"])
    if not inserted:
        logger.info("twilio_duplicate_sid", extra={"sid": sid})
        # Idempotent: do not re-process; reply 200 with empty TwiML so Twilio
        # stops retrying. Outbound was already sent on the original delivery.
        return _twiml_response(None)

    # ---- Parse command + derive state --------------------------------------
    cmd = ParsedCommand.parse(body)
    current, derived_ctx = await derive_state(store, member["id"])

    ctx: dict[str, Any] = {
        "member": member,
        "twilio_sid": sid,
    }
    if derived_ctx is not None:
        ctx["round"] = derived_ctx["round"]
        ctx["payout_position"] = derived_ctx.get("payout_position")
        ctx["cycle"] = derived_ctx.get("cycle")

    # ---- JOIN needs special pre-loading ------------------------------------
    if cmd.event.value == "JOIN" and cmd.payload:
        target = await store.get_round_by_code(cmd.payload)
        if target is not None:
            ctx["join_round"] = target
            existing = await store.get_round_member(target["id"], member["id"])
            if existing is not None:
                ctx["already_in_round"] = True
                ctx["payout_position"] = existing["payout_position"]
        # else: invalid code → state machine emits INVALID_JOIN_CODE

    # ---- Drive the state machine -------------------------------------------
    sm = StateMachine()
    result: TransitionResult = sm.transition(current, cmd.event, ctx)

    # ---- Apply side effects sequentially (still inside the same logical txn)
    for fx in result.side_effects:
        await _apply_side_effect(fx, store=store, ctx=ctx)
        # Re-resolve payout_position for the WELCOME_JOIN reply if we just
        # inserted a round_members row.
        if fx["type"] == "add_round_member":
            rm = await store.get_round_member(fx["round_id"], fx["member_id"])
            if rm is not None:
                result.reply.kwargs["position"] = rm["payout_position"]

    # ---- Render + log outbound + reply -------------------------------------
    out_body = result.reply.render()
    # Log outbound; out-messages use a synthesized sid so they survive uniqueness.
    out_sid = f"out-{uuid.uuid4().hex[:12]}"
    await store.record_message(out_sid, "out", out_body, member_id=member["id"])
    logger.info(
        "twilio_inbound_handled",
        extra={
            "sid": sid,
            "event": cmd.event.value,
            "state": current.value,
            "next_state": result.next_state.value,
        },
    )
    return _twiml_response(out_body)


async def _apply_side_effect(
    fx: dict[str, Any],
    *,
    store: WhatsAppStore,
    ctx: dict[str, Any],
) -> None:
    """Carry out the side effects requested by `StateMachine.transition`.

    Kept here (router layer) so the state machine remains pure / testable.
    Stellar-write enqueues call into the backend-engineer's `stellar_jobs`
    helper; we lazy-import to avoid a hard dependency at import time.
    """
    t = fx["type"]
    if t == "add_round_member":
        await store.add_round_member(fx["round_id"], fx["member_id"])
        # Best-effort enqueue of `add_member` Soroban job. The helper may not
        # exist yet during early Phase 2; swallow the import error so the
        # webhook still reads as 200 OK.
        try:
            from damay_api.services import stellar_jobs  # type: ignore[import-not-found]
            await stellar_jobs.enqueue(  # type: ignore[attr-defined]
                job_type="add_member",
                payload={
                    "round_id": fx["round_id"],
                    "member_id": fx["member_id"],
                },
            )
        except Exception:  # noqa: BLE001
            logger.debug("stellar_jobs_unavailable", extra={"job": "add_member"})
    elif t == "create_pending_contribution":
        await store.create_pending_contribution(
            round_id=fx["round_id"],
            member_id=fx["member_id"],
            cycle_number=fx["cycle_number"],
            amount_php=fx["amount_php"],
            source_message_sid=fx["source_message_sid"],
        )
    elif t == "enqueue_stellar_contribute":
        try:
            from damay_api.services import stellar_jobs  # type: ignore[import-not-found]
            await stellar_jobs.enqueue(  # type: ignore[attr-defined]
                job_type="contribute",
                payload={
                    "round_id": fx["round_id"],
                    "member_id": fx["member_id"],
                    "cycle_number": fx["cycle_number"],
                },
            )
        except Exception:  # noqa: BLE001
            logger.debug("stellar_jobs_unavailable", extra={"job": "contribute"})
    else:
        logger.warning("unknown_side_effect", extra={"type": t})


@router.post("/webhooks/twilio")
async def twilio_webhook(
    request: Request,
    store: WhatsAppStore = Depends(get_store),
    settings: WebhookSettings = Depends(get_settings),
) -> Response:
    """Inbound WhatsApp message from Twilio.

    Always returns 200 to Twilio on success (TwiML or empty), 403 only when
    the signature verify fails. Internal exceptions are caught and turned
    into empty 200s so Twilio stops retrying; replay-safety is the dedupe.
    """
    # Twilio sends `application/x-www-form-urlencoded`. Parse into a plain
    # dict[str, str] (last-value-wins for repeats, which Twilio doesn't use).
    raw_form = await request.form()
    form: dict[str, str] = {k: str(v) for k, v in raw_form.items()}

    # ---- Signature verify --------------------------------------------------
    if settings.twilio_webhook_validation:
        signature = request.headers.get("x-twilio-signature")
        url = _abs_url(request)
        if not verify_twilio_signature(
            settings.twilio_auth_token,
            url,
            form,
            signature,
        ):
            logger.warning(
                "twilio_signature_rejected",
                extra={
                    "sid": form.get("MessageSid", ""),
                    "from_suffix": (form.get("From") or "")[-4:],
                    "body_preview": _redact_body(form.get("Body")),
                },
            )
            raise HTTPException(status_code=403, detail="invalid signature")
    else:
        logger.warning(
            "twilio_signature_validation_disabled "
            "TWILIO_WEBHOOK_VALIDATION=false — DO NOT USE IN PROD"
        )

    try:
        return await _process_inbound(form=form, store=store, settings=settings)
    except HTTPException:
        raise
    except Exception:  # noqa: BLE001
        logger.exception("twilio_webhook_unhandled_error")
        # Tell Twilio 200 so it doesn't retry-storm us; the dedupe will keep
        # state sane when the operator resubmits manually.
        return _twiml_response(None)


# ---------------------------------------------------------------------------
# Dev simulator — only mounted in non-prod / demo mode
# ---------------------------------------------------------------------------


def _dev_enabled() -> bool:
    """Evaluated at *import* time AND per-request to honour test overrides."""
    return WebhookSettings.from_env().dev_endpoints_enabled


@router.post("/dev/simulate-message")
async def simulate_message(
    payload: dict[str, str],
    store: WhatsAppStore = Depends(get_store),
    settings: WebhookSettings = Depends(get_settings),
) -> Response:
    """Synthesize an inbound Twilio message — demo backdoor for the organizer.

    Body: `{"whatsapp_e164": "+639...", "body": "JOIN BRG21"}`.

    Returns the TwiML response inline so the dashboard can show the reply.
    Returns 404 when dev endpoints are disabled (prod build w/o demo mode).
    """
    if not settings.dev_endpoints_enabled:
        # Mirror FastAPI's standard 404 shape so it's indistinguishable from
        # the route literally not being mounted.
        raise HTTPException(status_code=404, detail="Not Found")

    whatsapp_e164 = (payload.get("whatsapp_e164") or "").strip()
    body = payload.get("body") or ""
    if not whatsapp_e164:
        raise HTTPException(status_code=400, detail="whatsapp_e164 required")

    synthetic_form = {
        "MessageSid": f"sim-{uuid.uuid4().hex[:24]}",
        "From": f"whatsapp:{whatsapp_e164}",
        "To": "whatsapp:+14155238886",  # Twilio sandbox default
        "Body": body,
        "NumMedia": "0",
    }
    return await _process_inbound(form=synthetic_form, store=store, settings=settings)


__all__ = [
    "router",
    "WebhookSettings",
    "get_settings",
    "get_store",
    "MemberState",  # re-export for convenience in tests
]
