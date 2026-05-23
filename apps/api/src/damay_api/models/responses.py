"""Response models. camelCase on the wire to match packages/types."""

from __future__ import annotations

from datetime import date, datetime
from typing import Any, Generic, Literal, TypeVar

from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel


class CamelModel(BaseModel):
    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        from_attributes=True,
    )


T = TypeVar("T")


class CursorPage(CamelModel, Generic[T]):
    data: list[T]
    next_cursor: str | None = None


# ---------------------------- Health ----------------------------------------


HealthCheckStatus = Literal["ok", "fail", "skipped"]


class HealthChecks(CamelModel):
    db: HealthCheckStatus
    stellar: HealthCheckStatus
    twilio: HealthCheckStatus


class HealthResponse(CamelModel):
    status: Literal["ok", "degraded", "down"]
    checks: HealthChecks
    timestamp: datetime
    version: str
    request_id: str | None = None


# ---------------------------- Domain rows -----------------------------------


class Organizer(CamelModel):
    id: str
    email: str
    phone: str | None = None
    display_name: str
    created_at: datetime
    updated_at: datetime


class Member(CamelModel):
    id: str
    whatsapp_e164: str
    display_name: str
    stellar_account: str | None = None
    created_at: datetime
    updated_at: datetime


class Round(CamelModel):
    id: str
    organizer_id: str
    name: str
    code: str
    contribution_amount_php: int
    member_count: int
    frequency: str
    start_date: date
    status: str
    paluwagan_contract_id: str | None = None
    created_at: datetime
    updated_at: datetime


class RoundMember(CamelModel):
    round_id: str
    member_id: str
    payout_position: int
    joined_at: datetime


class Contribution(CamelModel):
    id: str
    round_id: str
    member_id: str
    cycle_number: int
    amount_php: int
    stellar_tx_hash: str | None = None
    status: str
    source_message_sid: str | None = None
    created_at: datetime
    updated_at: datetime


class Payout(CamelModel):
    id: str
    round_id: str
    member_id: str
    cycle_number: int
    amount_php: int
    stellar_tx_hash: str | None = None
    status: str
    created_at: datetime
    updated_at: datetime


class ReputationEvent(CamelModel):
    id: str
    member_id: str
    event_type: str
    weight: int
    stellar_tx_hash: str
    context: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime


class RoundMemberWithMember(RoundMember):
    member: Member


class RoundDetail(Round):
    members: list[RoundMemberWithMember] = Field(default_factory=list)
    contributions: list[Contribution] = Field(default_factory=list)
    payouts: list[Payout] = Field(default_factory=list)


# ---------------------------- Async ack envelopes ---------------------------


class PostContributionsResponse(CamelModel):
    contribution_id: str
    status: Literal["pending"] = "pending"
    job_id: str


class PostRoundActivateResponse(CamelModel):
    round_id: str
    job_id: str
    status: Literal["activation_pending"] = "activation_pending"


class PostRoundCloseResponse(CamelModel):
    job_id: str
    status: Literal["close_pending"] = "close_pending"


class PostPayoutsDistributeResponse(CamelModel):
    job_id: str
    status: Literal["payout_pending"] = "payout_pending"


class GetReputationResponse(CamelModel):
    member_id: str
    score: int
    events: list[ReputationEvent] = Field(default_factory=list)


class GetContributionsResponse(CamelModel):
    data: list[Contribution]


class PostDevSimulateMessageResponse(CamelModel):
    accepted: Literal[True] = True
    twilio_sid: str


# ---------------------------- Errors ----------------------------------------


class ApiError(CamelModel):
    code: str
    message: str
    request_id: str | None = None
    details: dict[str, Any] | None = None


class ApiErrorResponse(CamelModel):
    error: ApiError
