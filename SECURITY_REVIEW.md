# DAMAY Security Review — Phase 5

**Date:** 2026-05-23
**Reviewer:** security-reviewer subagent
**Branch:** claude/damay-sprint-orchestration-aMF4A
**Verdict:** **PASS_WITH_NOTES** — no High open. Demo not blocked.

## Summary

| Severity | Count |
|---|---|
| High | 0 |
| Medium | 2 |
| Low | 3 |
| Informational | 2 |

---

## Findings

### [MED-1] Twilio webhook signature validation can be globally disabled by env flag

- **Location:** `apps/api/src/damay_api/routers/webhooks.py:352-374`. Default `WebhookSettings.twilio_webhook_validation=True`, but `TWILIO_WEBHOOK_VALIDATION=false` env silently disables verification with only a `logger.warning`.
- **Category:** Crypto / AuthZ.
- **Details:** A misconfigured prod env (or attacker who can flip env) silently accepts any inbound to `/v1/webhooks/twilio`, which drives Soroban writes (`enqueue_stellar_contribute`) and DB writes (`add_round_member`). A single startup warning is easy to miss.
- **Recommendation:** Refuse to boot in `node_env=production` when validation is disabled; or hard-fail the request with 500. Expose validation status in `/healthz`.
- **Status:** Open (config-level, not a code path bug — keep for post-demo).

### [MED-2] Generic exception handler echoes raw exception string

- **Location:** `apps/api/main.py:188-200` — `get_logger(...).error("unhandled_exception", error=str(exc))`.
- **Category:** Logging / Info disclosure.
- **Details:** `str(exc)` from Supabase / Stellar SDK clients can include connection strings, hostnames, or partial JWT fragments. Logged into structured logs.
- **Recommendation:** Log `type(exc).__name__` + `request_id`; keep the message under a redaction allow-list. Body returned to client is already sanitized.
- **Status:** Open, low likelihood, easy fix post-demo.

### [LOW-1] `simulate_message` dev endpoint defaults to enabled

- **Location:** `apps/api/src/damay_api/routers/webhooks.py:83-100` — `feature_demo_mode=True` by default, so `dev_endpoints_enabled = node_env != "production" OR feature_demo_mode` is `True` even in prod unless explicitly disabled.
- **Category:** Configuration.
- **Details:** Endpoint bypasses Twilio signature verification by design, has no auth and no rate-limit decorator, accepts arbitrary `whatsapp_e164`, drives the same backend path as a real Twilio message.
- **Recommendation:** Flip default to `feature_demo_mode=False`. Add `@limiter.limit(PUBLIC_LIMIT)`. Optionally require an `X-Demo-Token` header in prod.
- **Status:** Open — explicit demo requirement per CLAUDE.md §8 ("Demo trick"); **accept-risk for hackathon, fix immediately after**.

### [LOW-2] `next.config.mjs` CSP allows `unsafe-inline` and `unsafe-eval`

- **Location:** `apps/web/next.config.mjs:11-12`.
- **Category:** XSS hardening.
- **Details:** Required by Next.js dev mode and some shadcn components, but materially weakens CSP. `localhost:8000` is also in `connect-src` — fine for dev, should be stripped from prod builds.
- **Recommendation:** Use nonced inline scripts in prod (Next.js 15 supports it via `headers()`-with-nonce middleware). Drop `localhost:8000` when `NODE_ENV=production`.
- **Status:** Open, acceptable for hackathon.

### [LOW-3] `webhook_public_base_url` unset falls back silently

- **Location:** `apps/api/src/damay_api/routers/webhooks.py:170-187`.
- **Category:** Configuration.
- **Details:** If deployer forgets `WEBHOOK_PUBLIC_BASE_URL`, Twilio signatures will always fail behind the reverse proxy. Warned once, but should hard-fail in prod.
- **Recommendation:** In `node_env=production`, raise on startup if `WEBHOOK_PUBLIC_BASE_URL` is unset.
- **Status:** Open.

### [INFO-1] `paluwagan/src/lib.rs:337` uses `.unwrap()` on `list.get(i)`

- **Location:** `contracts/paluwagan/src/lib.rs:334-343` (`contains` helper).
- **Details:** The unwrap is inside `while i < list.len()` so the index is provably in range. No user-controlled panic path.
- **Status:** Accepted-risk (sound by construction).

### [INFO-2] `compare_digest` exposes signature length on failure

- **Location:** `apps/api/src/damay_api/services/twilio_signature.py:66-72`.
- **Details:** `compare_digest` handles unequal lengths safely. Logged `received_len`/`expected_len` is a tiny side channel on failure only, not exploitable for forgery (HMAC-SHA1 digest length is fixed at 28 chars b64).
- **Status:** Accepted.

---

## Checklist completed

- [x] **(1) gitleaks v8.18.4** — `gitleaks detect --no-banner --verbose`: 10 commits scanned, **no leaks found**. Verified `.env.local` is gitignored, `deployments.json` mode 0600, `.env.example` placeholders only.
- [x] **(2) Endpoint auth audit — 16 backend routes, 0 mismatches:**
  - `GET /healthz` — public, PUBLIC_LIMIT (60/min). OK.
  - `POST/GET /v1/rounds`, `GET /v1/rounds/{id}`, `POST /v1/rounds/{id}/{activate,close,members}` — `OrganizerDep` (JWT HS256) + AUTH_LIMIT (600/min). OK.
  - `POST/GET /v1/members`, `GET /v1/members/{id}` — `OrganizerDep` + AUTH_LIMIT. OK.
  - `POST/GET /v1/contributions`, `POST /v1/payouts/{round_id}/distribute` — `OrganizerDep` + AUTH_LIMIT. OK.
  - `GET /v1/reputation/{member_id}` — `OrganizerDep` + AUTH_LIMIT. OK.
  - `POST /v1/webhooks/twilio` — Twilio HMAC-SHA1 signature via `verify_twilio_signature` (`hmac.compare_digest`). OK (see MED-1).
  - `POST /v1/dev/simulate-message` — gated by `dev_endpoints_enabled`, 404 in prod when correctly configured. See LOW-1.
  - Frontend: `/dashboard/**` redirects to `/login` via `dashboard/layout.tsx:9-12` when `getSession()` is empty. Demo-mode bypass is intentional and documented in `lib/auth.ts:17`.
