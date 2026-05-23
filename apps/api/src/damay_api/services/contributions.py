"""Contribution flow."""

from __future__ import annotations

from typing import Any

from fastapi import HTTPException, status

from damay_api.clients.supabase import SupabaseClient
from damay_api.services.stellar_jobs import enqueue


async def record_contribution(
    supabase: SupabaseClient,
    *,
    round_id: str,
    member_id: str,
    cycle_number: int,
    amount_php: int,
    source_message_sid: str | None = None,
) -> dict[str, Any]:
    """Insert a pending contribution + enqueue the chain submission.

    Idempotent on ``(round_id, member_id, cycle_number)`` — if a row already
    exists we return it without re-enqueueing.
    """
    existing = await supabase.select_one(
        "contributions",
        {"round_id": round_id, "member_id": member_id, "cycle_number": cycle_number},
    )
    if existing:
        job = await supabase.select_one(
            "stellar_jobs",
            {"target_table": "contributions", "target_id": existing["id"]},
        )
        return {
            "contribution": existing,
            "job_id": job["id"] if job else "",
        }

    # Validate round exists
    rnd = await supabase.select_one("rounds", {"id": round_id})
    if not rnd:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "ROUND_NOT_FOUND", "message": "Round not found."},
        )

    row = await supabase.insert(
        "contributions",
        {
            "round_id": round_id,
            "member_id": member_id,
            "cycle_number": cycle_number,
            "amount_php": amount_php,
            "status": "pending",
            "stellar_tx_hash": None,
            "source_message_sid": source_message_sid,
        },
    )
    job = await enqueue(
        supabase,
        job_type="contribute",
        payload={
            "round_id": round_id,
            "member_id": member_id,
            "cycle_number": cycle_number,
            "paluwagan_contract_id": rnd.get("paluwagan_contract_id"),
        },
        target_table="contributions",
        target_id=row["id"],
    )
    return {"contribution": row, "job_id": job["id"]}


async def list_contributions(
    supabase: SupabaseClient, organizer_id: str, round_id: str, cycle: int | None
) -> list[dict[str, Any]]:
    rnd = await supabase.select_one("rounds", {"id": round_id})
    if not rnd or rnd.get("organizer_id") != organizer_id:
        # Don't leak existence.
        return []
    filters: dict[str, Any] = {"round_id": round_id}
    if cycle is not None:
        filters["cycle_number"] = cycle
    return await supabase.select(
        "contributions", filters=filters, order="-created_at"
    )


async def distribute_payout(
    supabase: SupabaseClient, organizer_id: str, round_id: str, cycle_number: int
) -> dict[str, Any]:
    rnd = await supabase.select_one("rounds", {"id": round_id})
    if not rnd or rnd.get("organizer_id") != organizer_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "ROUND_NOT_FOUND", "message": "Round not found."},
        )
    contributions = await supabase.select(
        "contributions", filters={"round_id": round_id, "cycle_number": cycle_number}
    )
    confirmed = [c for c in contributions if c.get("status") == "confirmed"]
    if len(confirmed) < rnd["member_count"]:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "code": "CONTRIBUTIONS_INCOMPLETE",
                "message": (
                    f"Cycle {cycle_number}: {len(confirmed)}/{rnd['member_count']} confirmed."
                ),
            },
        )
    existing_payout = await supabase.select_one(
        "payouts", {"round_id": round_id, "cycle_number": cycle_number}
    )
    if existing_payout and existing_payout.get("status") in ("pending", "confirmed"):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"code": "CYCLE_ALREADY_PAID", "message": "Already distributed."},
        )
    job = await enqueue(
        supabase,
        job_type="distribute_payout",
        payload={
            "round_id": round_id,
            "cycle_number": cycle_number,
            "paluwagan_contract_id": rnd.get("paluwagan_contract_id"),
        },
        target_table="rounds",
        target_id=round_id,
    )
    return {"job_id": job["id"]}
