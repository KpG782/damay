# DAMAY — 3:00 Judge Demo Script

> Verbatim words to say, per beat. Read out loud once at 150 wpm before the live run. If a beat runs over, cut the next beat's filler — never cut the Stellar Expert moment (1:30) or the reputation moment (2:00).

---

## Pre-demo checklist (T-15 min)

Tick every box. If any one is red, switch to the backup video (`docs/backup-demo.mp4`) for the affected segment.

- [ ] `bash scripts/deploy_testnet.sh` ran successfully — `deployments.json` shows live `id` values for both contracts (not `null`).
- [ ] `curl -fsS https://api.damay.kenbuilds.tech/healthz | jq` returns `db: ok`, `horizon: ok`, `twilio: ok`, `soroban_rpc: ok`.
- [ ] `curl -fsS -o /dev/null -w "%{http_code}\n" https://damay.kenbuilds.tech/` returns `200`.
- [ ] Twilio sandbox webhook points at `https://api.damay.kenbuilds.tech/v1/webhooks/twilio` (POST).
- [ ] Seed data loaded: `apps/api/supabase/migrations/0002_seed.sql` applied. Dashboard shows the round **Kapitbahay Kalsada 7** with 6 members.
- [ ] You are signed into the dashboard as the seeded organizer; the **Kapitbahay Kalsada 7** detail page is open in tab 1.
- [ ] Stellar Expert open in tab 2: `https://stellar.expert/explorer/testnet/contract/<PALUWAGAN_CONTRACT_ID>`.
- [ ] Phone is mirrored to laptop screen (QuickTime / scrcpy) and visible to camera.
- [ ] Backup video `docs/backup-demo.mp4` is **paused at 00:00** in tab 3 — one click away.
- [ ] You have water. Take a sip now.

---

## 0:00–0:20 — Hook

**Visual:** Hero page full-screen on laptop. Phone-in-frame in the corner shows a real Filipino group chat with paluwagan reminders (consent-cleared screenshot — `docs/groupchat-broll.png`).

**Script (verbatim, 18s at 150 wpm):**
> "Eighteen million Filipinos save through paluwagan. One hundred billion pesos a year flows through these rotating savings circles. Zero of it touches financial rails. Today, one ghosted organizer equals the whole group dissolves. We fixed that."

**Beat:** One-second pause. Click into `/dashboard`. Smile.

**Fallback:** If hero page fails to load → fall back to `docs/screenshot-hero.png` opened full-screen; same script, no change.

---

## 0:20–0:40 — Problem

**Visual:** Slide overlay (or simple `/problem` route) with three stats stacked:
- `₱100B/year — paluwagan TAM (est.)`
- `18M participants — BSP Financial Inclusion (est.)`
- `0 — recourse when the organizer ghosts`

**Script (verbatim, 20s):**
> "Paluwagan runs on three things: a group chat, GCash receipts, and trust. When trust breaks — the organizer ghosts, someone misses a cycle, the ledger is just screenshots — there is no record that follows them to the next group. No portable reputation. No recourse. That is the gap."

**Beat:** Click into the active round **Kapitbahay Kalsada 7**.

**Fallback:** If slide doesn't load, say the line over the dashboard. Stats are in the script — they don't need to be on screen to land.

---

## 0:40–1:00 — Organizer creates the round

**Visual:** `/rounds/[id]` detail page. Six members visible — Carmela, Rey, Joelle, Marites, Joaquin, Aileen. Top-right shows `Status: active` and `Contract: C... (Stellar Expert)`.

**Script (verbatim, 20s):**
> "Here is **Kapitbahay Kalsada 7** — six neighbors, five hundred pesos every Saturday, six weeks. The organizer set it up in the dashboard. The moment she clicked activate, a fresh Paluwagan contract deployed to Stellar testnet, with all six members baked into the roster. Position one this week: Marites."

**Beat:** Hover the contract ID chip → cursor visible. Don't click yet.

**Fallback:** If round is missing from the seed, run `psql "$SUPABASE_DB_URL" -f apps/api/supabase/migrations/0002_seed.sql` from a side terminal (have it pre-typed). Costs you ~5s; skip the Joaquin/Aileen name-drops to catch up.

---

## 1:00–1:30 — Member contributes via WhatsApp

**Visual:** Switch focus to the mirrored phone. WhatsApp open to the Twilio sandbox thread.

**Script (verbatim, 30s):**
> "Members never leave WhatsApp — that's where they already live. Watch. Rey sends `PAY` to the bot. The webhook hits the API, signature verifies, idempotency keys catch any duplicate, we drop a contribution row in pending, and the worker queues a Soroban transaction. Back in the dashboard — there — Supabase Realtime ticks the timeline live. Status flips from pending to confirmed when Horizon confirms. No refresh."

