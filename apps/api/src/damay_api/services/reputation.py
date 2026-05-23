"""Reputation read service — mirrors on-chain score from reputation_events."""

from __future__ import annotations

import math
from datetime import datetime, timezone
from typing import Any

from fastapi import HTTPException, status

from damay_api.clients.supabase import SupabaseClient

# Score formula mirrors contracts/reputation/src/lib.rs:
#   +10*weight per contribution, -25*weight per default, +1 per payout received,
#   decayed 1%/30d applied per event age.
DECAY_PCT_PER_30D = 0.01


def _decay_factor(event_at: datetime, now: datetime) -> float:
    age_days = max(0.0, (now - event_at).total_seconds() / 86400.0)
    periods = min(age_days / 30.0, 240.0)
    return (1.0 - DECAY_PCT_PER_30D) ** periods


def _base_weight(event_type: str, weight: int) -> int:
    if event_type == "contribution":
        return 10 * weight
    if event_type == "default":
        return -25 * weight
    if event_type == "payout":
        return 1
    return 0


def compute_score(events: list[dict[str, Any]], now: datetime | None = None) -> int:
    now = now or datetime.now(timezone.utc)
    total = 0.0
    for e in events:
        created = e.get("created_at")
        if isinstance(created, str):
            try:
                created_dt = datetime.fromisoformat(created.replace("Z", "+00:00"))
            except ValueError:
                continue
        elif isinstance(created, datetime):
            created_dt = created
        else:
            continue
        if created_dt.tzinfo is None:
            created_dt = created_dt.replace(tzinfo=timezone.utc)
        base = _base_weight(e.get("event_type", ""), int(e.get("weight", 1)))
        total += base * _decay_factor(created_dt, now)
    return int(math.floor(total))


async def get_reputation(
    supabase: SupabaseClient, organizer_id: str, member_id: str
) -> dict[str, Any]:
    member = await supabase.select_one("members", {"id": member_id})
    if not member:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "MEMBER_NOT_FOUND", "message": "Member not found."},
        )
    shared = await supabase.select("round_members", filters={"member_id": member_id})
    authorized = False
    for rm in shared:
        rnd = await supabase.select_one("rounds", {"id": rm["round_id"]})
        if rnd and rnd.get("organizer_id") == organizer_id:
            authorized = True
            break
    if not authorized:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "code": "FORBIDDEN",
                "message": "Not authorized to view this reputation.",
            },
        )
    events = await supabase.select(
        "reputation_events", filters={"member_id": member_id}, order="-created_at"
    )
    score = compute_score(events)
    return {"member_id": member_id, "score": score, "events": events}
