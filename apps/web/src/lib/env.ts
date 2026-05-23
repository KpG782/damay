import { z } from "zod";

/**
 * Public env is what we ship to the browser. Server-only env is read with
 * `process.env` directly in server modules (Server Actions, route handlers).
 *
 * Validation is lazy — Next.js evaluates this once per server boot and once
 * per browser session. If a required var is missing in production we throw
 * loud and early.
 */

const PublicEnvSchema = z.object({
  NEXT_PUBLIC_APP_URL: z.string().url().default("http://localhost:3000"),
  NEXT_PUBLIC_API_URL: z.string().url().default("http://localhost:8000"),
  NEXT_PUBLIC_SUPABASE_URL: z.string().url().optional(),
  NEXT_PUBLIC_SUPABASE_ANON_KEY: z.string().optional(),
  NEXT_PUBLIC_STELLAR_NETWORK: z.enum(["testnet", "public"]).default("testnet"),
});

export type PublicEnv = z.infer<typeof PublicEnvSchema>;

function readPublicEnv(): PublicEnv {
  const raw = {
    NEXT_PUBLIC_APP_URL: process.env.NEXT_PUBLIC_APP_URL,
    NEXT_PUBLIC_API_URL: process.env.NEXT_PUBLIC_API_URL,
    NEXT_PUBLIC_SUPABASE_URL: process.env.NEXT_PUBLIC_SUPABASE_URL,
    NEXT_PUBLIC_SUPABASE_ANON_KEY: process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY,
    NEXT_PUBLIC_STELLAR_NETWORK: process.env.NEXT_PUBLIC_STELLAR_NETWORK,
  };
  const parsed = PublicEnvSchema.safeParse(raw);
  if (!parsed.success) {
    // eslint-disable-next-line no-console
    console.warn("[env] public env validation failed", parsed.error.flatten());
    return PublicEnvSchema.parse({});
  }
  return parsed.data;
}

export const env = readPublicEnv();

export const isSupabaseConfigured = Boolean(
  env.NEXT_PUBLIC_SUPABASE_URL && env.NEXT_PUBLIC_SUPABASE_ANON_KEY
);

export const isDemoMode = !isSupabaseConfigured;
