"""/v1/rounds — organizer round CRUD + lifecycle endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Request, status

from damay_api.deps import OrganizerDep, SupabaseDep
from damay_api.middleware.rate_limit import AUTH_LIMIT, limiter
from damay_api.models.requests import GetRoundsQuery, PostRoundMembersRequest, PostRoundsRequest
from damay_api.models.responses import (
    CursorPage,
    PostRoundActivateResponse,
    PostRoundCloseResponse,
    Round,
    RoundDetail,
    RoundMember,
)
from damay_api.services import rounds as rounds_svc

router = APIRouter(prefix="/v1/rounds", tags=["rounds"])


@router.post(
    "",
    response_model=Round,
    status_code=status.HTTP_201_CREATED,
)
@limiter.limit(AUTH_LIMIT)
async def create_round(
    request: Request,
    body: PostRoundsRequest,
    organizer: OrganizerDep,
    supabase: SupabaseDep,
) -> Round:
    row = await rounds_svc.create_round(
        supabase,
        organizer.id,
        name=body.name,
        contribution_amount_php=body.contribution_amount_php,
        member_count=body.member_count,
        frequency=body.frequency,
        start_date=body.start_date,
        code=body.code,
    )
    return Round.model_validate(row)


@router.get("", response_model=CursorPage[Round])
@limiter.limit(AUTH_LIMIT)
async def list_rounds(
    request: Request,
    organizer: OrganizerDep,
    supabase: SupabaseDep,
    status: str | None = None,
    limit: int = 20,
    cursor: str | None = None,
) -> CursorPage[Round]:
    rows = await rounds_svc.list_rounds(supabase, organizer.id, status, limit)
    return CursorPage[Round](data=[Round.model_validate(r) for r in rows], next_cursor=None)


@router.get("/{round_id}", response_model=RoundDetail)
@limiter.limit(AUTH_LIMIT)
async def get_round(
    request: Request,
    round_id: str,
    organizer: OrganizerDep,
    supabase: SupabaseDep,
) -> RoundDetail:
    row = await rounds_svc.get_round_detail(supabase, organizer.id, round_id)
    return RoundDetail.model_validate(row)


@router.post(
    "/{round_id}/activate",
    response_model=PostRoundActivateResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
@limiter.limit(AUTH_LIMIT)
async def activate_round(
    request: Request,
    round_id: str,
    organizer: OrganizerDep,
    supabase: SupabaseDep,
) -> PostRoundActivateResponse:
    out = await rounds_svc.activate_round(supabase, organizer.id, round_id)
    return PostRoundActivateResponse(round_id=out["round_id"], job_id=out["job_id"])


@router.post(
    "/{round_id}/close",
    response_model=PostRoundCloseResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
@limiter.limit(AUTH_LIMIT)
async def close_round(
    request: Request,
    round_id: str,
    organizer: OrganizerDep,
    supabase: SupabaseDep,
) -> PostRoundCloseResponse:
    out = await rounds_svc.close_round(supabase, organizer.id, round_id)
    return PostRoundCloseResponse(job_id=out["job_id"])


@router.post(
    "/{round_id}/members",
    response_model=RoundMember,
    status_code=status.HTTP_201_CREATED,
)
@limiter.limit(AUTH_LIMIT)
async def add_member_to_round(
    request: Request,
    round_id: str,
    body: PostRoundMembersRequest,
    organizer: OrganizerDep,
    supabase: SupabaseDep,
) -> RoundMember:
    row = await rounds_svc.add_member_to_round(
        supabase,
        organizer.id,
        round_id,
        member_id=body.member_id,
        payout_position=body.payout_position,
    )
    return RoundMember.model_validate(row)
