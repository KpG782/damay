"""Twilio webhook signature verification.

Twilio signs each webhook request by:
  1. Taking the full URL (https://host/path?query) that Twilio POSTed to.
  2. Appending each POST form parameter as `key + value` (no separator), sorted
     alphabetically by key.
  3. Computing HMAC-SHA1 over the resulting string using the account's
     AUTH TOKEN as the key.
  4. Base64-encoding the digest and sending it as `X-Twilio-Signature`.

We replicate that, then compare with `hmac.compare_digest` (constant-time).

Docs: https://www.twilio.com/docs/usage/webhooks/webhooks-security
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import logging
from typing import Mapping

logger = logging.getLogger(__name__)


def compute_twilio_signature(auth_token: str, url: str, params: Mapping[str, str]) -> str:
    """Compute the expected `X-Twilio-Signature` for a given URL + form params.

    Args:
        auth_token: Twilio account AUTH TOKEN (TWILIO_AUTH_TOKEN env).
        url: Fully qualified URL Twilio POSTed to, including scheme + query.
        params: POST form parameters (string-to-string).

    Returns:
        Base64-encoded HMAC-SHA1 digest (str).
    """
    # Per Twilio: sort by key, concatenate `key + value` with no separator.
    sorted_pairs = sorted(params.items(), key=lambda kv: kv[0])
    payload = url + "".join(f"{k}{v}" for k, v in sorted_pairs)
    digest = hmac.new(
        auth_token.encode("utf-8"),
        payload.encode("utf-8"),
        hashlib.sha1,
    ).digest()
    return base64.b64encode(digest).decode("ascii")


def verify_twilio_signature(
    auth_token: str,
    url: str,
    params: Mapping[str, str],
    received_signature: str | None,
) -> bool:
    """Constant-time verify the `X-Twilio-Signature` header.

    Returns True only when a non-empty received signature matches the computed
    signature byte-for-byte. Logs (without leaking the signature itself) on
    failure.
    """
    if not received_signature:
        logger.warning("twilio_signature_missing")
        return False
    expected = compute_twilio_signature(auth_token, url, params)
    ok = hmac.compare_digest(expected, received_signature)
    if not ok:
        # Never log the received signature or AUTH TOKEN. Log shape only.
        logger.warning(
            "twilio_signature_invalid",
            extra={"received_len": len(received_signature), "expected_len": len(expected)},
        )
    return ok
