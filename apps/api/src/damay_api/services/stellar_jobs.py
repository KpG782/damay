"""Stellar write queue — producer side.

All chain writes go through ``stellar_jobs``. Router code calls ``enqueue``;
the worker (``workers/stellar_worker.py``) drains the table and submits.
"""

from __future__ import annotations

import hashlib
from typing import Any

import structlog

from damay_api.clients.supabase import SupabaseClient

logger = structlog.get_logger("damay.stellar_jobs")


def _idempotency_key(job_type: str, target_id: str | None, payload: dict[str, Any]) -> str:
    cycle = payload.get("cycle_number") or payload.get("cycle") or ""
    raw = f"{job_type}:{target_id or ''}:{cycle}".encode()
    return hashlib.sha256(raw).hexdigest()


async def enqueue(
    supabase: SupabaseClient,
    *,
    job_type: str,
    payload: dict[str, Any],
    target_table: str | None = None,
    target_id: str | None = None,
) -> dict[str, Any]:
    """Insert a queued row in ``stellar_jobs``.

    Idempotency: ``(job_type, target_id, cycle)`` is hashed into
    ``idempotency_key`` which is UNIQUE in the table. Duplicate enqueues
    silently return the existing row.
    """
    key = _idempotency_key(job_type, target_id, payload)
    existing = await supabase.select_one("stellar_jobs", {"idempotency_key": key})
    if existing:
        logger.info("stellar_job_duplicate", job_type=job_type, target_id=target_id)
        return existing
    row = {
        "job_type": job_type,
        "payload": payload,
        "target_table": target_table,
        "target_id": target_id,
        "idempotency_key": key,
        "status": "queued",
        "attempts": 0,
    }
    inserted = await supabase.insert("stellar_jobs", row)
    logger.info(
        "stellar_job_enqueued",
        job_id=inserted["id"],
        job_type=job_type,
        target_id=target_id,
    )
    return inserted
