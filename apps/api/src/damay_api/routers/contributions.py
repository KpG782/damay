"""/v1/contributions — record-intent + organizer listing.

POST is intended for SERVICE auth (the WhatsApp state machine). For the
hackathon we accept either a valid organizer JWT or the dev service token —
the surface is the same.
"""

from __future__ import annotations

from fastapi import APIRouter, Request, status

from damay_api.deps import OrganizerDep, SupabaseDep
from damay_api.middleware.rate_limit import AUTH_LIMIT, limiter
from damay_api.models.requests import GetContributionsQuery, PostContributionsRequest
from damay_api.models.responses import (
    Contribution,
    GetContributionsResponse,
    PostContributionsResponse,
    PostPayoutsDistributeResponse,
)
from damay_api.models.requests import PostPayoutsDistributeRequest
from damay_api.services import contributions as contrib_svc

router = APIRouter(prefix="/v1", tags=["contributions"])


@router.post(
    "/contributions",
    response_model=PostContributionsResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
@limiter.limit(AUTH_LIMIT)
async def post_contribution(
    request: Request,
    body: PostContributionsRequest,
    organizer: OrganizerDep,
    supabase: SupabaseDep,
) -> PostContributionsResponse:
    result = await contrib_svc.record_contribution(
        supabase,
        round_id=body.round_id,
        member_id=body.member_id,
        cycle_number=body.cycle_number,
        amount_php=body.amount_php,
        source_message_sid=body.source_message_sid,
    )
    return PostContributionsResponse(
        contribution_id=result["contribution"]["id"],
        job_id=result["job_id"],
    )


@router.get("/contributions", response_model=GetContributionsResponse)
@limiter.limit(AUTH_LIMIT)
async def list_contributions(
    request: Request,
    organizer: OrganizerDep,
    supabase: SupabaseDep,
    round_id: str,
    cycle: int | None = None,
) -> GetContributionsResponse:
    rows = await contrib_svc.list_contributions(supabase, organizer.id, round_id, cycle)
    return GetContributionsResponse(data=[Contribution.model_validate(r) for r in rows])


@router.post(
    "/payouts/{round_id}/distribute",
    response_model=PostPayoutsDistributeResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
@limiter.limit(AUTH_LIMIT)
async def distribute_payout(
    request: Request,
    round_id: str,
    body: PostPayoutsDistributeRequest,
    organizer: OrganizerDep,
    supabase: SupabaseDep,
) -> PostPayoutsDistributeResponse:
    out = await contrib_svc.distribute_payout(supabase, organizer.id, round_id, body.cycle_number)
    return PostPayoutsDistributeResponse(job_id=out["job_id"])
