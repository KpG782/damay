# DAMAY — Decision Log

Append-only record of non-obvious decisions. Every deviation from `CLAUDE.md` gets a row here with rationale and the path-not-taken.

Format:
```
## YYYY-MM-DD — <decision>
**Context:** ...
**Decision:** ...
**Path not taken:** ...
**Trade-off accepted:** ...
**Author:** <agent|orchestrator>
```

---

## 2026-05-22 — Sprint kickoff
**Context:** Stellar Philippines Hackathon @ PDAX. 5–8h timebox.
**Decision:** Orchestrator pattern with 10 single-responsibility subagents per CLAUDE.md §2. Two-contract design (Reputation + Paluwagan). Supabase + FastAPI + Next.js 15 stack.
**Path not taken:** Monolithic Next.js full-stack (rejected: backend needs Stellar SDK + Twilio webhooks better suited to Python ecosystem).
**Trade-off accepted:** Two-source-of-truth (Supabase ↔ Stellar) requires reconciliation. Deferred to post-hackathon nightly job.
**Author:** orchestrator

## 2026-05-23 — Phase 0 devops scaffold deviations
**Context:** Scaffold-only pass; deferring live deploy + Twilio webhook + Sentry wiring to Phase 4.
**Decision:**
- `apps/api/Dockerfile` uses `python:3.12-slim` (not distroless) so we can ship `curl` + `tini` for healthchecks and signal handling; uv pinned to 0.5.11 via copy from `ghcr.io/astral-sh/uv:0.5.11`.
- `apps/web/Dockerfile` assumes Next.js 15 `output: 'standalone'`; comment in file flags this contract for frontend-engineer in Phase 3.
- `easypanel.yml` omits an internal Postgres service — Supabase is external; only `SUPABASE_DB_URL` is wired.
- `ci.yml` `api-tests` and `contracts-tests` are guarded with `if [ -f ... ]` so CI stays green during Phase 0/1 before those projects exist (per orchestrator brief).
- `ci.yml` `deploy` job is a skeleton — actual EasyPanel API call is `TODO(phase-4)` pending `EASYPANEL_URL` + `EASYPANEL_API_TOKEN` secrets.
- `scripts/env-parity.sh` runs in `--ci` mode in lint job: validates `.env.example` integrity even without a `.env.local`. Strict diff mode is used locally / on a deploy host.
**Path not taken:** Distroless runtime (loses curl healthcheck simplicity); embedding Postgres in EasyPanel (Supabase already authoritative); hard-failing CI on missing api/contracts dirs (would block Phase 0 PRs).
**Trade-off accepted:** Slightly larger Python runtime (~150MB base vs ~80MB distroless) in exchange for ops ergonomics; still well under 300MB target.
**Author:** devops

## 2026-05-23 — Phase 0 architecture decisions
**Context:** Phase 0 contract design. CLAUDE.md §5 lists tables but not all column-level choices; §4 names async writes but not the queue mechanism.
**Decision:**
- `reputation_events.weight` stays an `integer` (per §6 score formula), but added a `context jsonb` column to carry round_id / cycle_number / decay metadata without schema churn per event-type.
- Introduced `stellar_jobs` table (not in §5) as the explicit write queue backing CLAUDE.md §4's "Queued writes to Stellar". Single typed payload + unique idempotency_key + visibility-timeout lock; APScheduler workers drain it.
- Introduced `idempotency_keys` table (not in §5) keyed on `(key, route)` with 24h TTL per §7.
- Added `rounds.code` (4–16 char unique) to support the WhatsApp `JOIN <code>` flow from §8 — §5 omits this column but the state machine requires a human-typable identifier.
- Hard-delete only for `draft` rounds; active/completed rounds are immutable (RLS policy blocks delete). Avoids reconciliation hell with on-chain state.
- API path prefix `/v1` adopted to allow non-breaking evolution post-hackathon. §3.3 lists endpoints unprefixed; treating prefix as cosmetic.
- Payout endpoint accepts both organizer JWT and SERVICE auth so scheduler can fire it; §6 says `distribute_payout` is permissionless after deadline, so the endpoint guard is policy not chain enforcement.
- Members table is fully service-role gated (no organizer-direct RLS); cross-org read access is mediated through the API which joins through `round_members`. Cleaner authorization model than per-row RLS unions across rounds.
**Path not taken:**
- Per-event-type reputation columns (rejected: every new event type would require migration).
- Redis-based queue (rejected: extra infra in 8h sprint; Postgres SKIP LOCKED is sufficient at this scale).
- Soft-delete on all tables (rejected: complicates RLS and unique constraints; status enums already model lifecycle).
**Trade-off accepted:** Postgres-as-queue won't scale past ~50 jobs/sec, fine for hackathon and well past v1.0 traffic; revisit if Late-Night Lend ships.
**Author:** architect

