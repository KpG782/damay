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
