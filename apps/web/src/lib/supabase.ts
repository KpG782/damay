import { createBrowserClient, createServerClient } from "@supabase/ssr";
import { env, isSupabaseConfigured } from "./env";

/**
 * Browser client — safe to call from Client Components. Returns null if
 * Supabase is not configured (demo mode); callers handle the null gracefully.
 */
export function getBrowserSupabase() {
  if (!isSupabaseConfigured) return null;
  return createBrowserClient(
    env.NEXT_PUBLIC_SUPABASE_URL!,
    env.NEXT_PUBLIC_SUPABASE_ANON_KEY!
  );
}

/**
 * Server client — used in Server Components, Route Handlers, Server Actions.
 * Cookies plumbed by the caller because Next 15 `cookies()` API is async.
 */
export function getServerSupabase(cookieAdapter: {
  get: (name: string) => string | undefined;
  set: (name: string, value: string, options?: Record<string, unknown>) => void;
  remove: (name: string, options?: Record<string, unknown>) => void;
}) {
  if (!isSupabaseConfigured) return null;
  return createServerClient(
    env.NEXT_PUBLIC_SUPABASE_URL!,
    env.NEXT_PUBLIC_SUPABASE_ANON_KEY!,
    {
      cookies: {
        get: cookieAdapter.get,
        set: cookieAdapter.set,
        remove: cookieAdapter.remove,
      },
    }
  );
}