## 2026-05-23 — Phase 1 contracts decisions
**Context:** CLAUDE.md §6 specifies two Soroban contracts. Brief pinned `soroban-sdk = "22.0.0"` but allowed picking latest stable if documented.
**Decision:**
- Pinned `soroban-sdk = "22.0.0"` (resolves to latest 22.x patch — `22.0.11` at build time). Newer 26.x is GA but requires rustc 1.91; 22.x is the most-deployed line on hackathon judging infra and our toolchain is rustc 1.94 so 22.x compiles cleanly.
- Reputation decay applied **at read-time**, not on every mutation: cheaper writes, deterministic reads, no background job needed. Cap at 240 decay periods (~20y) so an untouched member converges to 0 without runaway iteration.
- Reputation `weight = 0` rejected with `ZeroWeight`: distinguishes "no-op call" (caller bug) from a real event; keeps history meaningful.
- Reputation history bounded to 100 entries / member (FIFO prune). Storage griefing protection; older entries still observable via on-chain event log.
- Paluwagan stores **one round per contract instance** (mirrors §6 spec "round state machine"). Backend deploys a fresh contract for each new round; same WASM, different storage. Cheaper isolation + simpler auth than a multi-round registry.
- `distribute_payout` is **permissionless after deadline + complete contributions** — anyone can trigger, including the scheduler. Matches §6 ("permissionless after cycle deadline") and lets the backend retry without auth juggling.
- `contribute` blocks once the cycle's payout is distributed (`AlreadyDistributed`) — keeps post-payout state immutable.
- Live testnet deploy not executed from the build sandbox (no `stellar` CLI installed there). `deployments.json` carries `status: PENDING_DEPLOY` with explanatory note. `scripts/deploy_testnet.sh` is idempotent and will populate IDs on first run from any machine with the CLI + friendbot reachable.
**Path not taken:**
- Single multi-round Paluwagan contract (rejected: forces composite keys + per-round auth lookups; one-round-per-contract is the Soroban-idiomatic shape).
- Decay-on-write (rejected: doubles write cost, complicates testing, no read-time benefit).
- soroban-sdk 26.x (rejected: not yet broadly indexed by stellar.expert as of judging date; 22.x renders all event topics correctly in the explorer).
**Trade-off accepted:** Per-round contract deploys cost a few XLM each in mainnet rent — fine for hackathon (testnet) and still affordable for v1 mainnet (~$0.01/round at current XLM price).
**Author:** soroban-engineer

## 2026-05-23 — Phase 1 DoD gap: live testnet deploy blocked by sandbox network policy
**Context:** Orchestrator attempted to satisfy the Phase 1 DoD (§12: "contracts deployed to testnet, IDs in `deployments.json`") by installing stellar-cli 22.8.1 and running `scripts/deploy_testnet.sh`. WASM built cleanly to wasm32v1-none, hashes recorded. Soroban RPC, Horizon, and friendbot endpoints all return HTTP 403 from this environment's egress proxy, so deploy + init cannot complete here.
**Decision:**
- WASM hashes (`reputation: 9963…2b9c`, `paluwagan: 9198…7b6f`) and deployer account written to `deployments.json` with `status=PENDING_DEPLOY`.
- `scripts/deploy_testnet.sh` patched to autodetect `wasm32v1-none` (stellar-cli 22.x default) vs the older `wasm32-unknown-unknown` path — fixes a real bug, not just a workaround.
- `.gitignore` updated to exclude `.stellar/` identity dir created by the CLI during the attempt.
- Backend (Phase 2) will be wired to read `REPUTATION_CONTRACT_ID` and `PALUWAGAN_CONTRACT_ID` from env (already in `.env.example`); contract clients will graceful-degrade to mock mode when IDs are unset so dev + tests run without on-chain deps.
**Path not taken:** Proxying through a residential network (out of scope for hackathon ops); ephemeral mainnet deploy (cost + no reason).
**Trade-off accepted:** Live IDs must be populated by Ken running `bash scripts/deploy_testnet.sh` from a machine with public network access before the demo. Idempotent, ~30s wall time. Verified clean WASM + idempotent script reduces the residual risk to "one bash command on demo day."
**Author:** orchestrator

