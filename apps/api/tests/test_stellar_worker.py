"""Stellar worker: drains a queued job and marks it done."""

import pytest

from damay_api.clients.stellar import get_stellar
from damay_api.clients.supabase import get_supabase
from damay_api.config import get_settings
from damay_api.services.stellar_jobs import enqueue
from damay_api.workers import stellar_worker


@pytest.mark.asyncio
async def test_worker_drains_contribute_job():
    settings = get_settings()
    supabase = await get_supabase(settings)
    stellar = get_stellar(settings)

    # Seed a fake contribution row so the worker can update it on success.
    contribution = await supabase.insert(
        "contributions",
        {
            "round_id": "00000000-0000-0000-0000-000000000010",
            "member_id": "00000000-0000-0000-0000-000000000011",
            "cycle_number": 1,
            "amount_php": 500,
            "status": "pending",
        },
    )
    await enqueue(
        supabase,
        job_type="contribute",
        payload={
            "round_id": contribution["round_id"],
            "member_id": contribution["member_id"],
            "cycle_number": 1,
        },
        target_table="contributions",
        target_id=contribution["id"],
    )

    processed = await stellar_worker.drain_once(supabase, stellar)
    assert processed >= 1

    done = await supabase.select("stellar_jobs", filters={"status": "done"})
    assert len(done) >= 1
    assert done[0]["stellar_tx_hash"]

    refreshed = await supabase.select_one("contributions", {"id": contribution["id"]})
    assert refreshed["status"] == "confirmed"
    assert refreshed["stellar_tx_hash"]
