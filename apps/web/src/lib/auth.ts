import { cookies } from "next/headers";
import { getServerSupabase } from "./supabase";
import { isDemoMode } from "./env";

const DEMO_ORGANIZER = {
  id: "org_demo_carmela",
  email: "carmela@damay.demo",
  display_name: "Carmela",
};

/**
 * Resolve the current organizer session. In demo mode (no Supabase configured)
 * we return a deterministic demo organizer so the orchestrator's demo flow
 * still works end-to-end without external services.
 */
export async function getSession() {
  if (isDemoMode) {
    return { organizer: DEMO_ORGANIZER, isDemo: true as const };
  }
  const cookieStore = await cookies();
  const supabase = getServerSupabase({
    get: (n) => cookieStore.get(n)?.value,
    set: (n, v, o) => {
      try {
        cookieStore.set({ name: n, value: v, ...(o ?? {}) });
      } catch {
        // setting cookies from Server Components is a noop — middleware handles it.
      }
    },
    remove: (n, o) => {
      try {
        cookieStore.set({ name: n, value: "", ...(o ?? {}) });
      } catch {
        /* noop */
      }
    },
  });
  if (!supabase) return { organizer: null, isDemo: false as const };
  const { data } = await supabase.auth.getUser();
  if (!data.user) return { organizer: null, isDemo: false as const };
  return {
    organizer: {
      id: data.user.id,
      email: data.user.email ?? "",
      display_name: (data.user.user_metadata?.display_name as string) ?? "Organizer",
    },
    isDemo: false as const,
  };
}
