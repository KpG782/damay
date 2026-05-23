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