## 2026-05-23 — Phase 2 WhatsApp router: store Protocol + pure state machine + no schema diff
**Context:** The whatsapp-integrator's slice landed alongside the backend-engineer's FastAPI shell. Two coordination questions came up: (a) how to write router code before backend's Supabase client exists, and (b) whether to add a new `outbound_messages` / `dead_letter_messages` table for failed Twilio outbound retries.
**Decision:**
- All DB access in `services/whatsapp.py` and `routers/webhooks.py` goes through a `WhatsAppStore` Protocol with an `InMemoryStore` reference impl. Backend-engineer ships the Supabase-backed implementation and wires it via `app.dependency_overrides[webhooks.get_store]` in `main.py`. No hard import of any unfinished backend client.
- The state machine is implemented as a *pure* class (`StateMachine.transition(state, event, ctx) -> TransitionResult`) returning a list of side-effect dicts that the router applies. State is derived per-message from `round_members` + `contributions`; nothing is cached.
- Outbound retry on payout notifications uses an in-process Tenacity-style helper (`send_with_retry`) with a `dead_letter_sink` list parameter. **No new schema table was added.** When backend-engineer needs persistent dead-letters they should reuse the existing `stellar_jobs` envelope (add a `notify_member` `stellar_job_type` enum value) rather than introduce a parallel queue. Logged here so we don't drift.
- `/dev/simulate-message` is mounted unconditionally on the router but guarded per-request by `WebhookSettings.dev_endpoints_enabled` (true iff `NODE_ENV != production` OR `FEATURE_DEMO_MODE=true`); disabled paths return a clean 404 indistinguishable from "route not present."
- `messages.twilio_sid UNIQUE` is the *only* replay defence. `record_message` returns False on dedupe hit and the handler short-circuits to empty TwiML. No additional idempotency table needed for the webhook path (matches §3 of ARCHITECTURE.md).
**Trade-off accepted:** InMemoryStore is duplicated test/demo logic that backend-engineer's Supabase store must shadow exactly; we mitigate by keeping the `WhatsAppStore` Protocol surface minimal (10 methods) and asserting on observable behaviour, not implementation.
**Author:** whatsapp-integrator

## 2026-05-23 — Phase 2 backend decisions
**Context:** FastAPI gateway, idempotency, async Stellar queue, mock-mode fallback.
**Decision:**
- Single `SupabaseClient` with in-memory fallback when `SUPABASE_URL`/service key are unset, so tests + dev + mock-mode demos boot without a real DB. Same mock toggle applies to Twilio + Stellar.
- Idempotency middleware uses an in-process `InMemoryIdempotencyStore` for now; production swap to a `idempotency_keys`-backed store is one class change. ARCHITECTURE.md §2.1 24h TTL is honoured by the table schema; in-memory store ignores TTL (acceptable for hackathon).
- Stellar contract submission is *not* implemented inline — `StellarClient._submit_contract` returns a synthetic `tx_hash` in mock mode and a placeholder path otherwise. Production submission is intended to shell out to `stellar` CLI from the worker host (per `contracts/README.md` example). Documented in `clients/stellar.py`.
- Auth bypass token `test-service-token` is honoured only when `SUPABASE_JWT_SECRET` is unset — dev-only escape hatch for the WhatsApp state machine to call `/v1/contributions` without a JWT.
- SlowAPI in-memory storage is reset between tests via `limiter.reset()` in autouse fixture, otherwise the rate-limit bucket leaks across tests.
- 8 pre-existing whatsapp-integrator webhook tests fail on Twilio signature verification (their URL reconstruction expects host that differs from `http://test`). Outside backend-engineer scope; left untouched.
- Backend tests share `tests/conftest.py` with the whatsapp-integrator's fixtures; `app`/`client` heuristically switch between full-app and webhook-only-app based on whether the test references the `store` fixture.
**Path not taken:** Live supabase-py async client (uses `realtime` + `gotrue` which pull extra deps). PostgREST over httpx is enough for service-role reads/writes.
**Trade-off accepted:** In-memory idempotency store loses replay protection across worker restarts — fine for hackathon, swap before prod.
**Author:** backend-engineer

