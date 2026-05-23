# Seed Screen — `/reputation/[memberId]` (reputation page)

**Route:** `/reputation/[memberId]`
**Purpose:** Show one member's on-chain reputation score, history, and proof. Linked from any member chip in dashboard / round detail.
**Data:** `members`, `reputation_events`, on-chain `get_score` + `get_history` from Reputation contract. **Source of truth = the contract**, Supabase is cache.

---

## Loaded state

```
┌─────────────────────────────────────────────────────────────────────────┐
│  ← Back                                                Carmela ▾        │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│                                                                         │
│                          ┌─────────────┐                                │
│                          │   ( RC )    │                                │  ← avatar circle, bg.subtle, initials in fg.muted
│                          └─────────────┘                                │
│                                                                         │
│                           Rey Cabrera                                   │  ← Fraunces 4xl, fg.base
│                       Member since Feb 2026                             │  ← Inter sm, fg.muted
│                                                                         │
│                                                                         │
│              ┌───────────────────────────────────────┐                  │
│              │                                       │                  │
│              │              REPUTATION               │                  │  ← label scale.sm, fg.muted, letter-spacing
│              │                                       │                  │
│              │                 142                   │                  │  ← Fraunces 5xl, fg.base
│              │                                       │                  │
│              │           [On-chain ✓]                │                  │  ← accent pill — score itself is verified
│              │      GCXY…K9P2 · tx a1f2…9d4e         │                  │  ← mono xs, fg.subtle
│              │                                       │                  │
│              │      ▲ +10 this week (3 contribs)     │                  │  ← color.success, scale.sm
│              │                                       │                  │
│              └───────────────────────────────────────┘                  │
│                                                                         │
│                                                                         │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │ HOW THIS SCORE WORKS                                             │   │  ← h2 Fraunces 3xl
│  ├─────────────────────────────────────────────────────────────────┤    │
│  │  +10  bawat on-time contribution                                 │   │
│  │  +1   bawat payout natanggap nang tama                           │   │
│  │  −25  kapag nag-default (hindi nakapag-contribute)               │   │
│  │  Decays 1% kada 30 days kapag tahimik.                           │   │
│  │                                                                  │   │
│  │  Naka-record lahat sa Stellar — hindi pwedeng i-edit.            │   │
│  └─────────────────────────────────────────────────────────────────┘    │
│                                                                         │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │ HISTORY                                                          │   │
│  ├─────────────────────────────────────────────────────────────────┤    │
│  │  +10   Contribution    Kapitbahay c3   [On-chain ✓]   Tue 7:48am│    │
│  │        tx: a1f2…9d4e                                              │   │  ← mono, fg.subtle, click → Stellar Expert
│  │  +10   Contribution    Kapitbahay c2   [On-chain ✓]   May 9      │   │
│  │  +1    Payout received Kapitbahay c2   [On-chain ✓]   May 9      │   │
│  │  +10   Contribution    Kapitbahay c1   [On-chain ✓]   May 2      │   │
│  │  +10   Contribution    Tindera c6      [On-chain ✓]   Apr 25     │   │
│  │  −25   Default         Pamilya c4      [On-chain ✓]   Mar 14     │   │  ← amount in color.danger, but pill still accent (it's on-chain)
│  │  +10   Contribution    Pamilya c3      [On-chain ✓]   Mar 7      │   │
│  │  …                                                                │   │
│  └─────────────────────────────────────────────────────────────────┘    │
│                                                                         │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │  Verify lahat sa Stellar Expert  →                               │   │  ← link, accent.base, mono tail
│  └─────────────────────────────────────────────────────────────────┘    │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

### Token map

- Score number "142": `font.display` Fraunces, `scale.5xl`, `color.fg.base`
- Score card: `color.bg.raised`, `radius.lg`, `shadow.md`, border `color.border.base`, generous `space.9` padding
- "[On-chain ✓]" pill below score: `color.accent.base` — this is the page's trust hero
- Contract + tx beneath: `font.mono`, `scale.xs`, `color.fg.subtle`, link → Stellar Expert
- Weekly delta "▲ +10 this week": `color.success`, `scale.sm`
- History row positive weights "+10", "+1": `color.success`
- History row negative weights "−25": `color.danger`
- History row accent pill stays `color.accent.base` for defaults too — the event itself is verified on chain, even though it hurt the score. **Do not color the pill red.** Trust signal ≠ sentiment.
- "Verify lahat sa Stellar Expert →": text link in `color.accent.base`, hover `color.accent.hover`
- No primary brand button on this page. It's read-only. The brand color does not appear here. **This is intentional** — the page's job is to show truth, not to drive action.

---

## Empty state (brand new member, no history)

```
┌─────────────────────────────────────────────────────────────────────────┐
│                                                                         │
│                          ┌─────────────┐                                │
│                          │   ( MA )    │                                │
│                          └─────────────┘                                │
│                                                                         │
│                          Marites Aquino                                 │
│                       Member since today                                │
│                                                                         │
│              ┌───────────────────────────────────────┐                  │
│              │              REPUTATION               │                  │
│              │                 0                     │                  │  ← Fraunces 5xl, fg.subtle (lighter — not yet earned)
│              │                                       │                  │
│              │       Bago ka pa lang.                │                  │  ← Inter base, fg.muted
│              │  Pag-contribute ka, lalakas ang score.│                  │
│              └───────────────────────────────────────┘                  │
│                                                                         │
│                  Walang pa history. Pag-contribute si Marites,          │  ← Inter base, fg.muted
│                  lalabas dito ang lahat — naka-record sa Stellar.       │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## Loading skeleton

