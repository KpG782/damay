# DAMAY — Production Sprint Orchestration

> **Single source of truth for this sprint.** Subagent files live in `.claude/agents/`.

---

## 0. North Star

**Mission:** Ship **DAMAY** (Paluwagan by Damay) — a trustless protocol for Filipino informal financial behaviors — in **5–8 hours**, production-grade, demo-ready for Stellar Philippines Hackathon judging at PDAX.

**Layman frame:** Paluwagan is a Filipino rotating savings circle ("you put in ₱500/week, every week someone different gets the pot"). Today it runs on trust + group chats and falls apart when someone ghosts. We're putting the trust layer on Stellar so contributions, payouts, and reputation are verifiable, while keeping the UX inside WhatsApp where the actual users already live.

**Judging axes we optimize for:** (1) real Stellar primitive use, not just "uses Stellar"; (2) Filipino market specificity; (3) live working demo; (4) polish that signals shippability.

**Hard scope cuts already made:**

- v1.0 = **organizer dashboard (web) + member WhatsApp bot + Reputation Trustline on Soroban + one full paluwagan round simulated end-to-end.**
- "Late-Night Lend" intent → v1.1 stub, contract interface only, no UI. Mentioned in pitch as roadmap.
- No KYC, no real fiat rails. Use testnet XLM + a "₱ pegged" display layer.
- No mobile app. PWA only.

If a feature is not on this list, **it is not in scope.** Push back if asked to add anything mid-sprint.

---

## 1. Operating Contract

You (Claude Code) are the **Orchestrator**. You do not write production code in the main thread except for glue, configs, and migrations. **All implementation work is delegated to subagents** (Section 16). Your job:

1. **Plan** the next phase using Section 3.
2. **Dispatch** subagents in parallel where the dependency graph allows.
3. **Verify** subagent output against the Definition of Done (Section 12) before moving on.
4. **Course-correct.** If a subagent returns work that misses DoD, send it back with the specific failing criterion — don't accept partial work to "save time."
5. **Track time.** At the start of each phase, log the wall-clock target. If a phase runs >25% over, declare it and cut scope (Section 3.6).

**Rules of engagement:**

- **No silent decisions.** Any deviation from this doc gets logged in `DECISIONS.md` with rationale before code is written.
- **No skipped tests.** Each subagent ships its own tests. The QA agent ships integration tests.
- **No secrets in code.** Ever. `.env.example` only, real values in `.env.local` (gitignored).
- **No new libraries** without justifying weight, license, and maintenance status.
- **Skills are mandatory.** Before any UI work, the frontend subagent loads `/mnt/skills/public/frontend-design/SKILL.md`. Before any document deliverables, load the relevant skill from `/mnt/skills/public/`.

---

## 2. Subagent Roster

| Name | Single Responsibility | Triggers |
|---|---|---|
| `architect` | System design, interface contracts, schema, sequence diagrams | Phase 0 + any contract changes |
| `soroban-engineer` | Rust/Soroban smart contracts, tests, deploy scripts | Phase 1, Phase 5 (integration) |
| `backend-engineer` | FastAPI services, Supabase integration, Stellar Horizon client | Phase 2 |
| `frontend-engineer` | Next.js 15 organizer PWA, shadcn/ui, design tokens | Phase 3 |
| `ui-designer` | Design tokens, component specs, brand, demo screens | Phase 0 (parallel with architect) |
| `whatsapp-integrator` | Twilio WhatsApp flows, state machine, webhook handlers | Phase 3 (parallel with frontend) |
| `devops` | Dockerfiles, EasyPanel manifest, env wiring, CI smoke | Phase 4 |
| `qa-engineer` | E2E happy path, contract fuzz, webhook replay tests | Phase 5 |
| `security-reviewer` | Secret scan, auth checks, contract audit pass, OWASP top-5 | Phase 6 |
| `docs-writer` | README, demo script, pitch one-pager, video shot list | Phase 6 (parallel with security) |

**Dispatch pattern:** Spawn parallel subagents whenever their inputs don't overlap. Block only on hard deps (e.g., frontend cannot finalize without design tokens; QA cannot run E2E without backend + contracts).

---

## 3. Phase Plan (T+0 → T+8h)

### 3.1 Phase 0 — Foundation (T+0 → T+0:45)

