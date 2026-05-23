# DAMAY Soroban Contracts

Two contracts power the on-chain trust layer for DAMAY:

| Contract     | Purpose                                                                                          | Lifecycle              |
|--------------|--------------------------------------------------------------------------------------------------|------------------------|
| `reputation` | Portable per-member reputation score with bounded event history + 1%/30d decay.                  | Deployed once.         |
| `paluwagan`  | Single rotating-savings round: members, payout schedule, per-cycle contribute + payout state.    | One deployment / round. |

soroban-sdk: pinned to `22.0.0` (resolves to latest patch in the 22.x line).

## Layout

```
contracts/
  Cargo.toml              # workspace
  reputation/
    Cargo.toml
    src/lib.rs
    src/test.rs
  paluwagan/
    Cargo.toml
    src/lib.rs
    src/test.rs
```

## Build + test

```bash
cd contracts
cargo test --all          # 48 tests across both contracts
stellar contract build    # release wasm into target/wasm32-unknown-unknown/release/
```

## Public interface

### `reputation` — `ReputationContract`

| Function                                                               | Auth         | Emits                          | Notes                                                                |
|------------------------------------------------------------------------|--------------|--------------------------------|----------------------------------------------------------------------|
| `init(admin: Address)`                                                 | `admin`      | `("rep","init")`               | One-shot. Errors `AlreadyInitialized` on second call.                |
| `record_contribution(member: Address, weight: u32)`                    | `admin`      | `("rep","contrib")`            | +10 * weight. `weight=0` rejected.                                   |
| `record_default(member: Address, weight: u32)`                         | `admin`      | `("rep","default")`            | -25 * weight.                                                        |
| `record_payout_received(member: Address)`                              | `admin`      | `("rep","payout")`             | +1.                                                                  |
| `get_score(member: Address) -> i64`                                    | view         | —                              | Applies 1%/30d decay vs. ledger timestamp.                           |
| `get_history(member: Address) -> Vec<ReputationEntry>`                 | view         | —                              | Bounded to last 100 entries, oldest pruned FIFO.                     |
| `get_admin() -> Address`                                               | view         | —                              | Returns configured admin.                                            |

Errors: `NotInitialized`, `AlreadyInitialized`, `NotAuthorized`, `ZeroWeight`.

### `paluwagan` — `PaluwaganContract`

| Function                                                                                       | Auth                   | Emits                         | Notes                                                                                                  |
|------------------------------------------------------------------------------------------------|------------------------|-------------------------------|--------------------------------------------------------------------------------------------------------|
| `init_round(organizer, members: Vec<Address>, amount: i128, cycles: u32, cycle_seconds: u64)`  | `organizer`            | `("pal","init")`              | `members.len() == cycles`, all positive. Sets `start_ts = ledger.timestamp`.                           |
| `contribute(member: Address, cycle: u32)`                                                      | `member`               | `("pal","contrib")`           | Member must be in roster. Idempotent rejection on double-contribute.                                   |
| `distribute_payout(cycle: u32) -> Address`                                                     | permissionless         | `("pal","payout")`            | Requires cycle deadline reached AND all members contributed. Returns scheduled recipient.              |
| `close_round()`                                                                                | `organizer`            | `("pal","closed")`            | Only after every cycle paid.                                                                           |
| `get_state() -> RoundState`                                                                    | view                   | —                             | Status + per-cycle contributions + payouts.                                                            |

Errors: `NotInitialized`, `AlreadyInitialized`, `NotAuthorized`, `InvalidConfig`, `WrongState`, `MemberNotInRound`, `CycleOutOfRange`, `AlreadyContributed`, `CycleNotReady`, `AlreadyDistributed`, `CyclesRemaining`.

Recipient schedule: `members[cycle - 1]` receives the cycle-N payout. Position == enrollment order.

## Storage

| Layer        | Used for                                                              |
|--------------|-----------------------------------------------------------------------|
| `instance`   | Reputation: admin. Paluwagan: round `Config` (immutable post-init except `status`). |
| `persistent` | Reputation: per-member `MemberRecord`. Paluwagan: per-cycle contributors + payout flag. |
| `temporary`  | Not used; all data must survive cycle boundaries.                     |

## Deploy

```bash
# One-shot, idempotent. Re-run skips already-deployed contracts unless --force.
scripts/deploy_testnet.sh
scripts/deploy_testnet.sh --force   # forces redeploy
```

Requirements: `stellar` CLI (>= 22) and `jq`. The script bootstraps a `damay-deployer` testnet identity via friendbot on first run.

After deploy, the script writes IDs and wasm hashes to `/deployments.json` at repo root.

## Example invocations

After `deploy_testnet.sh` populates `deployments.json`:

```bash
REPUTATION_ID="$(jq -r .contracts.reputation.id deployments.json)"
PALUWAGAN_ID="$(jq -r .contracts.paluwagan.id deployments.json)"
DEPLOYER="$(stellar keys address damay-deployer)"

# Record a contribution for a member (admin-signed).
stellar contract invoke \
  --id "$REPUTATION_ID" --source damay-deployer --network testnet \
  -- record_contribution \
  --member "$DEPLOYER" \
  --weight 1

# Read the score.
stellar contract invoke \
  --id "$REPUTATION_ID" --network testnet \
  -- get_score --member "$DEPLOYER"
```

For a Paluwagan round (typically the backend deploys a fresh contract per round, but the same WASM is reused via `stellar contract deploy --wasm-hash`):

```bash
stellar contract invoke \
  --id "$PALUWAGAN_ID" --source damay-deployer --network testnet \
  -- init_round \
  --organizer "$DEPLOYER" \
  --members '["G...A","G...B","G...C"]' \
  --amount 500 \
  --cycles 3 \
  --cycle_seconds 604800   # 1 week
```

## Test inventory

- `reputation`: 18 tests — init guards, weight branches, decay over time, history cap + ordering, saturating math, event emission, all error paths.
- `paluwagan`: 30 tests — every state transition, every error variant, plus an end-to-end 3-member / 3-cycle round.

```bash
cargo test --all
```

## Security notes (CLAUDE.md §14)

- Every state-mutating function calls `require_auth` on the appropriate principal (admin / organizer / member).
- All arithmetic uses `saturating_*` — no panics on adversarial input.
- No `unwrap()` on user-supplied data; errors surfaced via the typed `Error` enum.
- Reputation history is bounded (100 entries / member) to prevent storage griefing.
- Contracts have no re-entry surface: no cross-contract calls are made from mutating paths.
