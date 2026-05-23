"""Round + member services."""

from __future__ import annotations

import secrets
from datetime import date
from typing import Any

from fastapi import HTTPException, status

from damay_api.clients.supabase import SupabaseClient
from damay_api.services.stellar_jobs import enqueue


def _http_409(code: str, message: str) -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_409_CONFLICT,
        detail={"code": code, "message": message},
    )


def _http_404(code: str, message: str) -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail={"code": code, "message": message},
    )


def _gen_code() -> str:
    return secrets.token_hex(3).upper()  # 6 chars, hex


async def create_round(
    supabase: SupabaseClient,
    organizer_id: str,
    *,
    name: str,
    contribution_amount_php: int,
    member_count: int,
    frequency: str,
    start_date: date,
    code: str | None = None,
) -> dict[str, Any]:
    row = {
        "organizer_id": organizer_id,
        "name": name,
        "code": code or _gen_code(),
        "contribution_amount_php": contribution_amount_php,
        "member_count": member_count,
        "frequency": frequency,
        "start_date": start_date.isoformat() if isinstance(start_date, date) else start_date,
        "status": "draft",
        "paluwagan_contract_id": None,
    }
    return await supabase.insert("rounds", row)


async def list_rounds(
    supabase: SupabaseClient, organizer_id: str, status_filter: str | None, limit: int
) -> list[dict[str, Any]]:
    filters: dict[str, Any] = {"organizer_id": organizer_id}
    if status_filter:
        filters["status"] = status_filter
    return await supabase.select("rounds", filters=filters, order="-created_at", limit=limit)


async def get_round(
    supabase: SupabaseClient, organizer_id: str, round_id: str
) -> dict[str, Any]:
    row = await supabase.select_one("rounds", {"id": round_id})
    if not row or row.get("organizer_id") != organizer_id:
        raise _http_404("ROUND_NOT_FOUND", f"Round {round_id} not found.")
    return row


async def get_round_detail(
    supabase: SupabaseClient, organizer_id: str, round_id: str
) -> dict[str, Any]:
    round_row = await get_round(supabase, organizer_id, round_id)
    round_members = await supabase.select(
        "round_members", filters={"round_id": round_id}, order="payout_position"
    )
    member_ids = [rm["member_id"] for rm in round_members]
    members_by_id: dict[str, dict[str, Any]] = {}
    for mid in member_ids:
        m = await supabase.select_one("members", {"id": mid})
        if m:
            members_by_id[mid] = m
    members_payload = [
        {**rm, "member": members_by_id.get(rm["member_id"])} for rm in round_members
    ]
    contributions = await supabase.select(
        "contributions", filters={"round_id": round_id}, order="-created_at"
    )
    payouts = await supabase.select(
        "payouts", filters={"round_id": round_id}, order="cycle_number"
    )
    return {
        **round_row,
        "members": members_payload,
        "contributions": contributions,
        "payouts": payouts,
    }


async def activate_round(
    supabase: SupabaseClient, organizer_id: str, round_id: str
) -> dict[str, Any]:
    rnd = await get_round(supabase, organizer_id, round_id)
    if rnd.get("status") == "active":
        raise _http_409("ALREADY_ACTIVE", "Round already active.")
    if rnd.get("status") not in ("draft",):
        raise _http_409("ROUND_NOT_READY", f"Round in status {rnd.get('status')}.")
    rm = await supabase.select("round_members", filters={"round_id": round_id})
    if len(rm) < rnd["member_count"]:
        raise _http_409(
            "ROUND_NOT_READY", f"Round needs {rnd['member_count']} members, has {len(rm)}."
        )
    job = await enqueue(
        supabase,
        job_type="deploy_paluwagan",
        payload={"round_id": round_id},
        target_table="rounds",
        target_id=round_id,
    )
    return {"round_id": round_id, "job_id": job["id"]}


async def close_round(
    supabase: SupabaseClient, organizer_id: str, round_id: str
) -> dict[str, Any]:
    rnd = await get_round(supabase, organizer_id, round_id)
    if rnd.get("status") != "active":
        raise _http_409("NOT_ACTIVE", "Round is not active.")
    job = await enqueue(
        supabase,
        job_type="close_round",
        payload={"round_id": round_id},
        target_table="rounds",
        target_id=round_id,
    )
    return {"job_id": job["id"]}


# ---------------------------- Members ---------------------------------------


async def create_member(
    supabase: SupabaseClient, *, whatsapp_e164: str, display_name: str
) -> dict[str, Any]:
    existing = await supabase.select_one("members", {"whatsapp_e164": whatsapp_e164})
    if existing:
        raise _http_409("MEMBER_EXISTS", "A member with that phone is already registered.")
    return await supabase.insert(
        "members",
        {
            "whatsapp_e164": whatsapp_e164,
            "display_name": display_name,
            "stellar_account": None,
        },
    )


async def get_member(
    supabase: SupabaseClient, organizer_id: str, member_id: str
) -> dict[str, Any]:
    m = await supabase.select_one("members", {"id": member_id})
    if not m:
        raise _http_404("MEMBER_NOT_FOUND", f"Member {member_id} not found.")
    # Authorization: caller must share a round with this member.
    shared = await supabase.select("round_members", filters={"member_id": member_id})
    if shared:
        for rm in shared:
            rnd = await supabase.select_one("rounds", {"id": rm["round_id"]})
            if rnd and rnd.get("organizer_id") == organizer_id:
                return m
    raise _http_404("MEMBER_NOT_FOUND", f"Member {member_id} not found.")


async def add_member_to_round(
    supabase: SupabaseClient,
    organizer_id: str,
    round_id: str,
    *,
    member_id: str,
    payout_position: int,
) -> dict[str, Any]:
    rnd = await get_round(supabase, organizer_id, round_id)
    existing = await supabase.select("round_members", filters={"round_id": round_id})
    if any(rm["payout_position"] == payout_position for rm in existing):
        raise _http_409("POSITION_TAKEN", f"Position {payout_position} is taken.")
    if len(existing) >= rnd["member_count"]:
        raise _http_409("ROUND_FULL", "Round is full.")
    m = await supabase.select_one("members", {"id": member_id})
    if not m:
        raise _http_404("MEMBER_NOT_FOUND", f"Member {member_id} not found.")
    row = {
        "round_id": round_id,
        "member_id": member_id,
        "payout_position": payout_position,
    }
    return await supabase.insert("round_members", row)