**Parallel dispatch:** `architect`, `ui-designer`, `devops` (scaffold only).

Deliverables:

- `ARCHITECTURE.md` — services, data flow, sequence diagram for "join → contribute → payout."
- `schema.sql` — all tables, RLS policies sketched.
- `design-tokens.ts` — colors, type scale, spacing, radii, motion.
- Repo scaffold: Turborepo with `apps/web`, `apps/api`, `contracts/reputation`, `packages/ui`, `packages/types`.
- `.env.example` populated (Section 11).
- `DECISIONS.md` initialized.

**Gate:** Architect's sequence diagram is reviewed and signed off by orchestrator before Phase 1.

### 3.2 Phase 1 — Stellar Contracts (T+0:45 → T+2:15)

**Solo:** `soroban-engineer`. Critical path — start hard, start early.

Deliverables:

- `contracts/reputation/src/lib.rs` — Reputation Trustline contract with `record_contribution`, `record_default`, `get_score`, events emitted on every state change.
- `contracts/paluwagan/src/lib.rs` — round state machine: `init_round`, `contribute`, `distribute_payout`, `close_round`.
- Unit tests: 100% of state transitions, including failure paths.
- `scripts/deploy_testnet.sh` — idempotent, prints contract IDs to `deployments.json`.
- Contract IDs committed to `deployments.json` after first successful testnet deploy.

**Gate:** All contract tests green. `deployments.json` contains live testnet contract IDs.

### 3.3 Phase 2 — Backend (T+2:15 → T+4:00)

**Parallel:** `backend-engineer` (FastAPI + Supabase), `whatsapp-integrator` (webhook + state machine stub).

Backend deliverables:

- FastAPI app: `/rounds`, `/members`, `/contributions`, `/reputation`, `/webhooks/twilio`, `/healthz`.
- Supabase migrations applied via `supabase db push`.
- Stellar Horizon client wrapper with retries (exponential backoff, max 3, jitter) and idempotency keys on every write.
- Soroban contract invocation layer (read = direct, write = queued through job table).
- Structured logging (JSON, request_id correlation).
- OpenAPI spec auto-generated at `/docs`.

WhatsApp deliverables:

- Twilio sandbox webhook signature verification.
- State machine: `IDLE → JOINED → AWAITING_CONTRIBUTION → CONTRIBUTED → PAYOUT_NOTIFIED`.
- Outbound message templates approved-format compatible.
- Replay-safe: dedupe on Twilio `MessageSid`.

**Gate:** `pytest` green. `/healthz` returns 200 with DB + Stellar + Twilio reachability check.

### 3.4 Phase 3 — Frontend (T+4:00 → T+6:00)

**Solo:** `frontend-engineer` (consumes design tokens + OpenAPI types).

Deliverables:

- Next.js 15 App Router PWA.
- Pages: `/` (landing with demo CTA), `/dashboard` (organizer view of active rounds), `/rounds/[id]` (round detail + member list + contribution timeline + Stellar tx links), `/reputation/[member]` (score + on-chain proof).
- Auth: Supabase magic link (organizer only). Member side is WhatsApp.
- Real-time: Supabase Realtime subscription on `contributions` table → live timeline updates.
- shadcn/ui components themed against design tokens.
- Loading skeletons, empty states, error boundaries — **all three are required per page.**
- Lighthouse score ≥ 90 on Performance, Accessibility, Best Practices for `/dashboard`.

**Gate:** Demo flow clickable end-to-end in browser using seeded data. PWA installable on mobile.

### 3.5 Phase 4 — Deploy (T+6:00 → T+6:45)

**Solo:** `devops`.

Deliverables:

- Multi-stage Dockerfiles for `web` and `api`.
- EasyPanel `easypanel.yml` with both services + Postgres reference + env wiring from Supabase.
- Public URLs live: `damay.kenbuilds.tech` (web) and `api.damay.kenbuilds.tech` (api).
- Twilio webhook URL pointed to production API.
- Sentry DSN wired.

**Gate:** Hit prod URL from phone, complete the demo flow, see contribution land on testnet within 30s.

### 3.6 Phase 5 — Integration & QA (T+6:45 → T+7:30)

**Parallel:** `qa-engineer`, `security-reviewer`.

QA deliverables:

