import { NextResponse, type NextRequest } from "next/server";
import { cookies } from "next/headers";
import { getServerSupabase } from "@/lib/supabase";

export const dynamic = "force-dynamic";

/**
 * Magic-link OAuth completion. Supabase posts a `code` back; we exchange it
 * for a session cookie and redirect to /dashboard.
 */
export async function GET(req: NextRequest) {
  const url = new URL(req.url);
  const code = url.searchParams.get("code");
  if (!code) {
    return NextResponse.redirect(new URL("/login", url));
  }
  const cookieStore = await cookies();
  const supabase = getServerSupabase({
    get: (n) => cookieStore.get(n)?.value,
    set: (n, v, o) => cookieStore.set({ name: n, value: v, ...(o ?? {}) }),
    remove: (n, o) => cookieStore.set({ name: n, value: "", ...(o ?? {}) }),
  });
  if (!supabase) {
    return NextResponse.redirect(new URL("/dashboard", url));
  }
  await supabase.auth.exchangeCodeForSession(code);
  return NextResponse.redirect(new URL("/dashboard", url));
}