## 2026-05-23 — Phase 2 followup — Twilio signature URL must be the public URL
**Context:** 8/42 whatsapp-integrator webhook tests failed with HTTP 403 (signature rejected). Root cause was a real production bug, not a test artifact: the webhook handler reconstructed the signing URL from `request.url`, which is the *internal* URL the ASGI app observes (`http://test/webhooks/twilio` under pytest, `http://api:8000/...` behind an EasyPanel/nginx/Cloudflare ingress in prod). Twilio signs the *public* URL it POSTed to (`https://api.damay.kenbuilds.tech/webhooks/twilio`); the two HMACs never match, so every webhook 403s the moment a reverse proxy sits in front of the API.
**Decision:**
- Added `WEBHOOK_PUBLIC_BASE_URL` to `Settings` (`apps/api/src/damay_api/config.py`) and to the router's local `WebhookSettings` dataclass (`apps/api/src/damay_api/routers/webhooks.py`). When set, the router computes `f"{base.rstrip('/')}{request.url.path}?{request.url.query}"` and feeds *that* to `verify_twilio_signature`. When unset, falls back to `str(request.url)` and emits a one-time WARNING urging the operator to set it. The fallback is dev-only convenience; production must set the env var.
- Query string (if any) is preserved on both branches — Twilio rarely includes one on inbound but it's part of the signed string when present.
- `.env.example` documents the var under the Twilio section with the prod URL as the default and the dev guidance inline.
- `tests/conftest.py` sets `WEBHOOK_PUBLIC_BASE_URL=https://api.test` at import time AND passes the matching `webhook_public_base_url` into the `settings_fixture` so dependency-overridden settings agree with the test's signing constant (`WEBHOOK_URL = "https://api.test/webhooks/twilio"` in `test_webhook_twilio.py`). The test constant was correct; the production code was wrong.
- `/dev/simulate-message` already bypasses `verify_twilio_signature` by design (gated by `dev_endpoints_enabled`) — left unchanged. Confirmed it does not call `_signing_url`.
**Verification:** `tests/test_webhook_twilio.py` 42/42, `tests/test_simulate_message.py` included in that count, full backend suite 63/63.
**Path not taken:** Pulling host from `X-Forwarded-Host`/`X-Forwarded-Proto` headers — works but trusts whatever the proxy sets, which is a footgun if any non-prod entry point exists. Explicit env var is auditable and unambiguous.
**Trade-off accepted:** One additional required env var in production. Cheap.
**Author:** whatsapp-integrator (Phase 2 followup)

---

## 2026-05-23 — Web demo-mode fallback when Supabase is unset
**Context:** Phase 3 frontend ships before Supabase is provisioned. We need /dashboard and the full demo flow clickable in the build/start lifecycle with zero external services.
**Decision:**
- `src/lib/env.ts` exposes `isSupabaseConfigured` and `isDemoMode = !isSupabaseConfigured`.
- `src/lib/auth.ts` `getSession()` returns a deterministic `Carmela` demo organizer when in demo mode, so the dashboard layout's redirect-to-/login still works correctly in real auth mode (no creds → /login) but the demo path is unbroken.
- `src/lib/api.ts` falls back to seeded data (Filipino names per style guide) when the FastAPI backend at `NEXT_PUBLIC_API_URL` is unreachable. Every fallback path also returns `isLive: false` so the UI can surface an "Offline — demo data" badge.
- `src/components/brand/ServiceWorker.tsx` only registers `/sw.js` in production builds; dev HMR is unaffected.
**Trade-off accepted:** Demo-mode helper code stays in the production bundle (~1 KB). Worth it for hackathon resilience.
**Author:** frontend-engineer (Phase 3)

