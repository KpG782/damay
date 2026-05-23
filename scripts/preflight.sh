#!/usr/bin/env bash
# preflight.sh — run all checks before declaring a deploy ready.
#
#   1. env-parity --ci    (sanity-parse .env.example)
#   2. docker build       (api + web; capture sizes; enforce 300/200 MB budgets)
#   3. boot containers    (compose up -d; wait for /healthz on both)
#   4. teardown
#
# Exit 0 only if every step passes. Designed to be run locally before flipping
# the EasyPanel deploy switch, and as the gate for `gh workflow run deploy`.

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

bold() { printf '\033[1m%s\033[0m\n' "$*"; }
ok()   { printf '\033[32m[preflight] %s\033[0m\n' "$*"; }
err()  { printf '\033[31m[preflight] %s\033[0m\n' "$*" >&2; }
warn() { printf '\033[33m[preflight] %s\033[0m\n' "$*" >&2; }

API_SIZE_BUDGET_MB=300
WEB_SIZE_BUDGET_MB=200

# ---------- 1. env-parity --------------------------------------------------
bold "[1/4] env-parity --ci"
bash scripts/env-parity.sh --ci
ok "env-parity OK"

# ---------- 2. docker builds ----------------------------------------------
if ! command -v docker >/dev/null 2>&1; then
  err "docker is required for preflight (image builds + healthcheck boot)."
  exit 2
fi
if ! docker info >/dev/null 2>&1; then
  err "docker daemon not reachable. Start Docker Desktop or the dockerd service."
  exit 2
fi

bold "[2/4] docker build api + web"
docker build -t damay-api:preflight -f apps/api/Dockerfile .
docker build -t damay-web:preflight -f apps/web/Dockerfile .

# Size budget check.
size_mb() {
  docker image inspect "$1" --format '{{.Size}}' | awk '{printf "%d", $1/1024/1024}'
}
API_SIZE=$(size_mb damay-api:preflight)
WEB_SIZE=$(size_mb damay-web:preflight)
ok "api image: ${API_SIZE} MB (budget ${API_SIZE_BUDGET_MB})"
ok "web image: ${WEB_SIZE} MB (budget ${WEB_SIZE_BUDGET_MB})"

STATUS=0
if (( API_SIZE > API_SIZE_BUDGET_MB )); then
  err "api image exceeds ${API_SIZE_BUDGET_MB} MB budget"
  STATUS=1
fi
if (( WEB_SIZE > WEB_SIZE_BUDGET_MB )); then
  err "web image exceeds ${WEB_SIZE_BUDGET_MB} MB budget"
  STATUS=1
fi
[[ $STATUS -ne 0 ]] && exit 1

# ---------- 3. boot + healthcheck -----------------------------------------
bold "[3/4] boot containers + curl healthchecks"

if [[ ! -f .env.local ]]; then
  warn ".env.local not present; using .env.example (some checks will degrade)."
  COMPOSE_ENV=".env.example"
else
  COMPOSE_ENV=".env.local"
fi

# Boot api standalone first (web depends on it).
docker rm -f damay-preflight-api damay-preflight-web >/dev/null 2>&1 || true
docker run -d --rm --name damay-preflight-api \
  --env-file "$COMPOSE_ENV" \
  -p 18000:8000 \
  damay-api:preflight >/dev/null

# Poll /healthz for up to 60s.
api_ready=0
for i in $(seq 1 30); do
  if curl -fsS --max-time 2 http://127.0.0.1:18000/healthz >/dev/null 2>&1; then
    api_ready=1
    break
  fi
  sleep 2
done
if (( api_ready != 1 )); then
  err "api /healthz did not respond within 60s"
  docker logs damay-preflight-api | tail -40 >&2 || true
  docker rm -f damay-preflight-api >/dev/null 2>&1 || true
  exit 1
fi
ok "api /healthz → 200"

# Boot web.
docker run -d --rm --name damay-preflight-web \
  --env-file "$COMPOSE_ENV" \
  -e API_URL=http://host.docker.internal:18000 \
  --add-host=host.docker.internal:host-gateway \
  -p 13000:3000 \
  damay-web:preflight >/dev/null

web_ready=0
for i in $(seq 1 30); do
  if curl -fsS --max-time 2 http://127.0.0.1:13000/api/health >/dev/null 2>&1; then
    web_ready=1
    break
  fi
  sleep 2
done
if (( web_ready != 1 )); then
  err "web /api/health did not respond within 60s"
  docker logs damay-preflight-web | tail -40 >&2 || true
  docker rm -f damay-preflight-api damay-preflight-web >/dev/null 2>&1 || true
  exit 1
fi
ok "web /api/health → 200"

# ---------- 4. teardown ---------------------------------------------------
bold "[4/4] teardown"
docker rm -f damay-preflight-api damay-preflight-web >/dev/null 2>&1 || true
ok "preflight passed — safe to deploy."
