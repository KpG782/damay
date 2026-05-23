/**
 * Webhook replay — POST the same Twilio payload twice, assert idempotent
 * end-to-end behaviour. Verifies the `messages.twilio_sid UNIQUE` invariant
 * (ARCHITECTURE.md §5.3) at the live HTTP boundary.
 *
 * Signs the payload with HMAC-SHA1 against the same auth token + URL the API
 * is configured with (TWILIO_AUTH_TOKEN + WEBHOOK_PUBLIC_BASE_URL).
 *
 * The single-DB-row / single-outbound-message invariant is covered with
 * direct store access in `apps/api/tests/test_webhook_twilio.py`
 * (test_duplicate_message_sid_is_no_op). At this layer we confirm:
 *   - both deliveries return 200 (so Twilio stops retrying),
 *   - both return the same TwiML payload (idempotent reply shape),
 *   - bad signatures are rejected with 403.
 */

import { test, expect } from "@playwright/test";
import * as crypto from "node:crypto";

const API_URL = "http://127.0.0.1:8000";
const WEBHOOK_PATH = "/v1/webhooks/twilio";
const SIGNING_URL = `${API_URL}${WEBHOOK_PATH}`;
const TWILIO_TOKEN = "test-e2e-token";

/** Mirrors apps/api/.../services/twilio_signature.py. */
function computeSignature(url: string, params: Record<string, string>, token: string): string {
  const sortedKeys = Object.keys(params).sort();
  let payload = url;
  for (const k of sortedKeys) payload += k + params[k];
  return crypto.createHmac("sha1", token).update(payload, "utf8").digest("base64");
}

function formEncode(params: Record<string, string>): string {
  return Object.entries(params)
    .map(([k, v]) => `${encodeURIComponent(k)}=${encodeURIComponent(v)}`)
    .join("&");
}

test.describe("Twilio webhook replay safety", () => {
  test("duplicate MessageSid is idempotent end-to-end", async ({ request }) => {
    const sid = `SMreplay${Date.now().toString(36)}${Math.random().toString(36).slice(2, 8)}`;
    const form: Record<string, string> = {
      MessageSid: sid,
      From: "whatsapp:+639170000777",
      To: "whatsapp:+14155238886",
      Body: "HELP",
      NumMedia: "0",
    };
    const signature = computeSignature(SIGNING_URL, form, TWILIO_TOKEN);
    const headers = {
      "content-type": "application/x-www-form-urlencoded",
      "x-twilio-signature": signature,
    };
    const body = formEncode(form);

    // First delivery — must 200 with a TwiML body.
    const r1 = await request.post(SIGNING_URL, { headers, data: body });
    expect(r1.status()).toBe(200);
    const xml1 = await r1.text();
    expect(xml1).toMatch(/<Response/);
    expect(r1.headers()["content-type"]).toMatch(/application\/xml/);

    // Replay — same SID, same signature. Must also 200 (Twilio expects 200
    // to stop retrying). The TwiML reply must be identical: replaying must
    // never produce a *different* response or new outbound side effect.
    const r2 = await request.post(SIGNING_URL, { headers, data: body });
    expect(r2.status()).toBe(200);
    const xml2 = await r2.text();
    expect(xml2).toBe(xml1);
  });

  test("bad signature is rejected with 403", async ({ request }) => {
    const sid = `SMbad${Date.now().toString(36)}`;
    const form: Record<string, string> = {
      MessageSid: sid,
      From: "whatsapp:+639170000777",
      Body: "HELP",
    };
    const headers = {
      "content-type": "application/x-www-form-urlencoded",
      "x-twilio-signature": "ZG9uJ3QtdHJ1c3QtdGhpcw==",
    };
    const res = await request.post(SIGNING_URL, {
      headers,
      data: formEncode(form),
    });
    expect(res.status()).toBe(403);
  });
});