- Playwright E2E: organizer creates round → 3 members join via simulated WhatsApp → all contribute → payout distributed → reputation scores updated → all events visible on testnet.
- Contract fuzz: 500 random sequences against Soroban contracts, no panics.
- Webhook replay test: send same Twilio payload twice, verify single side effect.

Security deliverables:

- `gitleaks` clean.
- All endpoints requiring auth verified.
- Soroban contracts: re-entrancy check, overflow check, auth check on every state-mutating function.
- CSP headers, HSTS, `X-Content-Type-Options: nosniff` on web.

**Scope cut protocol (invoke if behind):** Drop in this order — (1) reputation UI page (keep score in dashboard sidebar), (2) PWA install prompt, (3) real-time timeline (poll every 5s instead), (4) Sentry, (5) one of the three contract events.

### 3.7 Phase 6 — Demo Polish (T+7:30 → T+8:00)

**Parallel:** `docs-writer`, `frontend-engineer` (visual polish only).

Deliverables:

- `README.md` with architecture diagram, setup, demo steps, contract addresses.
- `DEMO_SCRIPT.md` — exact 3-minute walkthrough with timing per beat.
- Pitch one-pager (markdown — judges can read it on phone).
- Video shot list (90s vertical for socials, 3min landscape for judges).
- Seed data: 1 round, 6 members with realistic Filipino names, 3 past rounds with reputation history.

**Final gate:** Run the demo script start-to-finish in real time. If anything fails, fix or cut.

---

## 4. Architecture (Locked)

```
┌─────────────────┐         ┌─────────────────┐
│ Organizer PWA   │         │ Member          │
│ (Next.js 15)    │         │ (WhatsApp)      │
└────────┬────────┘         └────────┬────────┘
         │ HTTPS                     │ Twilio webhook
         │                           │
         ▼                           ▼
   ┌──────────────────────────────────────┐
   │ FastAPI Gateway (api.damay.*)        │
   │ - Auth (Supabase JWT)                │
   │ - Webhook signature verify           │
   │ - Idempotency layer                  │
   └────┬──────────────┬──────────────────┘
        │              │
        ▼              ▼
   ┌─────────┐    ┌──────────────────┐
   │Supabase │    │ Stellar Soroban  │
   │Postgres │    │ - Reputation     │
   │Realtime │    │ - Paluwagan      │
   └─────────┘    └──────────────────┘
```

**Why this shape:**

- **API in front of everything** so we can swap WhatsApp for SMS/Telegram later without touching contracts.
- **Supabase = system of record for off-chain data** (member profiles, round metadata, message logs). **Stellar = system of record for value + reputation.** Two sources of truth, joined by `member_id ↔ stellar_account`.
- **Realtime on Supabase** = cheap live updates without WebSocket infra.
- **Queued writes to Stellar** = backend never blocks user on chain latency; webhook returns 200 immediately, async worker submits tx.

**Trade-offs:**

- Fast to ship, swappable channels, judge-friendly observable on-chain.
- Two-source-of-truth means reconciliation needed (post-hackathon nightly diff job).
- Async tx submission = brief "pending" window; UI shows pending badge until Horizon confirms.

---

## 5. Data Model

Tables (Supabase, all with `created_at`, `updated_at`, RLS enabled):

- `organizers` — `id (uuid)`, `email`, `phone`, `display_name`
- `members` — `id (uuid)`, `whatsapp_e164`, `display_name`, `stellar_account`, `created_at`
- `rounds` — `id`, `organizer_id`, `name`, `contribution_amount_php`, `member_count`, `frequency` (`weekly`|`biweekly`|`monthly`), `start_date`, `status` (`draft`|`active`|`completed`), `paluwagan_contract_id`
- `round_members` — `round_id`, `member_id`, `payout_position` (1..N), `joined_at`
- `contributions` — `id`, `round_id`, `member_id`, `cycle_number`, `amount_php`, `stellar_tx_hash`, `status` (`pending`|`confirmed`|`failed`), `created_at`
- `payouts` — `id`, `round_id`, `member_id`, `cycle_number`, `amount_php`, `stellar_tx_hash`, `status`
- `messages` — `id`, `member_id`, `direction` (`in`|`out`), `twilio_sid`, `body`, `created_at`
- `reputation_events` — `id`, `member_id`, `event_type` (`contribution`|`default`|`payout`), `weight`, `stellar_tx_hash`, `created_at`

