# Seed Screen — `/rounds/[id]` (round detail)

**Route:** `/rounds/[id]`
**Purpose:** Organizer monitors one round: members, contribution timeline, payout schedule, on-chain proof.
**Data:** `rounds`, `round_members` JOIN `members`, `contributions` (realtime), `payouts`, `paluwagan_contract_id`.

---

## Loaded state

```
┌─────────────────────────────────────────────────────────────────────────┐
│  ← Back to dashboard                                  Carmela ▾         │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│   Kapitbahay Savings                                  [+ Invite member] │  ← h1 Fraunces 4xl;  primary CTA = brand.base
│   Cycle 3 of 6 · ₱500/week · 6 members                                  │  ← Inter base, fg.muted
│   Contract: GCXY…K9P2  [On-chain ✓]                                     │  ← mono font for contract id, accent pill links Stellar Expert
│                                                                         │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │ THIS CYCLE  (closes Fri, May 30)                                 │   │  ← h2 Fraunces 3xl
│  ├─────────────────────────────────────────────────────────────────┤    │
│  │                                                                  │   │
│  │  ●  Carmela    ₱500   Done na    [On-chain ✓]  Mon 9:14am        │   │  ← success text + accent pill
│  │  ●  Rey        ₱500   Done na    [On-chain ✓]  Mon 11:02am       │   │
│  │  ●  Joelle     ₱500   Done na    [On-chain ✓]  Tue 7:48am        │   │
│  │  ●  Marites    ₱500   Pending    [Pending ⧗]   sent reminder     │   │  ← warning pill, no checkmark
│  │  ○  Joselito   ₱500   Hindi pa   [— Send pa]   reminder Joselito │   │  ← ghost CTA per row
│  │  ○  Aning      ₱500   Hindi pa   [— Send pa]                     │   │
│  │                                                                  │   │
│  │  Pot this cycle: ₱2,000 collected of ₱3,000                      │   │  ← fg.muted, summary line
│  │  Next payout: Rey (position 3 of 6)                              │   │
│  │                                                                  │   │
│  │  [Trigger payout]   (disabled until 6 of 6 confirmed)           │   │  ← secondary outlined while disabled
│  └─────────────────────────────────────────────────────────────────┘    │
│                                                                         │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │ PAYOUT SCHEDULE                                                  │   │
│  ├─────────────────────────────────────────────────────────────────┤    │
│  │  #1  Carmela   ₱3,000   May 9   Done na    [On-chain ✓]          │   │
│  │  #2  Aning     ₱3,000   May 16  Done na    [On-chain ✓]          │   │
│  │  #3  Rey       ₱3,000   May 30  Up next                          │   │  ← bg.subtle row highlight
│  │  #4  Joelle    ₱3,000   Jun 6                                    │   │
│  │  #5  Marites   ₱3,000   Jun 13                                   │   │
│  │  #6  Joselito  ₱3,000   Jun 20                                   │   │
│  └─────────────────────────────────────────────────────────────────┘    │
│                                                                         │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │ ACTIVITY TIMELINE                                                │   │
│  ├─────────────────────────────────────────────────────────────────┤    │
│  │  Tue 7:48am  Joelle contributed ₱500          [On-chain ✓]       │   │
│  │              tx: a1f2…9d4e                                        │   │  ← mono, fg.subtle, click → Stellar Expert
│  │  Mon 11:02am Rey contributed ₱500              [On-chain ✓]      │   │
│  │  Mon 9:14am  Carmela contributed ₱500          [On-chain ✓]      │   │
│  │  Sun 8:00pm  Cycle 3 opened                    [On-chain ✓]      │   │
│  └─────────────────────────────────────────────────────────────────┘    │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

### Token map

- Page bg `color.bg.base`; cards `color.bg.raised`, `radius.md`, `shadow.sm`
- Member row dot: `color.success` (confirmed) / `color.warning` (pending) / `color.bg.subtle` ring (not yet)
- "[+ Invite member]" — primary brand CTA, top-right
- "Trigger payout" — secondary outlined (becomes primary brand only when enabled)
- "[Send pa]" per-row — ghost button, scale.sm, `color.fg.muted`
- "[On-chain ✓]" pill — `color.accent.base`, tooltip = tx hash mono, click opens Stellar Expert
- "[Pending ⧗]" pill — `color.warning` 15% bg + warning text
- Contract id "GCXY…K9P2" — `font.mono`, `scale.xs`, fg.muted
- Current cycle's "Up next" row in payout schedule: `color.bg.subtle` background

---

## Empty state (round just created, no contributions yet)

```
┌─────────────────────────────────────────────────────────────────────────┐
│                                                                         │
│                           ◯ (illustration)                              │
│                                                                         │
│                Walang pa naka-contribute sa cycle na ito.               │  ← Fraunces 3xl
│                                                                         │
│         Naka-notify na sina Carmela, Rey, at iba pa sa WhatsApp.        │  ← Inter base, fg.muted
│         Lalabas dito pag may nag-send na.                               │
│                                                                         │
│                       [Send reminder to all]                            │  ← secondary outlined
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## Loading skeleton

```
┌─────────────────────────────────────────────────────────────────────────┐
│  ▓▓▓▓▓▓▓▓                                                              │
│  ▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓                                                     │
│  ▓▓▓▓▓▓▓▓▓▓▓▓▓                                                         │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │ ▓▓▓▓▓▓▓▓▓▓▓                                                      │   │
│  │ ● ▓▓▓▓▓▓▓▓   ▓▓▓▓  ▓▓▓▓▓▓▓▓  ▓▓▓▓▓▓▓                            │   │
│  │ ● ▓▓▓▓▓▓▓▓   ▓▓▓▓  ▓▓▓▓▓▓▓▓  ▓▓▓▓▓▓▓                            │   │
│  │ ● ▓▓▓▓▓▓▓▓   ▓▓▓▓  ▓▓▓▓▓▓▓▓  ▓▓▓▓▓▓▓                            │   │
│  └─────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## Error state

```
┌─────────────────────────────────────────────────────────────────────────┐
│                            ⚠                                            │
│                Naku, hindi ma-load ang round na ito.                    │  ← Fraunces 3xl
│              Baka may connection issue sa Stellar testnet.              │  ← Inter base, fg.muted
│                            [Try again]                                  │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## Real-time behavior

- Supabase Realtime channel: `contributions:round_id=eq.{id}`.
- New contribution → row in "This cycle" flips from "Hindi pa" → "Done na", dot turns success, "[Send pa]" replaced with "[On-chain ✓]" (animating from warning pending → accent confirmed over `motion.base`).
- Activity timeline: new event prepended with slide-in.
- When 6 of 6 confirmed: "[Trigger payout]" enables, switches from secondary outlined to **primary brand** (this is the one moment the bottom button becomes brand-colored).

---

## Filipino voice copy bank

- Status confirmed: *"Done na"* (never "Completed" / "Paid")
- Status pending: *"Pending"* / *"naka-send na, hinihintay confirm"*
- Status not yet contributed: *"Hindi pa"* (never "Missing" / "Late")
- Row CTA: *"Send pa"* (never "Pay" / "Submit")
- Reminder action: *"sent reminder"* / *"reminder Joselito"*
- Empty cycle: *"Walang pa naka-contribute sa cycle na ito."*
- Closing soon: *"Done na — closing soon"*
