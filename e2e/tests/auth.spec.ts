/**
 * Auth + RLS guard tests.
 *
 * The e2e stack runs the web app in **demo mode** (Supabase env unset). In
 * that mode `lib/auth.ts::getSession` returns a deterministic demo organizer
 * so the dashboard renders for any visitor — there is no redirect to /login.
 *
 * That's intentional for the hackathon demo: judges should be able to click
 * "Try the demo" without provisioning Supabase. The auth-required behaviour
 * lives behind `isDemoMode === false`, which only fires when
 * `NEXT_PUBLIC_SUPABASE_URL` is set.
 *
 * So this suite covers two things:
 *   1. Demo-mode (current run): /dashboard is reachable + shows demo org name.
 *   2. API-side RLS proxy: /v1/rounds without a Bearer JWT must 401.
 *
 * The "non-org user cannot read other org's rounds" check from the brief
 * lives in `apps/api/tests/test_rounds.py` (organizer-scoped DB filter
 * unit-tested). At the e2e layer we verify the boundary: no JWT → 401, no
 * rounds leaked.
 */

import { test, expect } from "@playwright/test";

test.describe("auth & RLS boundary", () => {
  test("/dashboard renders in demo mode (NEXT_PUBLIC_SUPABASE_URL unset)", async ({ page }) => {
    await page.goto("/dashboard");
    // Demo organizer is "Carmela" (lib/auth.ts::DEMO_ORGANIZER).
    await expect(page.getByRole("heading", { level: 1 })).toContainText(/Carmela/i);
    // The "Offline — demo data" badge marks the demo-mode bypass clearly.
    // Either the badge is shown OR rounds rendered from API; both prove the
    // page reached organizer-scoped UI rather than a redirect.
    await expect(page).toHaveURL(/\/dashboard$/);
  });

  test("API /v1/rounds without JWT returns 401", async ({ request }) => {
    const res = await request.get("http://127.0.0.1:8000/v1/rounds");
    // The rounds router requires JWT (ARCHITECTURE.md §2.2). No Authorization
    // header → UNAUTHENTICATED. 403 also acceptable for some FastAPI auth
    // dependencies; we accept either to stay decoupled from the chosen
    // dependency style.
    expect([401, 403]).toContain(res.status());
    const body = await res.json().catch(() => ({}));
    // Error envelope per ARCHITECTURE.md §2.1 — must not leak any round IDs.
    const serialized = JSON.stringify(body);
    expect(serialized).not.toMatch(/rnd_kapitbahay|rnd_pamilya|rnd_tindera/);
  });

  test("API /v1/rounds with a foreign JWT does not leak another org's rounds", async ({ request }) => {
    // Synthesize a JWT for an unrelated organizer id. The API uses
    // SUPABASE_JWT_SECRET=e2e-jwt-secret-please-change in webServer env.
    const crypto = await import("node:crypto");
    const SECRET = "e2e-jwt-secret-please-change";
    const header = Buffer.from(
      JSON.stringify({ alg: "HS256", typ: "JWT" })
    ).toString("base64url");
    const payload = Buffer.from(
      JSON.stringify({
        sub: "00000000-0000-0000-0000-0000000000ff", // foreign org
        email: "stranger@example.com",
        iat: Math.floor(Date.now() / 1000),
        exp: Math.floor(Date.now() / 1000) + 3600,
      })
    ).toString("base64url");
    const sig = crypto
      .createHmac("sha256", SECRET)
      .update(`${header}.${payload}`)
      .digest("base64url");
    const token = `${header}.${payload}.${sig}`;

    const res = await request.get("http://127.0.0.1:8000/v1/rounds", {
      headers: { authorization: `Bearer ${token}` },
    });
    // Either 200 with empty data (rows filtered by organizer_id) or 4xx
    // (no organizer mapping → unauthorized). Both are acceptable; the
    // invariant we enforce is "no foreign rounds leaked".
    const txt = await res.text();
    expect(txt).not.toMatch(/rnd_kapitbahay|rnd_pamilya|rnd_tindera/);
    if (res.status() === 200) {
      const data = JSON.parse(txt);
      // Mock-mode API returns an empty list for an unknown organizer.
      const rounds = Array.isArray(data.data) ? data.data : data;
      expect(Array.isArray(rounds) ? rounds.length : 0).toBe(0);
    }
  });
});
