"""/v1/members — organizer-driven member registration."""

from __future__ import annotations

from fastapi import APIRouter, Request, status

from damay_api.deps import OrganizerDep, SupabaseDep
from damay_api.middleware.rate_limit import AUTH_LIMIT, limiter
from damay_api.models.requests import PostMembersRequest
from damay_api.models.responses import Member
from damay_api.services import rounds as rounds_svc

router = APIRouter(prefix="/v1/members", tags=["members"])


@router.post("", response_model=Member, status_code=status.HTTP_201_CREATED)
@limiter.limit(AUTH_LIMIT)
async def create_member(
    request: Request,
    body: PostMembersRequest,
    organizer: OrganizerDep,
    supabase: SupabaseDep,
) -> Member:
    row = await rounds_svc.create_member(
        supabase,
        whatsapp_e164=body.whatsapp_e164,
        display_name=body.display_name,
    )
    return Member.model_validate(row)


@router.get("/{member_id}", response_model=Member)
@limiter.limit(AUTH_LIMIT)
async def get_member(
    request: Request,
    member_id: str,
    organizer: OrganizerDep,
    supabase: SupabaseDep,
) -> Member:
    row = await rounds_svc.get_member(supabase, organizer.id, member_id)
    return Member.model_validate(row)
