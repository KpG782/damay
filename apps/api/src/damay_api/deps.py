"""FastAPI dependencies."""

from __future__ import annotations

from typing import Annotated

from fastapi import Depends, Header, HTTPException, Request, status
from jose import JWTError, jwt

from damay_api.clients.stellar import StellarClient, get_stellar
from damay_api.clients.supabase import SupabaseClient, get_supabase
from damay_api.clients.twilio import TwilioClient, get_twilio
from damay_api.config import Settings, get_settings


def settings_dep() -> Settings:
    return get_settings()


SettingsDep = Annotated[Settings, Depends(settings_dep)]


async def supabase_dep(settings: SettingsDep) -> SupabaseClient:
    return await get_supabase(settings)


SupabaseDep = Annotated[SupabaseClient, Depends(supabase_dep)]


def stellar_dep(settings: SettingsDep) -> StellarClient:
    return get_stellar(settings)


StellarDep = Annotated[StellarClient, Depends(stellar_dep)]


def twilio_dep(settings: SettingsDep) -> TwilioClient:
    return get_twilio(settings)


TwilioDep = Annotated[TwilioClient, Depends(twilio_dep)]


class CurrentOrganizer:
    """Resolved organizer subject from the Supabase JWT."""

    def __init__(self, organizer_id: str, email: str | None = None) -> None:
        self.id = organizer_id
        self.email = email


def require_organizer(
    request: Request,
    settings: SettingsDep,
    authorization: Annotated[str | None, Header()] = None,
) -> CurrentOrganizer:
    """Verify Supabase JWT (HS256) and inject the organizer subject."""
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "UNAUTHENTICATED", "message": "Missing bearer token."},
        )
    token = authorization.split(" ", 1)[1].strip()
    secret = settings.supabase_jwt_secret or settings.jwt_secret
    if not secret:
        # In dev/test we permit a SERVICE-style bypass token if explicit.
        if token == "test-service-token":
            request.state.organizer_id = "00000000-0000-0000-0000-000000000001"
            return CurrentOrganizer(organizer_id=request.state.organizer_id)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "code": "UNAUTHENTICATED",
                "message": "Server is not configured with a JWT secret.",
            },
        )
    try:
        payload = jwt.decode(
            token,
            secret,
            algorithms=["HS256"],
            options={"verify_aud": False},
        )
    except JWTError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "UNAUTHENTICATED", "message": f"Invalid token: {e}"},
        ) from e
    sub = payload.get("sub")
    if not sub:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "UNAUTHENTICATED", "message": "Token missing sub."},
        )
    request.state.organizer_id = sub
    return CurrentOrganizer(organizer_id=sub, email=payload.get("email"))


OrganizerDep = Annotated[CurrentOrganizer, Depends(require_organizer)]
