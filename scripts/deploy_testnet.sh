#!/usr/bin/env bash
# DAMAY — Soroban testnet deploy. Idempotent.
#
# Usage:
#   scripts/deploy_testnet.sh [--force]
#
# Behavior:
#   - Verifies `stellar` CLI is installed.
#   - Ensures a deployer identity named `damay-deployer` exists; funds via friendbot.
#   - Builds both contracts (release wasm).
#   - For each contract, deploys only if `deployments.json` has a null id (or --force).
#   - Initializes Reputation contract with admin=deployer on first deploy.
#   - Updates deployments.json with id, wasm_hash, deployed_at.
#
# Requirements: stellar CLI >= 22, jq.

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DEPLOYMENTS="${REPO_ROOT}/deployments.json"
CONTRACTS_DIR="${REPO_ROOT}/contracts"
NETWORK="${STELLAR_NETWORK:-testnet}"
IDENTITY="${STELLAR_IDENTITY:-damay-deployer}"
FORCE=0

for arg in "$@"; do
  case "$arg" in
    --force) FORCE=1 ;;
    -h|--help)
      sed -n '2,16p' "${BASH_SOURCE[0]}"
      exit 0
      ;;
    *) echo "unknown arg: $arg" >&2; exit 2 ;;
  esac
done

log() { printf "[deploy] %s\n" "$*" >&2; }

# ---------------------------------------------------------------------------
# 1. Toolchain check
# ---------------------------------------------------------------------------
if ! command -v stellar >/dev/null 2>&1; then
  cat >&2 <<EOF
ERROR: 'stellar' CLI not found.
Install it:
  cargo install --locked stellar-cli
  # or
  curl -sSf https://stellar.org/install.sh | sh
Then re-run this script.
EOF
  exit 1
fi

if ! command -v jq >/dev/null 2>&1; then
  echo "ERROR: 'jq' is required. Install via your package manager." >&2
  exit 1
fi

# ---------------------------------------------------------------------------
# 2. Identity bootstrap
# ---------------------------------------------------------------------------
if ! stellar keys ls 2>/dev/null | grep -q "^${IDENTITY}\$"; then
  log "Generating deployer identity '${IDENTITY}' on ${NETWORK}..."
  stellar keys generate "${IDENTITY}" --network "${NETWORK}" --fund
else
  log "Identity '${IDENTITY}' already exists; ensuring funded..."
  # Friendbot is idempotent (no-op if already funded enough).
  stellar keys fund "${IDENTITY}" --network "${NETWORK}" >/dev/null 2>&1 || true
fi

DEPLOYER_ADDR="$(stellar keys address "${IDENTITY}")"
log "Deployer: ${DEPLOYER_ADDR}"

# ---------------------------------------------------------------------------
# 3. Build
# ---------------------------------------------------------------------------
log "Building contracts (release)..."
(cd "${CONTRACTS_DIR}" && stellar contract build)

# Soroban CLI 22.x emits to wasm32v1-none; older CLIs to wasm32-unknown-unknown.
if [ -d "${CONTRACTS_DIR}/target/wasm32v1-none/release" ]; then
  WASM_TARGET_DIR="${CONTRACTS_DIR}/target/wasm32v1-none/release"
else
  WASM_TARGET_DIR="${CONTRACTS_DIR}/target/wasm32-unknown-unknown/release"
fi
REPUTATION_WASM="${WASM_TARGET_DIR}/damay_reputation.wasm"
PALUWAGAN_WASM="${WASM_TARGET_DIR}/damay_paluwagan.wasm"

for f in "${REPUTATION_WASM}" "${PALUWAGAN_WASM}"; do
  if [ ! -f "${f}" ]; then
    echo "ERROR: build artifact missing: ${f}" >&2
    exit 1
  fi
done

# ---------------------------------------------------------------------------
# 4. Deploy helpers
# ---------------------------------------------------------------------------
read_id() { jq -r ".contracts.$1.id // empty" "${DEPLOYMENTS}"; }

write_field() {
  local contract="$1" field="$2" value="$3"
  local tmp
  tmp="$(mktemp)"
  jq --arg c "${contract}" --arg f "${field}" --arg v "${value}" \
    '.contracts[$c][$f] = $v' "${DEPLOYMENTS}" > "${tmp}"
  mv "${tmp}" "${DEPLOYMENTS}"
}

deploy_contract() {
  local name="$1" wasm="$2"
  local existing
  existing="$(read_id "${name}")"
  if [ -n "${existing}" ] && [ "${FORCE}" -eq 0 ]; then
    log "Contract '${name}' already deployed at ${existing}; skipping (use --force to redeploy)."
    echo "${existing}"
    return 0
  fi

  log "Deploying '${name}' from ${wasm}..."
  local out
  out="$(stellar contract deploy --wasm "${wasm}" --source "${IDENTITY}" --network "${NETWORK}")"
  # stellar contract deploy prints the contract id on stdout (sometimes with trailing whitespace).
  local cid
  cid="$(echo "${out}" | tail -n1 | tr -d '[:space:]')"
  local hash
  hash="$(sha256sum "${wasm}" | awk '{print $1}')"
  local ts
  ts="$(date -u +%Y-%m-%dT%H:%M:%SZ)"

  write_field "${name}" "id" "${cid}"
  write_field "${name}" "wasm_hash" "${hash}"
  write_field "${name}" "deployed_at" "${ts}"
  log "Deployed '${name}' at ${cid}"
  echo "${cid}"
}

# ---------------------------------------------------------------------------
# 5. Deploy + init
# ---------------------------------------------------------------------------
REPUTATION_ID="$(deploy_contract reputation "${REPUTATION_WASM}")"
PALUWAGAN_ID="$(deploy_contract paluwagan "${PALUWAGAN_WASM}")"

# Init reputation only if newly deployed (or --force). Detect via deployed_at
# timestamp being within the last minute is fragile; instead, attempt init and
# tolerate AlreadyInitialized as a no-op.
log "Initializing reputation (admin=${DEPLOYER_ADDR})..."
if ! stellar contract invoke \
  --id "${REPUTATION_ID}" \
  --source "${IDENTITY}" \
  --network "${NETWORK}" \
  -- init --admin "${DEPLOYER_ADDR}" 2> /tmp/damay-init.err; then
  if grep -qi "AlreadyInitialized\|Error(Contract, #2)" /tmp/damay-init.err; then
    log "Reputation already initialized — skipping."
  else
    echo "Reputation init failed:" >&2
    cat /tmp/damay-init.err >&2
    exit 1
  fi
fi

# Paluwagan is per-round and initialized by the backend when a round
# `activate` action fires. We do NOT init the workspace-template instance here.

log "Done."
log "  reputation id: ${REPUTATION_ID}"
log "  paluwagan id : ${PALUWAGAN_ID}"
log "Updated ${DEPLOYMENTS}"
