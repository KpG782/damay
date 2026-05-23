"""/v1/reputation/{member_id} — score + on-chain history."""

from __future__ import annotations

from fastapi import APIRouter, Request

from damay_api.deps import OrganizerDep, SupabaseDep
from damay_api.middleware.rate_limit import AUTH_LIMIT, limiter
from damay_api.models.responses import GetReputationResponse, ReputationEvent
from damay_api.services import reputation as rep_svc

router = APIRouter(prefix="/v1/reputation", tags=["reputation"])


@router.get("/{member_id}", response_model=GetReputationResponse)
@limiter.limit(AUTH_LIMIT)
async def get_reputation(
    request: Request,
    member_id: str,
    organizer: OrganizerDep,
    supabase: SupabaseDep,
) -> GetReputationResponse:
    payload = await rep_svc.get_reputation(supabase, organizer.id, member_id)
    return GetReputationResponse(
        member_id=payload["member_id"],
        score=payload["score"],
        events=[ReputationEvent.model_validate(e) for e in payload["events"]],
    )