**RLS:** organizers can only read/write rows where `organizer_id = auth.uid()`. Members are accessed only through the API service role (members never log in to web).

---

## 6. Smart Contracts (Soroban)

### Reputation Trustline

```rust
pub trait Reputation {
    fn record_contribution(member: Address, weight: u32);
    fn record_default(member: Address, weight: u32);
    fn record_payout_received(member: Address);
    fn get_score(member: Address) -> i64;
    fn get_history(member: Address) -> Vec<Event>;
}
```

- Score formula: `+10` per on-time contribution, `-25` per default, `+1` per successful payout received as group member. Decays 1%/30d.
- Emits typed events for every mutation.

### Paluwagan Round

```rust
pub trait Paluwagan {
    fn init_round(organizer: Address, members: Vec<Address>, amount: i128, cycles: u32);
    fn contribute(member: Address, cycle: u32);
    fn distribute_payout(cycle: u32) -> Address;
    fn close_round();
    fn get_state() -> RoundState;
}
```

- Auth: only listed members can `contribute`; only organizer can `init_round` / `close_round`; `distribute_payout` is permissionless after cycle deadline.

**Why two contracts not one:** Reputation is reusable across products (future Late-Night Lend reads from same Reputation contract). Single-responsibility wins long-term.

---

## 7. Backend Services

- **Framework:** FastAPI + Pydantic v2.
- **Layout:** `routers/`, `services/`, `clients/` (stellar, twilio, supabase), `models/`, `workers/`.
- **Worker:** `apscheduler` background loop for: (a) Stellar tx submission queue, (b) cycle-deadline payout trigger.
- **Idempotency:** every `POST` accepts `Idempotency-Key` header, stored in `idempotency_keys` table with response hash, 24h TTL.
- **Retries:** Horizon calls = 3 retries, exp backoff `0.5s, 1s, 2s` + jitter. Twilio sends = same.
- **Rate limits:** SlowAPI middleware, `60/min` per IP on public endpoints.

---

## 8. WhatsApp Channel (Twilio)

**Sandbox first** (instant), production number is post-hackathon.

```
IDLE
  └─ "JOIN <round_code>" → JOINED
       └─ system prompts at cycle start → AWAITING_CONTRIBUTION
            └─ "PAY" → backend creates payment intent → CONTRIBUTED
                 └─ on payout cycle if member is recipient → PAYOUT_NOTIFIED → IDLE
```

**Failure modes:**

- Duplicate webhook: dedupe via `twilio_sid` unique constraint.
- Garbage input: fallback handler with menu of commands.
- Stellar tx fails post-confirm: compensating message + status flip + organizer alert.

**Demo trick:** hidden `/dev/simulate-message` endpoint for organizer to drive demos without QR-pairing.

---

## 9. Frontend (Organizer PWA)

- **Next.js 15 App Router**, Server Components by default.
- **State:** RSC for fetching, `useState`/`useReducer` for local UI, Supabase Realtime hook for live updates. No Redux/Zustand unless pain.
- **Forms:** `react-hook-form` + `zod` (schemas shared via `packages/types`).
- **Data fetching:** native `fetch` with `next: { revalidate }`; mutations via Server Actions.
- **Components:** shadcn/ui themed against `design-tokens.ts`.
- **PWA:** installable, offline shell for `/dashboard`.
- **Pages:** `/`, `/dashboard`, `/rounds/[id]`, `/reputation/[memberId]`.

---

## 10. Design System

**Brand:** DAMAY means "to share in feeling, to extend help." Visual identity = warm, communal, trustworthy — **not** crypto-bro.

Tokens defined in `packages/ui/tokens.ts` (see §10 in the original orchestration doc, source-of-truth tokens are codified there).

**Design rules** (frontend agent must enforce):

- One brand color used for primary actions only. No rainbow.
- Display font (Fraunces) for headlines (`h1`, `h2`), sans (Inter) for everything else.
- Cards use `radius.md` + `shadow.sm`. Modals use `radius.lg` + `shadow.lg`.
- Every interactive element has visible focus ring.
- Every page has empty state + loading skeleton + error boundary. **Three states, always.**
- Filipino warmth in copy: never "Submit" — use "Send", "Save", "Confirm pa." Never "User" — use member/organizer.

