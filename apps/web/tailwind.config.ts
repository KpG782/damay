import type { Config } from "tailwindcss";

/**
 * DAMAY Tailwind config.
 *
 * All design tokens are exposed as CSS variables in `globals.css`. Tailwind
 * utilities map onto those variables so we never hard-code hex values in
 * components. The source of truth lives in `packages/ui/tokens.ts`.
 */
const config: Config = {
  darkMode: ["class"],
  content: [
    "./src/**/*.{ts,tsx}",
    "../../packages/ui/**/*.{ts,tsx}",
  ],
  theme: {
    container: {
      center: true,
      padding: "1.25rem",
      screens: {
        "2xl": "1280px",
      },
    },
    extend: {
      colors: {
        bg: {
          base: "hsl(var(--bg-base))",
          subtle: "hsl(var(--bg-subtle))",
          raised: "hsl(var(--bg-raised))",
        },
        fg: {
          base: "hsl(var(--fg-base))",
          muted: "hsl(var(--fg-muted))",
          subtle: "hsl(var(--fg-subtle))",
        },
        brand: {
          DEFAULT: "hsl(var(--brand-base))",
          base: "hsl(var(--brand-base))",
          hover: "hsl(var(--brand-hover))",
          subtle: "hsl(var(--brand-subtle))",
        },
        accent: {
          DEFAULT: "hsl(var(--accent-base))",
          base: "hsl(var(--accent-base))",
          hover: "hsl(var(--accent-hover))",
        },
        success: "hsl(var(--success))",
        warning: "hsl(var(--warning))",
        danger: "hsl(var(--danger))",
        border: {
          DEFAULT: "hsl(var(--border-base))",
          base: "hsl(var(--border-base))",
          subtle: "hsl(var(--border-subtle))",
        },
        // shadcn semantic aliases (mapped to our tokens)
        background: "hsl(var(--bg-base))",
        foreground: "hsl(var(--fg-base))",
        card: {
          DEFAULT: "hsl(var(--bg-raised))",
          foreground: "hsl(var(--fg-base))",
        },
        popover: {
          DEFAULT: "hsl(var(--bg-raised))",
          foreground: "hsl(var(--fg-base))",
        },
        primary: {
          DEFAULT: "hsl(var(--brand-base))",
          foreground: "hsl(var(--bg-raised))",
        },
        secondary: {
          DEFAULT: "hsl(var(--bg-subtle))",
          foreground: "hsl(var(--fg-base))",
        },
        muted: {
          DEFAULT: "hsl(var(--bg-subtle))",
          foreground: "hsl(var(--fg-muted))",
        },
        destructive: {
          DEFAULT: "hsl(var(--danger))",
          foreground: "hsl(var(--bg-raised))",
        },
        input: "hsl(var(--border-base))",
        ring: "hsl(var(--brand-base))",
      },
      fontFamily: {
        sans: ["var(--font-sans)", "Inter", "system-ui", "sans-serif"],
        display: ["var(--font-display)", "Fraunces", "Georgia", "serif"],
        mono: ["var(--font-mono)", "ui-monospace", "monospace"],
      },
      fontSize: {
        xs: ["0.75rem", { lineHeight: "1rem" }],
        sm: ["0.875rem", { lineHeight: "1.25rem" }],
        base: ["1rem", { lineHeight: "1.6rem" }],
        lg: ["1.125rem", { lineHeight: "1.75rem" }],
        xl: ["1.25rem", { lineHeight: "1.85rem" }],
        "2xl": ["1.5rem", { lineHeight: "2rem" }],
        "3xl": ["1.875rem", { lineHeight: "2.25rem" }],
        "4xl": ["2.25rem", { lineHeight: "2.5rem" }],
        "5xl": ["3rem", { lineHeight: "1.05" }],
      },
      borderRadius: {
        sm: "4px",
        DEFAULT: "8px",
        md: "12px",
        lg: "16px",
        xl: "24px",
      },
      boxShadow: {
        sm: "0 1px 2px 0 rgba(26, 22, 20, 0.06), 0 1px 1px 0 rgba(26, 22, 20, 0.04)",
        md: "0 4px 8px -2px rgba(26, 22, 20, 0.08), 0 2px 4px -2px rgba(26, 22, 20, 0.06)",
        lg: "0 16px 32px -8px rgba(26, 22, 20, 0.12), 0 4px 8px -4px rgba(26, 22, 20, 0.08)",
      },
      transitionTimingFunction: {
        damay: "cubic-bezier(0.2, 0.8, 0.2, 1)",
      },
      transitionDuration: {
        fast: "120ms",
        base: "200ms",
        slow: "320ms",
      },
      keyframes: {
        shimmer: {
          "0%": { backgroundPosition: "-200% 0" },
          "100%": { backgroundPosition: "200% 0" },
        },
        "slide-in": {
          "0%": { opacity: "0", transform: "translateY(-8px)" },
          "100%": { opacity: "1", transform: "translateY(0)" },
        },
        "fade-in": {
          "0%": { opacity: "0" },
          "100%": { opacity: "1" },
        },
      },
      animation: {
        shimmer: "shimmer 1.6s cubic-bezier(0.2, 0.8, 0.2, 1) infinite",
        "slide-in": "slide-in 320ms cubic-bezier(0.2, 0.8, 0.2, 1)",
        "fade-in": "fade-in 200ms cubic-bezier(0.2, 0.8, 0.2, 1)",
      },
    },
  },
  plugins: [require("tailwindcss-animate")],
};

export default config;
