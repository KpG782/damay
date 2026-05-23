/**
 * DAMAY Design Tokens — single source of visual truth.
 *
 * Brand: warm, communal, trustworthy. NOT crypto-bro.
 * - `brand` (terracotta) = primary CTAs only.
 * - `accent` (deep teal) = verified / on-chain signals only.
 *
 * Locked per CLAUDE.md §10. Do not edit values without a DECISIONS.md entry.
 */

export const color = {
  bg: {
    base: "#FAF7F2",     // app background — warm off-white (abaca paper)
    subtle: "#F2EDE4",   // section background, hover surfaces
    raised: "#FFFFFF",   // cards, modals, raised surfaces
  },
  fg: {
    base: "#1A1614",     // primary text — warm near-black
    muted: "#5C544E",    // secondary text, labels
    subtle: "#8A8078",   // tertiary text, placeholder, captions
  },
  brand: {
    base: "#C2410C",     // terracotta — primary CTAs ONLY
    hover: "#9A330A",    // primary CTA hover/active
    subtle: "#FED7AA",   // brand-tinted backgrounds, badges (sparingly)
  },
  accent: {
    base: "#0F766E",     // deep teal — verified / on-chain ONLY
    hover: "#0D5F58",    // accent hover state
  },
  success: "#15803D",    // confirmed contributions, positive deltas
  warning: "#B45309",    // pending, awaiting, late-but-recoverable
  danger:  "#B91C1C",    // defaults, errors, destructive actions
  border: {
    base: "#E5DCC8",     // default borders, dividers
    subtle: "#EFE8D8",   // hairlines, subtle separators
  },
} as const;

export const font = {
  sans: "Inter, system-ui, -apple-system, Segoe UI, Roboto, sans-serif",
  display: "Fraunces, Georgia, 'Times New Roman', serif",
  mono: "'JetBrains Mono', 'SF Mono', Menlo, Consolas, monospace",
} as const;

export const scale = {
  xs:   "0.75rem",   // 12px — captions, badges, tx-hash
  sm:   "0.875rem",  // 14px — secondary body, labels
  base: "1rem",      // 16px — body
  lg:   "1.125rem",  // 18px — emphasized body, card titles
  xl:   "1.25rem",   // 20px — section headers
  "2xl":"1.5rem",    // 24px — h3
  "3xl":"1.875rem",  // 30px — h2 (Fraunces)
  "4xl":"2.25rem",   // 36px — h1 (Fraunces)
  "5xl":"3rem",      // 48px — hero display (Fraunces)
} as const;

export const space = {
  1:  "4px",
  2:  "8px",
  3:  "12px",
  4:  "16px",
  5:  "20px",
  6:  "24px",
  7:  "32px",
  8:  "40px",
  9:  "48px",
  10: "64px",
  11: "80px",
  12: "96px",
} as const;

export const radius = {
  sm:   "4px",   // chips, tight pills
  base: "8px",   // inputs, buttons
  md:   "12px",  // cards
  lg:   "16px",  // modals, large panels
  xl:   "24px",  // hero containers
  full: "9999px",// avatars, on-chain badges
} as const;

export const shadow = {
  sm: "0 1px 2px 0 rgba(26, 22, 20, 0.06), 0 1px 1px 0 rgba(26, 22, 20, 0.04)",
  md: "0 4px 8px -2px rgba(26, 22, 20, 0.08), 0 2px 4px -2px rgba(26, 22, 20, 0.06)",
  lg: "0 16px 32px -8px rgba(26, 22, 20, 0.12), 0 4px 8px -4px rgba(26, 22, 20, 0.08)",
} as const;

export const motion = {
  fast: "120ms",
  base: "200ms",
  slow: "320ms",
  ease: "cubic-bezier(0.2, 0.8, 0.2, 1)",
} as const;

export const tokens = {
  color,
  font,
  scale,
  space,
  radius,
  shadow,
  motion,
} as const;

export type Tokens = typeof tokens;
export type ColorTokens = typeof color;
export type FontTokens = typeof font;
export type ScaleTokens = typeof scale;
export type SpaceTokens = typeof space;
export type RadiusTokens = typeof radius;
export type ShadowTokens = typeof shadow;
export type MotionTokens = typeof motion;

export default tokens;
