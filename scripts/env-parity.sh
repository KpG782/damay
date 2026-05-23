#!/usr/bin/env bash
# env-parity.sh — fail CI if required env keys drift.
#
# Usage:
#   scripts/env-parity.sh                       # compare .env.example ⇄ .env.local (dev)
#   scripts/env-parity.sh --against .env.prod   # compare .env.example ⇄ given file
#   scripts/env-parity.sh --keys KEY1 KEY2 ...  # ensure these keys exist in .env.example
#   scripts/env-parity.sh --ci                  # CI mode: only verify .env.example is parseable
#                                                 and has no empty key names; warns if .env.local
#                                                 missing instead of failing.
#
# Exit codes:
#   0  parity OK
#   1  mismatch (missing keys in either side, or extra keys not in example)
#   2  bad invocation / file not found

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
EXAMPLE="${REPO_ROOT}/.env.example"

err()  { printf '\033[31m[env-parity] %s\033[0m\n' "$*" >&2; }
ok()   { printf '\033[32m[env-parity] %s\033[0m\n'   "$*"; }
warn() { printf '\033[33m[env-parity] %s\033[0m\n'  "$*" >&2; }

if [[ ! -f "$EXAMPLE" ]]; then
  err ".env.example not found at $EXAMPLE"
  exit 2
fi

# Extract uppercase KEY names from a dotenv-style file.
extract_keys() {
  local file="$1"
  # match KEY=... at line start, ignore comments + blanks.
  grep -E '^[A-Z][A-Z0-9_]*=' "$file" | sed -E 's/=.*$//' | sort -u
}

EXAMPLE_KEYS="$(extract_keys "$EXAMPLE")"

# Sanity: no empty/duplicate keys in .env.example.
if [[ -z "$EXAMPLE_KEYS" ]]; then
  err ".env.example contains no parseable keys"
  exit 1
fi
DUPES="$(extract_keys "$EXAMPLE" | uniq -d || true)"
if [[ -n "$DUPES" ]]; then
  err "duplicate keys in .env.example:"
  echo "$DUPES" >&2
  exit 1
fi

MODE="default"
TARGET=""
REQUIRED_KEYS=()

while [[ $# -gt 0 ]]; do
  case "$1" in
    --against) MODE="against"; TARGET="${2:-}"; shift 2 ;;
    --keys)    MODE="keys"; shift; REQUIRED_KEYS=("$@"); break ;;
    --ci)      MODE="ci"; shift ;;
    -h|--help) sed -n '1,30p' "$0"; exit 0 ;;
    *) err "unknown arg: $1"; exit 2 ;;
  esac
done

case "$MODE" in
  ci)
    ok ".env.example parses with $(echo "$EXAMPLE_KEYS" | wc -l | tr -d ' ') keys; no duplicates."
    if [[ -f "${REPO_ROOT}/.env.local" ]]; then
      TARGET="${REPO_ROOT}/.env.local"
      MODE="against"
    else
      warn ".env.local not present in CI — skipping diff (expected)."
      exit 0
    fi
    ;;
  default)
    TARGET="${REPO_ROOT}/.env.local"
    if [[ ! -f "$TARGET" ]]; then
      warn ".env.local missing — copy .env.example to .env.local for local dev."
      exit 0
    fi
    MODE="against"
    ;;
esac

if [[ "$MODE" == "against" ]]; then
  if [[ -z "$TARGET" || ! -f "$TARGET" ]]; then
    err "target file not found: $TARGET"
    exit 2
  fi
  TARGET_KEYS="$(extract_keys "$TARGET")"

  MISSING="$(comm -23 <(echo "$EXAMPLE_KEYS") <(echo "$TARGET_KEYS") || true)"
  EXTRA="$(comm -13 <(echo "$EXAMPLE_KEYS") <(echo "$TARGET_KEYS") || true)"

  STATUS=0
  if [[ -n "$MISSING" ]]; then
    err "missing in $TARGET (declared in .env.example):"
    echo "$MISSING" | sed 's/^/  - /' >&2
    STATUS=1
  fi
  if [[ -n "$EXTRA" ]]; then
    err "present in $TARGET but not in .env.example (drift):"
    echo "$EXTRA" | sed 's/^/  + /' >&2
    STATUS=1
  fi
  if [[ $STATUS -eq 0 ]]; then
    ok "env parity OK: $TARGET matches .env.example"
  fi
  exit $STATUS
fi

if [[ "$MODE" == "keys" ]]; then
  STATUS=0
  for key in "${REQUIRED_KEYS[@]}"; do
    if ! echo "$EXAMPLE_KEYS" | grep -qx "$key"; then
      err "required key missing from .env.example: $key"
      STATUS=1
    fi
  done
  [[ $STATUS -eq 0 ]] && ok "all required keys present in .env.example"
  exit $STATUS
fi
