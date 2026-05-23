# DAMAY — Paluwagan by Damay

*Trustless rails for the Philippines' ₱100B/year informal savings circles. Stellar Philippines Hackathon, PDAX, 2026.*

## Problem

Paluwagan is how an estimated **18 million Filipinos** save outside the banking system (BSP Financial Inclusion Survey, est.). Six neighbors put in ₱500/week; every week someone different takes the pot. Roughly **₱100B (est.)** cycles through these rotating circles every year. It runs on a group chat, GCash receipts, and trust. When someone ghosts — and in non-kin circles default rates are commonly cited as materially worse than kin-based ones — the group dissolves, the ledger is just screenshots, and the defaulter walks into the next paluwagan with a clean slate. No record. No recourse. No portable reputation.

## Solution

**DAMAY is an organizer dashboard plus a member WhatsApp bot that puts every contribution and payout on Stellar Soroban, with a reusable Reputation Trustline contract that any future product can read.** Same group-chat UX members already know, now with cryptographic receipts on Stellar Expert and a trust score that follows them.

![Dashboard — live round timeline with on-chain receipts](docs/screenshot-dashboard.png)

## Technical depth

- **2 Soroban contracts** — `reputation` (portable score, `+10/-25/+1`, 1%-per-30-day decay, bounded 100-entry history) and `paluwagan` (per-round state machine: init / contribute / distribute_payout / close).
- **Typed Soroban events** on every mutation — observable on Stellar Expert, linked from every dashboard row.
- **`require_auth` on every state-mutating function**; arithmetic uniformly `saturating_*`; no `unwrap` on user input; no cross-contract calls from mutating paths (zero re-entry surface).
- **Queued chain writes** — HTTP webhook never blocks on Stellar; `stellar_jobs` table + worker, idempotency keyed on `(job_type, target_id, cycle)`, exp backoff `0.5/1/2s`, dead-letter after 3.
- **127 tests green** — 50 contract (incl. 1000-iter fuzz, no panics) + 63 backend (pytest) + 14 E2E (Playwright).
- **Security review** — `PASS_WITH_NOTES`, **0 High** findings, gitleaks clean, RLS-by-default on every Supabase table, Twilio HMAC verified.
- **Frontend** — Next.js 15 App Router, Supabase Realtime live timeline, three states (loading skeleton + empty + error) on every page, PWA installable, Lighthouse target ≥ 90 on perf / a11y / best-practices.

## Market

Paluwagan TAM in the Philippines: **~₱100B/year, ~18M participants (est.)**. Why now: BSP's Digital Payments Transformation roadmap targets 50%+ of retail payments digital by 2026; GCash + Maya combined penetration is already past **50% of adult Filipinos**. The on-ramps exist. The trust layer doesn't.

## Roadmap

- **v1.1** — Late-Night Lend intent layer reading the same Reputation contract; partner-backed PHP rails (GCash cash-in, Maya cash-out).
- **v1.2** — Multi-currency rounds (USDC for OFW remittance circles), agent layer for third-party reputation reads.
- **v2** — Mainnet, BSP-friendly KYC tier, white-label for barangay LGUs and parish credit cooperatives.

## Team

**Ken Patrick Garcia** — full-stack AI engineer, Manila. Shipped solo via Claude Code subagent orchestration (10 specialized agents, one `CLAUDE.md` playbook). [kenbuilds.tech](https://kenbuilds.tech)

## Ask

Bring DAMAY to your barangay. Repo: **github.com/KpG782/damay**. Testnet contracts live in `deployments.json`.
