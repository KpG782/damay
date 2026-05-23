"""Request models. Field names camelCase on the wire, snake_case in Python."""

from __future__ import annotations

import re
from datetime import date
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator
from pydantic.alias_generators import to_camel

RoundFrequency = Literal["weekly", "biweekly", "monthly"]
RoundStatus = Literal["draft", "active", "completed", "cancelled"]

E164_RE = re.compile(r"^\+[1-9][0-9]{6,14}$")
STELLAR_ACCOUNT_RE = re.compile(r"^G[A-Z2-7]{55}$")


class CamelModel(BaseModel):
    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        str_strip_whitespace=True,
    )


# ---------------------------- /v1/rounds ------------------------------------


class PostRoundsRequest(CamelModel):
    name: str = Field(min_length=1, max_length=120)
    contribution_amount_php: int = Field(gt=0, le=1_000_000)
    member_count: int = Field(ge=2, le=50)
    frequency: RoundFrequency
    start_date: date
    code: str | None = Field(default=None, min_length=4, max_length=16)


class GetRoundsQuery(CamelModel):
    status: RoundStatus | None = None
    limit: int = Field(default=20, ge=1, le=100)
    cursor: str | None = None


# ---------------------------- /v1/members -----------------------------------


class PostMembersRequest(CamelModel):
    whatsapp_e164: str
    display_name: str = Field(min_length=1, max_length=120)

    @field_validator("whatsapp_e164")
    @classmethod
    def _check_e164(cls, v: str) -> str:
        if not E164_RE.match(v):
            raise ValueError("whatsapp_e164 must be E.164 (e.g. +639171234567)")
        return v


class PostRoundMembersRequest(CamelModel):
    member_id: str
    payout_position: int = Field(ge=1, le=50)


# ---------------------------- /v1/contributions -----------------------------


class PostContributionsRequest(CamelModel):
    round_id: str
    member_id: str
    cycle_number: int = Field(ge=1)
    amount_php: int = Field(gt=0)
    source_message_sid: str | None = None


class GetContributionsQuery(CamelModel):
    round_id: str
    cycle: int | None = None


# ---------------------------- /v1/payouts -----------------------------------


class PostPayoutsDistributeRequest(CamelModel):
    cycle_number: int = Field(ge=1)


# ---------------------------- /v1/dev ---------------------------------------


class PostDevSimulateMessageRequest(CamelModel):
    from_: str = Field(alias="from")
    body: str
    synthetic_sid: str | None = None

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
    )
