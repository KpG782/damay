# Seed Screen — `/dashboard` (organizer home)

**Route:** `/dashboard` (auth required, organizer only)
**Purpose:** Organizer sees all their rounds at a glance, jumps into one, or creates a new round.
**Data:** `rounds` (filtered by `organizer_id`), aggregated counts from `contributions` + `round_members`.

---

## Loaded state (primary)

```
┌─────────────────────────────────────────────────────────────────────────┐
│  DAMAY                                              Carmela ▾   [Sign out]│  ← top bar: bg.raised, border-bottom border.subtle
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│   Kumusta, Carmela.                                  [+ Create round]   │  ← h1 Fraunces 4xl; CTA = brand.base (PRIMARY, one per view)
│   3 rounds active.                                                      │  ← scale.base, fg.muted
│                                                                         │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │ ACTIVE ROUNDS                                                    │   │  ← h2 Fraunces 3xl section header
│  └─────────────────────────────────────────────────────────────────┘    │
│                                                                         │
│  ┌───────────────────────────────────┐  ┌───────────────────────────┐   │
│  │ Kapitbahay Savings · Cycle 3/6    │  │ Pamilya Pot · Cycle 1/8   │   │  ← card.h3 Inter 2xl
│  │ ─────────────────────────────────  │  │ ──────────────────────── │   │
│  │ ₱500/week · 6 members              │  │ ₱1,000/week · 8 members  │   │
│  │                                    │  │                          │   │
│  │ ●●●○○○  4 of 6 contributed         │  │ ○○○○○○○○ 0 of 8           │   │  ← dots: success / bg.subtle
│  │                                    │  │                          │   │
│  │ Next payout:  Rey  · in 2 days     │  │ Starts: Mon, May 27       │   │
│  │ [On-chain ✓]                       │  │ [On-chain ✓]              │   │  ← accent.base pill, tx-hash tooltip
│  │                                    │  │                          │   │
│  │ [Open round →]      (ghost button) │  │ [Open round →]            │   │
│  └───────────────────────────────────┘  └───────────────────────────┘   │
│                                                                         │
│  ┌───────────────────────────────────┐                                  │
│  │ Tindera Circle · Cycle 6/6        │                                  │
│  │ ─────────────────────────────────  │                                  │
│  │ ₱300/week · 6 members              │                                  │
│  │ ●●●●●●  Done na — closing soon     │  ← success copy, Filipino warmth │
│  │ [On-chain ✓]                       │                                  │
│  │ [Open round →]                     │                                  │
│  └───────────────────────────────────┘                                  │
│                                                                         │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │ RECENT ACTIVITY                                                  │   │
│  ├─────────────────────────────────────────────────────────────────┤    │
│  │  •  Rey nag-contribute ₱500 to Kapitbahay   [On-chain ✓]  2m ago│    │  ← row uses accent badge for confirmed
│  │  •  Joelle nag-contribute ₱500 to Kapitbahay [Pending ⧗] 5m ago │    │  ← warning pill — NOT accent
│  │  •  Marites joined Pamilya Pot              [On-chain ✓] 1h ago │    │
│  └─────────────────────────────────────────────────────────────────┘    │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

### Token map

- Page bg: `color.bg.base` (#FAF7F2)
- Top bar + cards: `color.bg.raised`, `radius.md`, `shadow.sm`, border `color.border.subtle`
- "+ Create round" CTA: filled `color.brand.base`, hover `color.brand.hover` — **the only brand color on the page**
- "Open round →": ghost button, `color.fg.muted` text, hover bg `color.bg.subtle`
- "[On-chain ✓]" pill: `color.accent.base` bg, white text, `radius.full`, tooltip shows tx hash mono
- "[Pending ⧗]" pill: `color.warning` bg at 15% opacity, `color.warning` text — no checkmark
- Progress dots: `color.success` filled / `color.bg.subtle` empty
- Greeting "Kumusta, Carmela.": `font.display` Fraunces, `scale.4xl`

---

## Empty state (no rounds)

```
┌─────────────────────────────────────────────────────────────────────────┐
│                                                                         │
│                          ◯  (warm illustration)                         │
│                                                                         │
│                   Wala pang round. Mag-start na?                        │  ← Fraunces 3xl, fg.base
│                                                                         │
│         Mag-create ng paluwagan circle para sa pamilya o barangay.      │  ← Inter base, fg.muted
│         Five minutes lang.                                              │
│                                                                         │
│                          [+ Create round]                               │  ← brand primary CTA
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## Loading skeleton

```
┌─────────────────────────────────────────────────────────────────────────┐
│  ▓▓▓▓▓▓▓▓                                            ▓▓▓▓     ▓▓▓▓     │
├─────────────────────────────────────────────────────────────────────────┤
│  ▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓                                                       │
│  ▓▓▓▓▓▓▓▓                                                              │
│                                                                         │
│  ┌──────────────────────┐  ┌──────────────────────┐                    │
│  │ ▓▓▓▓▓▓▓▓▓▓▓▓         │  │ ▓▓▓▓▓▓▓▓▓▓▓▓         │                    │
│  │ ▓▓▓▓▓▓▓▓ ▓▓▓▓        │  │ ▓▓▓▓▓▓▓▓ ▓▓▓▓        │                    │
│  │ ▓▓▓▓▓ ▓▓▓▓▓ ▓▓▓▓▓    │  │ ▓▓▓▓▓ ▓▓▓▓▓ ▓▓▓▓▓    │                    │
│  │ ▓▓▓▓▓▓▓▓▓▓           │  │ ▓▓▓▓▓▓▓▓▓▓           │                    │
│  └──────────────────────┘  └──────────────────────┘                    │
└─────────────────────────────────────────────────────────────────────────┘
```

Skeleton blocks: `color.bg.subtle`, shimmer animation 1.2s, `motion.ease`.

---

## Error state

```
┌─────────────────────────────────────────────────────────────────────────┐
│                                                                         │
│                            ⚠  (danger icon)                             │
│                                                                         │
│                       Naku, may problema sa connection.                 │  ← Fraunces 3xl
│                                                                         │
│              Hindi ma-load ang rounds mo. Subukan natin ulit.           │  ← Inter base, fg.muted
│                                                                         │
│                           [Try again]                                   │  ← secondary outlined button (NOT brand — not the page's job)
│                                                                         │
│                   May tanong? Mag-message sa support.                   │  ← Inter sm, fg.subtle
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

Icon `color.danger`. Headline `color.fg.base`. No exclamation points.

---

## Real-time behavior

- Supabase Realtime channel: `contributions:organizer_id=eq.{me}`.
- New row → prepend to "Recent activity" list with `motion.slow` slide-in.
- Status change `pending → confirmed` → pill animates from warning to accent over `motion.base`.

---

## Filipino voice copy bank for this screen

- Greeting: *"Kumusta, {first_name}."* (never "Welcome back, user")
- Active rounds heading: *"Active rounds"* (English is fine here — it's a label, not a sentence)
- Completed: *"Done na — closing soon"* (never "Completed")
- Empty: *"Wala pang round. Mag-start na?"*
- Error: *"Naku, may problema sa connection."*
- Retry: *"Subukan natin ulit"* / button label *"Try again"*
