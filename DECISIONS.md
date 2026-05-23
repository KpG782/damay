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
