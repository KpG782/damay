# EasyPanel Deploy Runbook — DAMAY

> **Audience:** Ken, running from a machine with outbound to Docker registry, EasyPanel host, Stellar testnet, Supabase, and Twilio. The sandbox where this repo was assembled cannot reach those services — every step below must be run from your workstation or the EasyPanel host.

**Targets**

- `damay.kenbuilds.tech` → web (Next.js standalone, port 3000)
- `api.damay.kenbuilds.tech` → api (FastAPI, port 8000)

**Pre-reqs on your machine**

- Docker 24+
- `gh` CLI authenticated (`gh auth status`)
- DNS for both subdomains pointing at the EasyPanel host (Cloudflare proxy off for first deploy, on once it's stable)
- A Supabase project, Twilio account (sandbox WhatsApp is fine), Stellar testnet issuer keypair, Sentry account

---

## 0. Stellar contracts — must come first

EasyPanel doesn't deploy contracts; the backend is mock-mode until `REPUTATION_CONTRACT_ID` + `PALUWAGAN_CONTRACT_ID` are populated.

```bash
cd ~/damay
bash scripts/deploy_testnet.sh
# Writes contract IDs to deployments.json. Copy both IDs — you'll paste them
# as EasyPanel secrets in Step 4.
```

Verify on Stellar Expert:

- `https://stellar.expert/explorer/testnet/contract/<REPUTATION_CONTRACT_ID>`
- `https://stellar.expert/explorer/testnet/contract/<PALUWAGAN_CONTRACT_ID>`

---

## 1. Local preflight (mandatory)

```bash
cd ~/damay
cp .env.example .env.local                      # fill values; see §4 table below
bash scripts/preflight.sh
```

This runs env-parity, builds both Docker images, boots them, hits `/healthz` and `/api/health`. **Do not proceed unless preflight exits 0.**

Optional: full local stack via compose to dry-run the demo.

```bash
docker compose --env-file .env.local up --build
# web → http://localhost:3000   api → http://localhost:8000/docs
```

---

## 2. Push images to GHCR

EasyPanel can build from a Dockerfile directly, but GHCR is faster and keeps each deploy reproducible.

```bash
# One-time
echo "$GHCR_PAT" | docker login ghcr.io -u kpg782 --password-stdin

# Per release
SHA=$(git rev-parse --short HEAD)
docker build -t ghcr.io/kpg782/damay-web:$SHA -t ghcr.io/kpg782/damay-web:latest -f apps/web/Dockerfile .
docker build -t ghcr.io/kpg782/damay-api:$SHA -t ghcr.io/kpg782/damay-api:latest -f apps/api/Dockerfile .
docker push ghcr.io/kpg782/damay-web:$SHA && docker push ghcr.io/kpg782/damay-web:latest
docker push ghcr.io/kpg782/damay-api:$SHA && docker push ghcr.io/kpg782/damay-api:latest
```

Then set the same `GHCR_PAT` value as `EASYPANEL_REGISTRY_TOKEN` in your EasyPanel project (Project → Settings → Registries → Add: `ghcr.io`, user `kpg782`, token).

---

## 3. EasyPanel project setup (one-time, via UI)

1. **Create project** named `damay`.
2. **Create service `web`**:
   - Source: Image → `ghcr.io/kpg782/damay-web:latest`
   - Port: 3000
   - Healthcheck: `GET /api/health` every 30s
   - Domain: `damay.kenbuilds.tech` (port 3000, HTTPS, Let's Encrypt)
3. **Create service `api`**:
   - Source: Image → `ghcr.io/kpg782/damay-api:latest`
   - Port: 8000
   - Healthcheck: `GET /healthz` every 30s
   - Domain: `api.damay.kenbuilds.tech` (port 8000, HTTPS, Let's Encrypt)
4. Paste env vars per §4. **Save** but don't deploy yet.

The committed `easypanel.yml` mirrors this layout — if your EasyPanel install supports `easypanel deploy <yml>`, you can run `easypanel deploy easypanel.yml` instead of clicking through the UI.

---

## 4. Environment variables (paste into EasyPanel "Environment" tab)

| Key | Where to get it | Notes |
|---|---|---|
| `NODE_ENV` | literal `production` | both services |
| `APP_URL` | `https://damay.kenbuilds.tech` | both |
| `API_URL` | `https://api.damay.kenbuilds.tech` | both |
| `NEXT_PUBLIC_APP_URL` | same as `APP_URL` | web only — baked at build time |
| `NEXT_PUBLIC_API_URL` | same as `API_URL` | web only |
| `NEXT_PUBLIC_SUPABASE_URL` | Supabase → Project Settings → API → Project URL | web only |
| `NEXT_PUBLIC_SUPABASE_ANON_KEY` | Supabase → API → anon public | web only |
| `NEXT_PUBLIC_STELLAR_NETWORK` | literal `testnet` | web only |
| `SUPABASE_URL` | same as above | both |
| `SUPABASE_ANON_KEY` | same as above | both |
| `SUPABASE_SERVICE_ROLE_KEY` | Supabase → API → service_role | **api only — never expose to web** |
| `SUPABASE_DB_URL` | Supabase → Database → Connection string (URI, pooled) | api only |
| `SUPABASE_JWT_SECRET` | Supabase → API → JWT Settings → secret | api only |
| `STELLAR_NETWORK` | `testnet` | api only |
| `STELLAR_HORIZON_URL` | `https://horizon-testnet.stellar.org` | api only |
| `STELLAR_SOROBAN_RPC_URL` | `https://soroban-testnet.stellar.org` | api only |
| `STELLAR_ISSUER_SECRET` | Stellar Lab → Create Account → friendbot fund → copy `S…` secret | api only |
| `REPUTATION_CONTRACT_ID` | from `deployments.json` after Step 0 | api only |
| `PALUWAGAN_CONTRACT_ID` | from `deployments.json` after Step 0 | api only |
| `TWILIO_ACCOUNT_SID` | Twilio Console → Account Info → SID | api only |
| `TWILIO_AUTH_TOKEN` | Twilio Console → Account Info → Auth Token | api only |
| `TWILIO_WHATSAPP_FROM` | `whatsapp:+14155238886` for sandbox | api only |
| `TWILIO_WEBHOOK_VALIDATION` | `true` | api only |
| `WEBHOOK_PUBLIC_BASE_URL` | `https://api.damay.kenbuilds.tech` | api only — used by Twilio signature verifier |
| `ANTHROPIC_API_KEY` | console.anthropic.com → API Keys | api only |
| `ANTHROPIC_MODEL` | `claude-opus-4-7` | api only |
| `SENTRY_DSN` | Sentry → Project → Client Keys (DSN); create two projects (one per service) | both, distinct values |
| `LOG_LEVEL` | `info` | both |
| `JWT_SECRET` | `openssl rand -hex 32` | api only |
| `WEBHOOK_SIGNING_SECRET` | `openssl rand -hex 32` | api only |
| `FEATURE_LATE_NIGHT_LEND` | `false` | both |
| `FEATURE_REAL_PAYMENTS` | `false` | both |
| `FEATURE_DEMO_MODE` | `true` | both |

After pasting: confirm `bash scripts/env-parity.sh --against /path/to/exported.env` returns OK.

---

## 5. First deploy

Click **Deploy** on `api` first, wait for green healthcheck, then **Deploy** on `web`.

```bash
# verify from your phone / laptop
curl -fsS https://api.damay.kenbuilds.tech/healthz | jq
curl -fsS -I https://damay.kenbuilds.tech/ | head
```

Both must return `200`. The `/healthz` body should show `db: ok`, `stellar: ok`, `twilio: ok`.

---

## 6. Twilio webhook wiring

Once `api.damay.kenbuilds.tech` is live, point the Twilio sandbox at it:

```bash
# Sandbox (Console → Messaging → Try it out → Send a WhatsApp message → Sandbox settings):
#   When a message comes in:  https://api.damay.kenbuilds.tech/v1/webhooks/twilio
#   Method:                   POST

# Or via Twilio CLI (production phone number flow):
twilio api:core:incoming-phone-numbers:update \
  --sid <PNxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx> \
  --sms-url "https://api.damay.kenbuilds.tech/v1/webhooks/twilio" \
  --sms-method POST \
  --sms-fallback-url "https://api.damay.kenbuilds.tech/v1/webhooks/twilio"
```

Smoke test from your phone: text `JOIN <round_code>` to the sandbox number. Confirm the api logs show signature verified + `messages` row inserted in Supabase.

---

## 7. Sentry

1. Create two Sentry projects: `damay-web` (Next.js) and `damay-api` (Python/FastAPI).
2. Copy each DSN, paste into the matching `SENTRY_DSN` env var (Step 4).
3. Trigger a test error per service:
   ```bash
   curl https://api.damay.kenbuilds.tech/healthz?force_error=1   # if implemented
   # Or temporarily import * as Sentry from "@sentry/nextjs"; Sentry.captureException(new Error("smoke"))
   ```
4. Confirm events appear in Sentry within 1 minute.

---

## 8. Continuous deploy (after first manual deploy)

`.github/workflows/ci.yml` `deploy` job runs on push to `main`. Set these GitHub repo secrets:

| Secret | Value |
|---|---|
| `GHCR_PAT` | a Personal Access Token with `write:packages` |
| `EASYPANEL_URL` | e.g. `https://panel.kenbuilds.tech` |
| `EASYPANEL_API_TOKEN` | EasyPanel → Account → API Tokens |
| `EASYPANEL_PROJECT` | `damay` |

The job will: build both images, push to GHCR with `:${GITHUB_SHA}` and `:latest`, then `POST $EASYPANEL_URL/api/services/app.deployService` for each service. Without the secrets it no-ops with a warning (safe for PRs).

---

## 9. Post-deploy verification (Phase 4 DoD)

Run all of these. Every step must pass.

```bash
# 1. Web responds
curl -fsS -o /dev/null -w "web: %{http_code}\n" https://damay.kenbuilds.tech/

# 2. API responds
curl -fsS https://api.damay.kenbuilds.tech/healthz

# 3. Twilio webhook (signature will fail without a real Twilio request; expect 403/422)
curl -i -X POST https://api.damay.kenbuilds.tech/v1/webhooks/twilio \
  -d "From=whatsapp:+14155551234&Body=PING"

# 4. Stellar tx visible — trigger a contribution from the dashboard, then
curl -fsS "https://horizon-testnet.stellar.org/accounts/$STELLAR_ISSUER_PUBLIC/transactions?order=desc&limit=1"
# Or open: https://stellar.expert/explorer/testnet/account/<STELLAR_ISSUER_PUBLIC>
```

---

## 10. Rollback

```bash
# Identify last-good image tag (SHA)
gh run list --workflow ci.yml --branch main --limit 5

# Re-deploy that SHA on EasyPanel:
# UI: Service → Source → change tag from `latest` to `<SHA>` → Deploy
# API:
curl -fsS -X POST \
  -H "Authorization: Bearer $EASYPANEL_API_TOKEN" \
  -H "Content-Type: application/json" \
  "$EASYPANEL_URL/api/services/app.updateSourceImage" \
  -d "{\"projectName\":\"damay\",\"serviceName\":\"api\",\"image\":\"ghcr.io/kpg782/damay-api:<SHA>\"}"
curl -fsS -X POST \
  -H "Authorization: Bearer $EASYPANEL_API_TOKEN" \
  "$EASYPANEL_URL/api/services/app.deployService" \
  -d '{"projectName":"damay","serviceName":"api"}'
# repeat for web
```

For a no-deploy "switch off" of a broken release, in EasyPanel set replicas to 0 on the affected service; the previous container keeps serving until you flip back.

---

## 11. Known sandbox limits (why this had to be a runbook)

The build sandbox where this repo was assembled cannot reach `*.stellar.org`, the EasyPanel API, or the Docker daemon. As a result:

- Contracts are built + tested but not deployed (see `deployments.json` → `status: PENDING_DEPLOY`).
- Docker images were not pushed from sandbox; Dockerfiles + compose were syntax-validated only.
- EasyPanel deploy must be triggered manually from your machine for the first roll.

Once Steps 0–6 are green from your workstation, CI takes over for every subsequent push to `main`.
