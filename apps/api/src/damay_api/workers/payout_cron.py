"""Cycle-deadline payout cron.

For each active round, check whether the current cycle has all contributions
confirmed AND the cycle deadline has passed; if so, enqueue
``distribute_payout``. Idempotent via the stellar_jobs unique key.
"""

from __future__ import annotations

import structlog

from damay_api.clients.supabase import SupabaseClient
from damay_api.services.stellar_jobs import enqueue

logger = structlog.get_logger("damay.worker.payout_cron")


async def tick(supabase: SupabaseClient) -> int:
    """Run one pass. Returns count of enqueued payouts."""
    active = await supabase.select("rounds", filters={"status": "active"})
    enqueued = 0
    for rnd in active:
        round_id = rnd["id"]
        for cycle in range(1, rnd["member_count"] + 1):
            existing = await supabase.select_one(
                "payouts", {"round_id": round_id, "cycle_number": cycle}
            )
            if existing and existing.get("status") in ("pending", "confirmed"):
                continue
            contribs = await supabase.select(
                "contributions",
                filters={"round_id": round_id, "cycle_number": cycle},
            )
            confirmed = [c for c in contribs if c.get("status") == "confirmed"]
            if len(confirmed) < rnd["member_count"]:
                continue
            await enqueue(
                supabase,
                job_type="distribute_payout",
                payload={
                    "round_id": round_id,
                    "cycle_number": cycle,
                    "paluwagan_contract_id": rnd.get("paluwagan_contract_id"),
                },
                target_table="rounds",
                target_id=round_id,
            )
            enqueued += 1
    if enqueued:
        logger.info("payout_cron_enqueued", count=enqueued)
    return enqueued
