//! DAMAY contract fuzz tests.
//!
//! 500 random invocation sequences per contract. Goals:
//!   * No actual panics or unwinds (test harness would catch those).
//!   * Invariants hold (history bounded, recipient ∈ roster, no double-distribute,
//!     no double-contribute, no contribute after distribute, no close before
//!     all cycles paid, status monotonicity).
//!
//! Plain xorshift PRNG with fixed per-iteration seeds keeps the suite
//! deterministic (no `proptest` dependency needed; soroban-sdk's `Env`
//! lifetime makes proptest's shrinking awkward to compose anyway).
//!
//! Error matching is intentionally **coarse**: from an external crate the
//! `try_*` client methods collapse contract errors into a generic outer
//! `Err(_)`. We treat any `Err` as "the contract chose to error" — which is
//! correct behaviour for fuzz; variant-level coverage already lives in the
//! per-crate `src/test.rs` modules. The fuzz target's job is to confirm no
//! invocation sequence panics or violates the structural invariants.

#![cfg(test)]

use damay_paluwagan::{PaluwaganContract, PaluwaganContractClient, Status};
use damay_reputation::{HISTORY_LIMIT, ReputationContract, ReputationContractClient};
use soroban_sdk::{
    testutils::{Address as _, Ledger},
    Address, Env, Vec,
};

// Soroban contracts are `#![no_std]`; pull in `alloc` for tracking sets.
extern crate alloc;

/// xorshift64* PRNG — deterministic, no extra deps.
struct Rng(u64);

impl Rng {
    fn new(seed: u64) -> Self {
        Self(if seed == 0 { 0x9E3779B97F4A7C15 } else { seed })
    }
    fn next_u64(&mut self) -> u64 {
        let mut x = self.0;
        x ^= x << 13;
        x ^= x >> 7;
        x ^= x << 17;
        self.0 = x;
        x
    }
    fn range(&mut self, lo: u32, hi_exclusive: u32) -> u32 {
        assert!(hi_exclusive > lo);
        lo + (self.next_u64() as u32 % (hi_exclusive - lo))
    }
}

const ITERATIONS: usize = 500;

/// True iff `try_*` returned a successful contract call (`Ok(Ok(_))`).
fn ok<T, E1, E2>(r: &Result<Result<T, E1>, E2>) -> bool {
    matches!(r, Ok(Ok(_)))
}

// ---------------------------------------------------------------------------
// Reputation contract fuzz
// ---------------------------------------------------------------------------

#[test]
fn reputation_fuzz_no_panics_history_bounded() {
    for iter in 0..ITERATIONS {
        let seed = 0xC0FFEE_u64.wrapping_add((iter as u64).wrapping_mul(0x9E3779B1));
        let mut rng = Rng::new(seed);

        let env = Env::default();
        env.mock_all_auths();
        let start_ts = 1_000_000u64 + (rng.next_u64() % 10_000_000);
        env.ledger().with_mut(|l| l.timestamp = start_ts);

        let cid = env.register(ReputationContract, ());
        let client = ReputationContractClient::new(&env, &cid);
        let admin = Address::generate(&env);

        let init_first = rng.next_u64() & 1 == 0;
        let mut initialized = false;
        if init_first {
            client.init(&admin);
            initialized = true;
        }

        let pool_size = rng.range(1, 5) as usize;
        let mut members: alloc::vec::Vec<Address> = alloc::vec::Vec::with_capacity(pool_size);
        for _ in 0..pool_size {
            members.push(Address::generate(&env));
        }

        let steps = rng.range(1, 32);
        for _ in 0..steps {
            if !initialized && rng.next_u64() & 0b11 == 0 {
                client.init(&admin);
                initialized = true;
            }

            if rng.next_u64() & 0b11 == 0 {
                let adv = (rng.next_u64() % (60 * 24 * 60 * 60)) + 1;
                env.ledger()
                    .with_mut(|l| l.timestamp = l.timestamp.saturating_add(adv));
            }

            let op = rng.range(0, 6);
            let member = &members[rng.range(0, pool_size as u32) as usize];
            let weight = rng.range(0, 5); // include 0 → ZeroWeight path

            match op {
                0 => {
                    let r = client.try_record_contribution(member, &weight);
                    if ok(&r) {
                        // Successful contribution requires init AND non-zero weight.
                        assert!(initialized);
                        assert!(weight > 0);
                    }
                }
                1 => {
                    let r = client.try_record_default(member, &weight);
                    if ok(&r) {
                        assert!(initialized);
                        assert!(weight > 0);
                    }
                }
                2 => {
                    let r = client.try_record_payout_received(member);
                    if ok(&r) {
                        assert!(initialized);
                    }
                }
                3 => {
                    // Total function — must never panic, even pre-init.
                    let _ = client.get_score(member);
                }
                4 => {
                    let hist = client.get_history(member);
                    assert!(
                        hist.len() <= HISTORY_LIMIT,
                        "history grew past HISTORY_LIMIT: {}",
                        hist.len()
                    );
                }
                _ => {
                    let _ = client.try_get_admin();
                }
            }
        }

        // Final sweep: bounded history, sane score envelope.
        for m in &members {
            let h = client.get_history(m);
            assert!(h.len() <= HISTORY_LIMIT);
            let s = client.get_score(m);
            assert!(
                s > i64::MIN / 2 && s < i64::MAX / 2,
                "score outside half-range: {}",
                s
            );
        }
    }
}