**Mandatory:** frontend-engineer reads `/mnt/skills/public/frontend-design/SKILL.md` before writing the first component.

---

## 11. Env Template

See `.env.example` in repo root.

---

## 12. Quality Gates (Definition of Done)

A phase is **Done** only when every box is checked. Orchestrator runs this checklist before unblocking next phase.

**Phase 0 DoD:** schema diagram exists, design tokens committed, repo runs `pnpm dev` without error, `.env.example` complete.
**Phase 1 DoD:** all contract tests pass, contracts deployed to testnet, IDs in `deployments.json`, at least one manual invocation succeeds.
**Phase 2 DoD:** `pytest` green, `/healthz` returns full reachability, OpenAPI doc renders, can `POST /rounds` from curl with auth.
**Phase 3 DoD:** Lighthouse ≥ 90 on perf/a11y/best-practices, three states present on every page, real-time updates visible, PWA installable.
**Phase 4 DoD:** prod URL responds, Twilio webhook hits prod, Stellar tx visible on Stellar Expert from prod-triggered action.
**Phase 5 DoD:** E2E Playwright green, gitleaks clean, contract fuzz clean, replay test green.
**Phase 6 DoD:** README complete, demo script timed under 3:00, pitch one-pager done, seed data loaded.

---

## 13. Observability

- Structured JSON logs (Pino on web, structlog on api), `request_id` correlation across services.
- Sentry on both apps, source maps uploaded on build.
- `/healthz` endpoint with deep checks (DB ping, Stellar RPC ping, Twilio HEAD).
- Stellar txs naturally observable via Stellar Expert — link from every contribution row.

---

## 14. Security Baseline

- All secrets via env, `gitleaks` in CI.
- Supabase RLS on every table, default deny.
- API: JWT auth on all non-webhook endpoints, webhook endpoints verify signature.
- CSP, HSTS, `X-Frame-Options: DENY`, `Referrer-Policy: strict-origin-when-cross-origin`.
- Soroban: auth check on every state-mutating function, no integer overflow, no re-entrancy.
- Member PII (phone numbers) never logged in plaintext.
- Rate limit: 60 req/min/IP on public, 600/min on authenticated.

---

## 15. Demo Script (3:00)

| Time | Beat | What's on screen |
|---|---|---|
| 0:00–0:20 | Hook: "Filipinos save ₱100B/year through paluwagan. Zero of it is on rails." | Hero page, b-roll of group chats |
| 0:20–0:40 | Problem: trust breaks, organizer ghosting, no recourse | Stats slide |
| 0:40–1:00 | Show organizer creating a round in the dashboard | Live create + invite |
| 1:00–1:30 | Show member contributing via WhatsApp | Phone screen mirror → dashboard live update |
| 1:30–2:00 | Open Stellar Expert, show contribution event on chain | stellar.expert tab |
| 2:00–2:30 | Reputation score updating; trustline reuse | Reputation page |
| 2:30–2:50 | Roadmap: Late-Night Lend, real PHP rails, agent layer | One slide |
| 2:50–3:00 | Ask: "Bring this to your barangay." | Repo URL + QR |

**Failure protocols:** WhatsApp dead → `/dev/simulate-message`. Stellar slow → talk reputation while it confirms. App crashes → 30s pre-recorded backup video.

---

## 16. Subagent Definitions

See `.claude/agents/` for full per-agent definitions. Each agent must read this full document before starting work.

---

## 17. Kickoff Command

> **Phase 0 kickoff.** Dispatch `architect`, `ui-designer`, and `devops` (scaffold-only) in parallel. Give each subagent the full CLAUDE.md context + their specific section references. Set 45-minute timer. When all three return, verify Phase 0 DoD, log start of Phase 1, dispatch `soroban-engineer`. Continue per §3.

**Reminders to surface every phase:**

1. **Layman check:** can Ken explain what just shipped to his mom in two sentences?
2. **Trade-off log:** any non-obvious decision goes in `DECISIONS.md`.
3. **Scope discipline:** reject and log work not in this doc.
4. **Time honesty:** if a phase runs >25% over, declare it and invoke §3.6 scope cut.

---

**End of orchestration. Build well, ship on time, demo with confidence.**