- [x] **(3) Soroban audit pass:**
  - **Auth:** `init`/`record_contribution`/`record_default`/`record_payout_received` in reputation all call `admin.require_auth()` after admin lookup. `init_round`/`close_round` in paluwagan call `organizer.require_auth()`. `contribute` calls `member.require_auth()`. `distribute_payout` permissionless by design (deadline + all-contributed gated). **ALL 8 mutating fns covered.**
  - **Overflow:** every score/timestamp op uses `saturating_add` / `saturating_mul` / `saturating_sub`. Two raw subtractions reviewed: `now - last_event_ts` guarded by `now <= last_event_ts` early-return; `cycle - 1` guarded by `cycle == 0` early-return. Safe.
  - **Re-entrancy:** no cross-contract `invoke` calls. N/A.
  - **Unwrap/panic:** 1 `.unwrap()` at `paluwagan/lib.rs:337` — safe-by-construction (INFO-1). 0 `panic!`, 0 `.expect()`.
  - **Storage hygiene:** `instance` = admin + config; `persistent` = per-member records + cycle contributions + payout flags. No `temporary`. TTL bumped on every write.
- [x] **(4) Security headers** (`next.config.mjs`): CSP present (unsafe-inline noted as LOW-2), HSTS `max-age=63072000; includeSubDomains; preload`, X-Content-Type-Options nosniff, X-Frame-Options DENY, Referrer-Policy strict-origin-when-cross-origin, Permissions-Policy locked, `poweredByHeader: false`. (Live header probe deferred — prod not deployed from sandbox.)
- [x] **(5) RLS sanity** (`apps/api/supabase/migrations/0001_initial.sql`): every table has `enable row level security`. Per-table policies present:
  - `organizers`: `id = auth.uid()` + service_role insert.
  - `members`, `messages`, `idempotency_keys`, `stellar_jobs`: service_role-only.
  - `rounds`, `round_members`, `contributions`, `payouts`: `organizer_id = auth.uid()` (EXISTS join through `rounds` for child tables) + service_role escape hatch.
  - `reputation_events`: organizer read via shared-round join + service_role.
  - Anon key gets 0 rows on every table (default deny, no policy grants anon).
- [x] **(6) PII log scrub** — no plaintext phone numbers in any logger call outside tests. `services/whatsapp.py:543` logs `to[-4:]` (last-4 suffix); `clients/twilio.py:64` uses `_redact(to_e164)` helper; `routers/webhooks.py:362-368` logs `from_suffix` + redacted body preview. No `service_role`/`jwt`/`token` strings in any logger call outside tests.
- [x] **(7) Rate limits** — `limiter` initialized with `default_limits=["60/minute"]`, `key_func` returns `org:<id>` when authenticated else IP. Every `/v1/*` route decorated `@limiter.limit(AUTH_LIMIT)` (600/min); `/healthz` decorated `@limiter.limit(PUBLIC_LIMIT)` (60/min). Wired in `main.py:131-132` with `RateLimitExceeded` handler returning 429 envelope. Webhook + dev-simulate endpoints lack decorators (Twilio rate-limited at source; see LOW-1 for dev).
- [x] **(8) OWASP top-5:**
  - **A01** covered by #2 + #5. Service role guarded behind backend, never in browser env.
  - **A02:** Twilio sig uses `hmac.compare_digest`. JWT uses explicit `algorithms=["HS256"]` whitelist — `none` rejected by jose. Secrets env-only, never logged.
  - **A03:** All POST bodies are Pydantic v2 models; FastAPI validates before service code runs. Supabase calls go through SDK methods only — `grep` for raw SQL string concat: **zero hits**.
  - **A05:** `.env.example` separates server vs `NEXT_PUBLIC_` keys; `lib/env.ts` zod-validates web env. `/dev/*` gated by env flag (LOW-1).
  - **A07:** covered by #2.

---

## Out of scope (deferred)

- Live header probe on prod (Phase 4 not deployed from sandbox).
- External penetration testing.
- Threat model deep dive.
- Sentry source map upload chain-of-custody.

---

## Files reviewed

- `apps/api/src/damay_api/deps.py`
- `apps/api/main.py`
- `apps/api/src/damay_api/routers/{rounds,members,contributions,reputation,health,webhooks}.py`
- `apps/api/src/damay_api/services/twilio_signature.py`
- `apps/api/src/damay_api/middleware/rate_limit.py`
- `apps/api/src/damay_api/clients/twilio.py`
- `apps/api/src/damay_api/services/whatsapp.py`
- `apps/api/supabase/migrations/0001_initial.sql`
- `apps/web/next.config.mjs`
- `apps/web/src/app/dashboard/layout.tsx`
- `apps/web/src/lib/{auth,env}.ts`
- `contracts/reputation/src/lib.rs`
- `contracts/paluwagan/src/lib.rs`