## 2026-05-23 — Phase 4 deploy: runbook over live deploy
**Context:** Phase 4 brief requires live URLs on `damay.kenbuilds.tech` and `api.damay.kenbuilds.tech`. Sandbox reachability probe:
- github.com → 200, ghcr.io → 301 (reachable)
- registry-1.docker.io → 404, easypanel.io → 403, api.easypanel.io → 403 (no auth path)
- docker CLI present but **dockerd not running** (`/var/run/docker.sock` missing)
- `*.stellar.org` already known blocked (see prior entry; `deployments.json` still `PENDING_DEPLOY`)
**Decision:** Path B — ship a deterministic runbook instead of faking a deploy.
- `EASYPANEL_DEPLOY.md`: 11-step runbook from zero to live, with the exact env-var table, Twilio CLI command, Sentry steps, post-deploy curls, and rollback procedure.
- `docker-compose.yml`: local mirror of prod shape (api + web only, Supabase external).
- `scripts/preflight.sh`: gate before deploy — env-parity + docker builds + size budgets (300/200 MB) + boot + healthcheck poll. Exit 0 only on full green.
- `.github/workflows/ci.yml` `deploy` job rewritten to build+push to GHCR with per-SHA + latest tags and call EasyPanel `app.updateSourceImage` + `app.deployService` for both services. Gated by `EASYPANEL_API_TOKEN` so PRs / fork builds no-op cleanly. Post-deploy smoke step curls both prod URLs.
- Dockerfiles verified: web `output: 'standalone'` confirmed in `apps/web/next.config.mjs:25`; api uvicorn target `main:app` matches `apps/api/main.py:217` (`app = create_app()`).
**Path not taken:** Faking a successful curl against the prod domain from sandbox (would corrupt the DoD signal); embedding EasyPanel API token in repo to demo the call (security violation).
**Trade-off accepted:** Phase 4 DoD ("prod URL responds, Twilio webhook hits prod, Stellar tx visible on Stellar Expert") cannot close from this sandbox. Residual = §0 + §1 + §3 + §5 + §6 of `EASYPANEL_DEPLOY.md` must be run from Ken's workstation. Every subsequent push to `main` deploys automatically once secrets are set.
**Author:** devops (Phase 4)

## 2026-05-23 — Phase 5 QA: e2e workspace + top-level fuzz crate
**Context:** QA needed Playwright e2e suite and 500-iter fuzz per contract.
**Decision:** Added `e2e/` as a third pnpm workspace path (alongside `apps/*` + `packages/*`) and a new `contracts/tests/` cargo workspace member (`damay-contract-fuzz`) holding `tests/fuzz.rs`.
**Path not taken:** Putting fuzz directly in each contract's `src/test.rs` would have kept testutils variant matching (`Err(Ok(Error::X))`), but it would tangle property-test loops with unit tests and force per-crate `cargo test` invocations. A top-level fuzz crate gives a single `cargo test --release -p damay-contract-fuzz` invocation; the only cost is coarser error matching from outside the contract crate (acceptable — variant-level coverage already lives in the per-crate unit tests).
**Trade-off accepted:** Outside-the-crate `try_*` collapses contract errors into a generic outer `Err`, so fuzz invariants assert success preconditions (`ok(&r) → initialized && weight > 0`) instead of matching exact `Error::ZeroWeight` etc.
**Author:** qa-engineer

## 2026-05-23 — Phase 5 QA: auth e2e is demo-mode aware
**Context:** Brief asked for an RLS check ("non-org user cannot read other org's rounds"). The web app is intentionally in demo mode for the hackathon (Supabase env unset → `getSession` returns a deterministic demo organizer), so a `/dashboard → /login` redirect never fires in this stack.
**Decision:** `e2e/tests/auth.spec.ts` documents the demo-mode bypass and replaces the redirect assertion with two API-layer guards: (1) `GET /v1/rounds` with no JWT must 401/403, (2) `GET /v1/rounds` with a JWT for an unknown organizer must not leak any seeded round IDs.
**Path not taken:** Booting the e2e stack with Supabase configured + a seeded organizers row would have exercised the real redirect, but it requires standing up Supabase in CI (heavy, time-blowing). The split keeps the hackathon demo mode reachable while still proving the API-side guarantee.
**Trade-off accepted:** Web-layer redirect-to-login is unit/integration-tested elsewhere; e2e asserts the boundary behaviour at the API.
**Author:** qa-engineer
