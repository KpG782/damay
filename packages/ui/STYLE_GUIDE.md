# DAMAY Style Guide

One page. If a rule is not here, ask before inventing it.

DAMAY means "to share in feeling, to extend help." Visual language = warm, communal, trustworthy. We are a barangay tita's ledger, not a trading floor.

---

## 1. Color — brand vs accent (the most important rule)

| Token | Use for | Never use for |
|---|---|---|
| `color.brand.base` (#C2410C terracotta) | Primary CTAs only — "Create round," "Send pa," "Confirm pa" | Links, charts, success states, badges that are not the page's main action |
| `color.accent.base` (#0F766E teal) | Verified / on-chain signals only — confirmation badges, "View on Stellar Expert" link, on-chain proof rows | General secondary actions, hovers, UI chrome |
| `color.success` | Confirmed contributions, positive reputation delta | CTAs |
| `color.warning` | Pending tx, awaiting member action | Errors |
| `color.danger`  | Defaults, destructive actions, error toasts | Anything optimistic |

**One brand color per screen.** If two things both look "primary," one of them isn't.

---

## 2. Type hierarchy

- `h1` — `font.display` (Fraunces), `scale.4xl`, weight 600. Page titles.
- `h2` — `font.display` (Fraunces), `scale.3xl`, weight 600. Section headers.
- `h3` — `font.sans` (Inter), `scale.2xl`, weight 600. Card titles.
- Body — `font.sans` (Inter), `scale.base`, weight 400, line-height 1.6.
- Label / caption — `font.sans`, `scale.sm`, weight 500, `color.fg.muted`.
- Tx hashes, contract IDs, amounts in raw stroops — `font.mono`, `scale.xs`.

Display font (Fraunces) is reserved for `h1`/`h2`. Everything else is Inter. No exceptions.

---

## 3. Button hierarchy

| Variant | Background | Text | Border | Use when |
|---|---|---|---|---|
| **Primary** | `color.brand.base` (hover: `brand.hover`) | `bg.raised` | none | One per view. The single most important action. |
| **Secondary** | transparent | `color.fg.base` | 1px `color.fg.base` | Supporting actions ("Cancel," "Invite member") |
| **Ghost** | transparent | `color.fg.muted` | none (hover: `bg.subtle`) | Tertiary, in-row, icon buttons |
| **Destructive** | transparent | `color.danger` | 1px `color.danger` | "Remove member," "Close round" |

All buttons: `radius.base`, padding `space.3` vertical / `space.5` horizontal, `motion.base` transition.

---

## 4. Spacing rhythm

Everything in multiples of 4 (we use `space.1` … `space.12`). Common patterns:

- Inline gap inside a row: `space.2` (8px)
- Form field stack: `space.4` (16px)
- Card inner padding: `space.6` (24px)
- Section vertical rhythm: `space.9` (48px)
- Page gutter (desktop): `space.10` (64px); mobile: `space.5` (20px)

No magic numbers. If you need 13px, you need 12px.

---

## 5. Three-state discipline (mandatory on every page)

Every page MUST ship all three:

1. **Loading skeleton** — neutral `bg.subtle` blocks, shimmer with `motion.slow`. No spinners as the primary loading state.
2. **Empty state** — illustration or icon + Fraunces headline + plain-language subhead + one primary CTA. See copy patterns below.
3. **Error boundary** — `color.danger` icon, friendly headline ("Naku, may problema."), retry CTA, link to support.

If a page is missing one of these three, the page is not done.

---

## 6. Empty-state copy patterns (Filipino warmth)

Pattern: **acknowledgement + light nudge + clear next step**. Light Taglish is welcome; never forced.

- No rounds yet: *"Wala pang round. Gusto mong mag-create ng una?"* → CTA: **Create round**
- No contributions yet in a round: *"Walang pa naka-contribute. Hintayin natin sina Carmela."*
- No reputation history: *"Bago ka pa lang. Pag-contribute ka, lalakas ang score mo."*
- No members invited: *"Wala pang miyembro. I-invite na natin sila."* → CTA: **Send invite**

**Voice rules (hard):**

- "Send pa," "Done na," "Confirm pa" — never "Submit" / "Complete."
- "Member" / "organizer" — never "user."
- No exclamation points in error states. We are calm with people's money.
- Names in seed/sample copy are Filipino: Carmela, Rey, Joelle, Marites, Joselito, Aning.

---

## 7. Focus ring

Every interactive element:

```
outline: 2px solid color.brand.base;
outline-offset: 2px;
border-radius: inherit;
```

Visible. Always. No `outline: none` without a replacement.

---

## 8. On-chain badge (trust signal)

The single most important component for judging.

- Shape: pill, `radius.full`.
- Background: `color.accent.base` (deep teal).
- Text: `bg.raised` white, `scale.xs`, weight 600, content: **"On-chain"** or **"Verified"**.
- Leading checkmark icon (12px stroke).
- Tooltip on hover: monospace tx hash (truncated `abc1…d4f9`) + "Click to view on Stellar Expert."
- Click → opens `stellar.expert/explorer/testnet/tx/{hash}` in new tab.

Appears next to: confirmed contributions, payouts, reputation events, contract IDs in the round header. **Never** appears on pending or off-chain rows. Pending uses `color.warning` + "Pending" text pill (no checkmark).

---

## 9. Cards, modals, surfaces

- **Card:** `bg.raised`, `radius.md`, `shadow.sm`, `border.subtle` 1px. Padding `space.6`.
- **Modal:** `bg.raised`, `radius.lg`, `shadow.lg`. Backdrop: `rgba(26,22,20,0.4)`.
- **Inline row:** `bg.raised` on `bg.base` page; hover → `bg.subtle`.

---

## 10. Motion

- Hover, focus, small state changes → `motion.fast` (120ms).
- Most transitions → `motion.base` (200ms).
- Modal open, page transition → `motion.slow` (320ms).
- Curve always `motion.ease` — no linear, no bounce. Trust feels calm.
