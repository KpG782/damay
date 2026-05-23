"""DB row dataclasses — thin shims used internally by services/clients."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any


@dataclass(slots=True)
class StellarJobRow:
    id: str
    job_type: str
    payload: dict[str, Any]
    target_table: str | None
    target_id: str | None
    idempotency_key: str | None
    status: str
    attempts: int
    last_error: str | None
    stellar_tx_hash: str | None
    scheduled_for: datetime
    locked_until: datetime | None
    created_at: datetime
    updated_at: datetime
