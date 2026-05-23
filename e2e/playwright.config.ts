import { defineConfig, devices } from "@playwright/test";

/**
 * DAMAY E2E suite — Phase 5 §3.6.
 *
 * Spins up both apps locally:
 *   - apps/web on :3030
 *   - apps/api on :8000
 *
 * The web app falls back to mock data when Supabase env is unset (demo mode),
 * and the API uses an InMemoryStore when SUPABASE_URL is empty — so the suite
 * is fully self-contained, no external services.
 */

const WEB_PORT = 3030;
const API_PORT = 8000;

// Auth token used both by the API (TWILIO_AUTH_TOKEN env) and by the test
// HMAC signing helper. Constant so the webhook replay test can sign its own
// requests against the live API process.
const TWILIO_TOKEN = "test-e2e-token";
const WEBHOOK_BASE = `http://127.0.0.1:${API_PORT}`;

const CI = !!process.env.CI;

export default defineConfig({
  testDir: "./tests",
  fullyParallel: false,
  forbidOnly: CI,
  retries: CI ? 1 : 0,
  workers: 1,
  reporter: CI ? [["line"], ["html", { open: "never" }]] : [["list"]],
  timeout: 30_000,
  expect: { timeout: 5_000 },
  use: {
    baseURL: `http://127.0.0.1:${WEB_PORT}`,
    trace: "retain-on-failure",
    screenshot: "only-on-failure",
    actionTimeout: 7_000,
    navigationTimeout: 15_000,
    extraHTTPHeaders: {
      "x-damay-e2e": "1",
    },
  },
  projects: [
    {
      name: "desktop-chromium",
      use: { ...devices["Desktop Chrome"] },
    },
    {
      name: "mobile-chromium",
      use: { ...devices["Pixel 7"] },
    },
  ],
  webServer: [
    {
      // API — FastAPI via uv, mock mode (no Supabase / Twilio creds present).
      command:
        `uv --directory ../apps/api run uvicorn main:app ` +
        `--host 127.0.0.1 --port ${API_PORT} --log-level warning`,
      url: `${WEBHOOK_BASE}/healthz`,
      reuseExistingServer: !CI,
      timeout: 60_000,
      stdout: "pipe",
      stderr: "pipe",
      env: {
        NODE_ENV: "test",
        FEATURE_DEMO_MODE: "true",
        SUPABASE_URL: "",
        SUPABASE_SERVICE_ROLE_KEY: "",
        SUPABASE_JWT_SECRET: "e2e-jwt-secret-please-change",
        REPUTATION_CONTRACT_ID: "",
        PALUWAGAN_CONTRACT_ID: "",
        TWILIO_ACCOUNT_SID: "",
        TWILIO_AUTH_TOKEN: TWILIO_TOKEN,
        TWILIO_WEBHOOK_VALIDATION: "true",
        WEBHOOK_PUBLIC_BASE_URL: WEBHOOK_BASE,
      },
    },
    {
      // Web — built once, then served via `next start`.
      command:
        `bash -lc "(test -d ../apps/web/.next || ` +
        `pnpm --filter @damay/web build) && ` +
        `pnpm --filter @damay/web exec next start -p ${WEB_PORT}"`,
      url: `http://127.0.0.1:${WEB_PORT}/`,
      reuseExistingServer: !CI,
      timeout: 180_000,
      stdout: "pipe",
      stderr: "pipe",
      env: {
        NODE_ENV: "production",
        NEXT_PUBLIC_APP_URL: `http://127.0.0.1:${WEB_PORT}`,
        NEXT_PUBLIC_API_URL: WEBHOOK_BASE,
        NEXT_PUBLIC_STELLAR_NETWORK: "testnet",
        // Intentionally unset Supabase env to force demo mode.
        NEXT_PUBLIC_SUPABASE_URL: "",
        NEXT_PUBLIC_SUPABASE_ANON_KEY: "",
      },
    },
  ],
});

export { TWILIO_TOKEN, WEBHOOK_BASE, WEB_PORT, API_PORT };