```
┌─────────────────────────────────────────────────────────────────────────┐
│                          ┌─────────────┐                                │
│                          │  ▓▓▓▓▓▓▓▓   │                                │
│                          └─────────────┘                                │
│                          ▓▓▓▓▓▓▓▓▓▓▓                                    │
│                          ▓▓▓▓▓▓▓▓                                       │
│                                                                         │
│              ┌───────────────────────────────────────┐                  │
│              │   ▓▓▓▓▓▓▓▓▓                           │                  │
│              │   ▓▓▓▓▓▓▓                             │                  │
│              │   ▓▓▓▓▓▓▓▓▓▓                          │                  │
│              └───────────────────────────────────────┘                  │
│                                                                         │
│  ▓▓▓▓▓▓▓▓▓▓▓▓▓▓                                                        │
│  ▓▓▓ ▓▓▓▓▓▓▓ ▓▓▓▓▓▓▓ ▓▓▓▓▓▓▓                                          │
│  ▓▓▓ ▓▓▓▓▓▓▓ ▓▓▓▓▓▓▓ ▓▓▓▓▓▓▓                                          │
│  ▓▓▓ ▓▓▓▓▓▓▓ ▓▓▓▓▓▓▓ ▓▓▓▓▓▓▓                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## Error state

```
┌─────────────────────────────────────────────────────────────────────────┐
│                                                                         │
│                            ⚠                                            │
│                                                                         │
│                Hindi ma-fetch ang score sa Stellar.                     │  ← Fraunces 3xl
│                                                                         │
│           Cached score: 142 (last updated 4 hours ago).                 │  ← Inter base, fg.muted
│           Subukan ulit para sa latest on-chain data.                    │
│                                                                         │
│                          [Try again]                                    │  ← secondary outlined
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

We still show the cached score so the page is never useless. The error tells the truth: this is stale.

---

## Real-time behavior

- On mount: fetch score from contract (`get_score`) AND from Supabase cache. Display contract value as source of truth; if they disagree, prefer contract and emit a structured log warning (`reputation.cache_drift`).
- Subscribe to `reputation_events:member_id=eq.{id}` — new event prepends to history, score increments with `motion.slow` count-up.

---

## Filipino voice copy bank

- Empty score: *"Bago ka pa lang. Pag-contribute ka, lalakas ang score mo."*
- Empty history: *"Walang pa history. Pag-contribute si {name}, lalabas dito ang lahat — naka-record sa Stellar."*
- How-it-works header: *"How this score works"* (label) / body in Taglish.
- Stellar verify link: *"Verify lahat sa Stellar Expert →"*
- Weekly delta positive: *"▲ +10 this week (3 contribs)"*
- Default event copy: *"Default"* (single word, neutral — not "Failed" / "Missed")

---

## Trust-design notes (read before building)

1. The score is the hero. Nothing else on this page competes for visual weight.
2. The on-chain badge directly under the score is the single most important element on the page for hackathon judging. Make it land.
3. No brand color anywhere on this page. Brand = action; this page is truth.
4. Negative events are shown plainly. Hiding defaults breaks trust. Color the weight red, leave the verification pill teal.
5. The cached-fallback error state matters — judges will ask "what if Stellar is slow?" The answer is on screen.
