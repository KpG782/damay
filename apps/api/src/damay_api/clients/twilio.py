"""Twilio outbound client.

Inbound webhook handling is owned by the ``whatsapp-integrator`` agent and
lives in ``routers/webhooks.py``. This module exposes ONLY the outbound
``send_whatsapp`` surface plus a healthcheck — both organizer alerts and the
whatsapp state machine route through it.
"""

from __future__ import annotations

import base64

import httpx
import pybreaker
import structlog
from tenacity import (
    AsyncRetrying,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential_jitter,
)

from damay_api.config import Settings

logger = structlog.get_logger("damay.twilio")


class TwilioError(Exception):
    """Raised when Twilio returns 4xx/5xx or is unreachable."""


class TwilioClient:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.mock = settings.twilio_mock_mode
        self._breaker = pybreaker.CircuitBreaker(fail_max=3, reset_timeout=60)
        self._client = httpx.AsyncClient(
            timeout=httpx.Timeout(5.0, connect=2.0),
        )

    async def aclose(self) -> None:
        await self._client.aclose()

    def _auth_header(self) -> dict[str, str]:
        token = f"{self.settings.twilio_account_sid}:{self.settings.twilio_auth_token}"
        return {"Authorization": "Basic " + base64.b64encode(token.encode()).decode()}

    async def ping(self) -> bool:
        if self.mock:
            return True
        try:
            url = (
                f"https://api.twilio.com/2010-04-01/Accounts/"
                f"{self.settings.twilio_account_sid}.json"
            )
            r = await self._client.head(url, headers=self._auth_header(), timeout=1.0)
            return r.status_code < 500
        except Exception:
            return False

    async def send_whatsapp(self, to_e164: str, body: str) -> dict:
        """Send a WhatsApp message. ``to_e164`` is a bare ``+639...`` number."""
        if self.mock:
            logger.info("twilio_mock_send", to=_redact(to_e164), body_len=len(body))
            return {"sid": "SM_mock_" + base64.b32encode(to_e164.encode()).decode()[:16], "mock": True}

        async def call() -> dict:
            url = (
                f"https://api.twilio.com/2010-04-01/Accounts/"
                f"{self.settings.twilio_account_sid}/Messages.json"
            )
            data = {
                "From": self.settings.twilio_whatsapp_from,
                "To": f"whatsapp:{to_e164}",
                "Body": body,
            }
            r = await self._client.post(url, headers=self._auth_header(), data=data)
            if r.status_code >= 500:
                raise TwilioError(f"twilio {r.status_code}: {r.text[:200]}")
            if r.status_code >= 400:
                # Don't retry 4xx
                logger.warning("twilio_4xx", status=r.status_code, body=r.text[:200])
                raise TwilioError(f"twilio {r.status_code}: {r.text[:200]}")
            return r.json()

        try:
            retryer = AsyncRetrying(
                stop=stop_after_attempt(3),
                wait=wait_exponential_jitter(initial=0.5, max=2.0),
                retry=retry_if_exception_type((httpx.TransportError, TwilioError)),
                reraise=True,
            )
            async for attempt in retryer:
                with attempt:
                    return await self._breaker.call_async(call)
        except pybreaker.CircuitBreakerError as e:
            raise TwilioError(f"circuit open: {e}") from e
        except Exception as e:
            raise TwilioError(str(e)) from e
        raise TwilioError("unreachable")


def _redact(e164: str) -> str:
    return e164[:4] + "****" + e164[-2:] if len(e164) > 6 else "****"


_singleton: TwilioClient | None = None


def get_twilio(settings: Settings) -> TwilioClient:
    global _singleton
    if _singleton is None:
        _singleton = TwilioClient(settings)
    return _singleton


def reset_twilio_singleton() -> None:
    global _singleton
    _singleton = None
