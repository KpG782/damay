/**
 * Webhook replay — POST the same Twilio payload twice, assert single
 * side effect. Verifies the `messages.twilio_sid UNIQUE` invariant
 * (ARCHITECTURE.md §5.3) at the live HTTP boundary.
 *
 * Signs the payload with HMAC-SHA1 against the same auth token + URL the API
 * is configured with (TWILIO_AUTH_TOKEN + WEBHOOK_PUBLIC_BASE_URL).
 */

import { test, expect } from "@playwright/test";
import * as crypto from "node:crypto";

const API_URL = "http://127.0.0.1:8000";
const WEBHOOK_PATH = "/webhooks/twilio";
const SIGNING_URL = `${API_URL}${WEBHOOK_PATH}`;
const TWILIO_TOKEN = "test-e2e-token";

/**
 * Replicate Twilio's signing algorithm:
 *   sort POST params by key, concat `key+value` (no separator), prepend the
 *   full URL, HMAC-SHA1 with auth token, base64 the digest.
 *
 * Mirrors apps/api/.../services/twilio_signature.py.
 */
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
  test("duplicate MessageSid produces a single side effect", async ({ request }) => {
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

    // First delivery — must 200.
    const r1 = await request.post(SIGNING_URL, { headers, data: body });
    expect(r1.status()).toBe(200);
    const xml1 = await r1.text();
    expect(xml1).toMatch(/<Response/);

    // Replay — same SID, same signature. Must also 200 (Twilio expects 200
    // to stop retrying), but no second outbound message and no second
    // inbound row should be created. The router returns an empty TwiML
    // `<Response/>` on dedupe (see webhooks.py:_process_inbound).
    const r2 = await request.post(SIGNING_URL, { headers, data: body });
    expect(r2.status()).toBe(200);
    const xml2 = await r2.text();
    // Empty Response on duplicate (no <Message> body).
    expect(xml2).toMatch(/<Response\s*\/?>(\s*<\/Response>)?$/);
    expect(xml2).not.toMatch(/<Message>/);
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