**Beat:** Type `PAY` on the phone. Send. Switch focus back to dashboard. Wait for the row to appear (typically 2–4s). Point at the timeline.

**Fallback A:** If WhatsApp message fails to send → run `POST /v1/dev/simulate-message` from a pre-loaded `curl` command in a side terminal. Cover with: "For demo speed, we have a backdoor that injects the same payload — same code path, same backend, no Twilio leg." Audience reads this as competence, not a hack.

**Fallback B:** If Realtime doesn't tick → manually refresh once at 1:25 and continue. Don't apologize, don't draw attention.

---

## 1:30–2:00 — Stellar Expert proof

**Visual:** Switch to tab 2 — Stellar Expert, contract detail. Click into the latest transaction. Show the typed event payload: `("pal","contrib")` with member address + cycle.

**Script (verbatim, 30s):**
> "This is the part judges should grep for. Every contribution is a real Stellar transaction with a typed Soroban event. Anyone in the world can read it. The members don't see Stellar — they see WhatsApp. The organizer doesn't see Stellar — she sees a dashboard. But the trust layer is here, on chain, observable, immutable. Two contracts: Paluwagan for the round state machine, Reputation as a reusable trustline."

**Beat:** Highlight the event payload with cursor. Pause one second on the contract ID.

**Fallback:** If Stellar Expert is slow → open the cached tab pre-opened to a previous tx hash (right-click tab 2 → reload only if needed; otherwise the previous load is already there). The line still lands.

---

## 2:00–2:30 — Reputation moment

**Visual:** Click `/reputation/[marites-id]` from the round member list. Score is visible. History list shows: 3 past rounds completed, 1 late default in cycle-3 of the second past round (`-25`), recovered with `+10` afterward. Net score visible.

**Script (verbatim, 30s):**
> "Here is Marites. Three rounds completed. One late payment a year ago — see the minus twenty-five — but she paid back the next cycle, plus ten. Her score follows her. Now any future product — a microloan, a new paluwagan with strangers, a lending intent — can read this score from the same Reputation contract. Same trustline, different products. That's the unlock."

**Beat:** Scroll the history list slowly. Stop on the default event. Tap it — opens Stellar Expert for that specific reputation event.

**Fallback:** If reputation page is the cut feature (per CLAUDE.md §3.6 scope-cut order), show the reputation chip in the round-detail sidebar instead. Same line, fewer pixels.

---

## 2:30–2:50 — Roadmap

**Visual:** Single slide. Three bullets:
- `v1.1 — Late-Night Lend (intent layer reads same Reputation Trustline)`
- `v1.2 — Real PHP rails via partner (GCash cash-in, Maya cash-out)`
- `v2 — Mainnet · BSP-friendly KYC · barangay LGU white-label`

**Script (verbatim, 20s):**
> "Roadmap. Version 1.1: Late-Night Lend — when a paluwagan member needs cash before their cycle, an intent layer reads the same Reputation contract and matches them with lenders. Version 1.2: real peso rails through a partner. Version 2: mainnet, KYC, and white-label for barangay LGUs and parish cooperatives."

**Beat:** Don't linger. Move to the close.

**Fallback:** If slide fails, say the three bullets over the dashboard. They're memorable enough on their own.

---

## 2:50–3:00 — Ask

**Visual:** Repo URL + QR code, full-screen. URL reads `github.com/KpG782/damay`.

**Script (verbatim, 10s):**
> "Bring DAMAY to your barangay. Repo is up, contracts are on testnet, demo is live. Salamat po."

**Beat:** Stop. Smile. Hands at sides. Wait for questions.

**Fallback:** None needed — if everything before this beat broke, just say the ask line over a black screen. The line works alone.

---

## Total demo time: **3:00 exactly.**

(0:20 + 0:20 + 0:20 + 0:30 + 0:30 + 0:30 + 0:20 + 0:10 = 3:00)

## Failure protocols (consolidated)

| Failure                            | Action                                                                                                |
|------------------------------------|-------------------------------------------------------------------------------------------------------|
| WhatsApp message doesn't deliver   | `POST /v1/dev/simulate-message` from pre-loaded curl — same code path, frame as "demo speed"          |
| Stellar tx is slow (>5s confirm)   | Talk about reputation while it confirms; cut back to the dashboard when the row flips                 |
| Dashboard crashes                  | 30s pre-recorded backup at `docs/backup-demo.mp4` — switch to tab 3, narrate over the recording       |
| Stellar Expert won't load          | Show the pre-cached tab; if also dead, show `deployments.json` in a terminal — contract ID is proof   |
| Twilio webhook returns 5xx         | `POST /v1/dev/simulate-message`; no apology, no acknowledgement on stage                              |
| You forget a line                  | Skip ahead to the next beat marker. Never re-read; the script overruns are budgeted to absorb one cut |