// ---------------------------------------------------------------------------
// Paluwagan contract fuzz
// ---------------------------------------------------------------------------

#[test]
fn paluwagan_fuzz_no_panics_invariants_hold() {
    for iter in 0..ITERATIONS {
        let seed = 0xBADBEEF_u64.wrapping_add((iter as u64).wrapping_mul(0x1234_5678_9ABC));
        let mut rng = Rng::new(seed);

        let env = Env::default();
        env.mock_all_auths();
        let start_ts = 2_000_000u64 + (rng.next_u64() % 1_000_000);
        env.ledger().with_mut(|l| l.timestamp = start_ts);

        let cid = env.register(PaluwaganContract, ());
        let client = PaluwaganContractClient::new(&env, &cid);

        let cycles = rng.range(2, 6);
        let cycle_seconds = (rng.next_u64() % 1000 + 1) as u64;
        let amount: i128 = (rng.next_u64() % 10_000 + 1) as i128;

        let organizer = Address::generate(&env);
        let mut roster: alloc::vec::Vec<Address> = alloc::vec::Vec::with_capacity(cycles as usize);
        for _ in 0..cycles {
            roster.push(Address::generate(&env));
        }
        let members_vec: Vec<Address> = {
            let mut v = Vec::new(&env);
            for m in &roster {
                v.push_back(m.clone());
            }
            v
        };

        let init_now = rng.next_u64() & 1 == 0;
        let mut initialized = false;
        if init_now {
            let r = client.try_init_round(
                &organizer,
                &members_vec,
                &amount,
                &cycles,
                &cycle_seconds,
            );
            assert!(ok(&r), "init_round failed with valid config");
            initialized = true;
        }

        // Track expected state for invariants.
        let mut paid_cycles: alloc::collections::BTreeSet<u32> =
            alloc::collections::BTreeSet::new();
        let mut contributors_per_cycle: alloc::collections::BTreeMap<
            u32,
            alloc::collections::BTreeSet<usize>,
        > = alloc::collections::BTreeMap::new();
        let mut closed = false;

        let steps = rng.range(4, 40);
        for _ in 0..steps {
            if rng.next_u64() & 1 == 0 {
                let adv = (rng.next_u64() % (cycle_seconds * 2 + 1)) + 1;
                env.ledger()
                    .with_mut(|l| l.timestamp = l.timestamp.saturating_add(adv));
            }

            let op = rng.range(0, 4);
            match op {
                0 => {
                    let cycle = rng.range(0, cycles + 2);
                    let pick_outsider = rng.next_u64() & 0b111 == 0;
                    let member = if pick_outsider {
                        Address::generate(&env)
                    } else {
                        roster[rng.range(0, cycles) as usize].clone()
                    };
                    let r = client.try_contribute(&member, &cycle);
                    if ok(&r) {
                        assert!(initialized, "contribute succeeded pre-init");
                        assert!(!closed, "contribute succeeded after close");
                        assert!(cycle >= 1 && cycle <= cycles);
                        assert!(
                            !paid_cycles.contains(&cycle),
                            "contribute succeeded after payout for cycle {}",
                            cycle
                        );
                        let idx = roster.iter().position(|a| a == &member).expect(
                            "successful contribute by non-roster member",
                        );
                        let set = contributors_per_cycle.entry(cycle).or_default();
                        assert!(set.insert(idx), "double-contribute slipped through");
                    }
                }
                1 => {
                    let cycle = rng.range(0, cycles + 2);
                    let r = client.try_distribute_payout(&cycle);
                    if let Ok(Ok(recipient)) = r {
                        assert!(initialized);
                        assert!(!closed);
                        assert!(cycle >= 1 && cycle <= cycles);
                        assert!(
                            roster.contains(&recipient),
                            "distribute_payout returned non-member"
                        );
                        assert!(
                            paid_cycles.insert(cycle),
                            "double-distribute for cycle {}",
                            cycle
                        );
                        let set = contributors_per_cycle
                            .get(&cycle)
                            .cloned()
                            .unwrap_or_default();
                        assert_eq!(
                            set.len() as u32,
                            cycles,
                            "payout fired with incomplete contributions"
                        );
                    }
                }
                2 => {
                    let r = client.try_close_round();
                    if ok(&r) {
                        assert!(initialized);
                        assert!(!closed);
                        assert_eq!(
                            paid_cycles.len() as u32,
                            cycles,
                            "close_round succeeded with unpaid cycles"
                        );
                        closed = true;
                    }
                }
                _ => {
                    let r = client.try_get_state();
                    if let Ok(Ok(state)) = &r {
                        assert_eq!(state.cycles, cycles);
                        if closed {
                            assert_eq!(state.status, Status::Completed);
                        }
                    }
                }
            }
        }
    }
}
