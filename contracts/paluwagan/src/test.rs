#![cfg(test)]

use super::*;
use soroban_sdk::{
    testutils::{Address as _, Ledger},
    vec, Env,
};

struct Ctx {
    env: Env,
    organizer: Address,
    members: Vec<Address>,
    client: PaluwaganContractClient<'static>,
}

fn setup(member_count: u32) -> Ctx {
    let env = Env::default();
    env.mock_all_auths();
    env.ledger().with_mut(|l| l.timestamp = 1_000_000);
    let contract_id = env.register(PaluwaganContract, ());
    let client = PaluwaganContractClient::new(&env, &contract_id);
    let organizer = Address::generate(&env);
    let mut members: Vec<Address> = Vec::new(&env);
    for _ in 0..member_count {
        members.push_back(Address::generate(&env));
    }
    Ctx { env, organizer, members, client }
}

fn init_round(ctx: &Ctx, amount: i128, cycle_seconds: u64) {
    ctx.client.init_round(
        &ctx.organizer,
        &ctx.members,
        &amount,
        &ctx.members.len(),
        &cycle_seconds,
    );
}

// ---------------------------------------------------------------------------
// init_round
// ---------------------------------------------------------------------------

#[test]
fn init_round_happy_path() {
    let ctx = setup(3);
    init_round(&ctx, 500, 7 * 24 * 60 * 60);
    let state = ctx.client.get_state();
    assert_eq!(state.status, Status::Active);
    assert_eq!(state.cycles, 3);
    assert_eq!(state.amount, 500);
    assert_eq!(state.organizer, ctx.organizer);
}

#[test]
fn init_twice_errors() {
    let ctx = setup(3);
    init_round(&ctx, 500, 100);
    let r = ctx
        .client
        .try_init_round(&ctx.organizer, &ctx.members, &500i128, &3u32, &100u64);
    assert!(matches!(r, Err(Ok(Error::AlreadyInitialized))));
}

#[test]
fn init_with_zero_cycles_errors() {
    let ctx = setup(0);
    let r = ctx
        .client
        .try_init_round(&ctx.organizer, &ctx.members, &500i128, &0u32, &100u64);
    assert!(matches!(r, Err(Ok(Error::InvalidConfig))));
}

#[test]
fn init_with_zero_cycle_seconds_errors() {
    let ctx = setup(2);
    let r = ctx
        .client
        .try_init_round(&ctx.organizer, &ctx.members, &500i128, &2u32, &0u64);
    assert!(matches!(r, Err(Ok(Error::InvalidConfig))));
}

#[test]
fn init_with_zero_amount_errors() {
    let ctx = setup(2);
    let r = ctx
        .client
        .try_init_round(&ctx.organizer, &ctx.members, &0i128, &2u32, &100u64);
    assert!(matches!(r, Err(Ok(Error::InvalidConfig))));
}

#[test]
fn init_with_member_count_mismatch_errors() {
    let ctx = setup(3);
    let r = ctx
        .client
        .try_init_round(&ctx.organizer, &ctx.members, &500i128, &4u32, &100u64);
    assert!(matches!(r, Err(Ok(Error::InvalidConfig))));
}

// ---------------------------------------------------------------------------
// contribute
// ---------------------------------------------------------------------------

#[test]
fn contribute_happy_path() {
    let ctx = setup(3);
    init_round(&ctx, 500, 100);
    let m0 = ctx.members.get(0).unwrap();
    ctx.client.contribute(&m0, &1);
    let state = ctx.client.get_state();
    let list = state.contributions.get(1).unwrap();
    assert_eq!(list.len(), 1);
    assert_eq!(list.get(0).unwrap(), m0);
}

#[test]
fn contribute_before_init_errors() {
    let env = Env::default();
    env.mock_all_auths();
    let id = env.register(PaluwaganContract, ());
    let client = PaluwaganContractClient::new(&env, &id);
    let m = Address::generate(&env);
    let r = client.try_contribute(&m, &1);
    assert!(matches!(r, Err(Ok(Error::NotInitialized))));
}

#[test]
fn contribute_non_member_errors() {
    let ctx = setup(3);
    init_round(&ctx, 500, 100);
    let stranger = Address::generate(&ctx.env);
    let r = ctx.client.try_contribute(&stranger, &1);
    assert!(matches!(r, Err(Ok(Error::MemberNotInRound))));
}

#[test]
fn contribute_cycle_zero_errors() {
    let ctx = setup(3);
    init_round(&ctx, 500, 100);
    let r = ctx.client.try_contribute(&ctx.members.get(0).unwrap(), &0);
    assert!(matches!(r, Err(Ok(Error::CycleOutOfRange))));
}

#[test]
fn contribute_cycle_too_large_errors() {
    let ctx = setup(3);
    init_round(&ctx, 500, 100);
    let r = ctx.client.try_contribute(&ctx.members.get(0).unwrap(), &99);
    assert!(matches!(r, Err(Ok(Error::CycleOutOfRange))));
}

#[test]
fn double_contribute_errors() {
    let ctx = setup(3);
    init_round(&ctx, 500, 100);
    let m0 = ctx.members.get(0).unwrap();
    ctx.client.contribute(&m0, &1);
    let r = ctx.client.try_contribute(&m0, &1);
    assert!(matches!(r, Err(Ok(Error::AlreadyContributed))));
}

#[test]
fn contribute_after_payout_errors() {
    let ctx = setup(2);
    init_round(&ctx, 500, 100);
    // All members contribute cycle 1.
    let m0 = ctx.members.get(0).unwrap();
    let m1 = ctx.members.get(1).unwrap();
    ctx.client.contribute(&m0, &1);
    ctx.client.contribute(&m1, &1);
    // Move past deadline + distribute.
    ctx.env.ledger().with_mut(|l| l.timestamp = 1_000_000 + 200);
    ctx.client.distribute_payout(&1);
    // Now a fresh "contribution" to cycle 1 must fail.
    let stray = Address::generate(&ctx.env); // not a member anyway
    let r = ctx.client.try_contribute(&stray, &1);
    // First failure trigger could be MemberNotInRound; use a real member:
    assert!(matches!(r, Err(Ok(Error::MemberNotInRound))));
    // For a real member, AlreadyContributed would fire because they already
    // contributed; instead test by using a fresh round where one member
    // didn't contribute (covered in `contribute_after_payout_real_member`).
}

#[test]
fn contribute_after_payout_real_member() {
    // Spin up a 3-member round, only 2 contribute, manually mark payout to
    // simulate distribute_payout — but distribute_payout requires complete
    // contributions, so we exercise this path via the storage manually:
    // simpler — test the AlreadyDistributed branch directly by setting the flag.
    let ctx = setup(3);
    init_round(&ctx, 500, 100);
    // All three contribute.
    for i in 0..3u32 {
        ctx.client.contribute(&ctx.members.get(i).unwrap(), &1);
    }
    ctx.env.ledger().with_mut(|l| l.timestamp = 1_000_000 + 200);
    ctx.client.distribute_payout(&1);
    // Now a member trying to contribute to that already-paid cycle should fail.
    // Pick a member who hasn't contributed by using a fresh cycle? No, cycle 1 is paid.
    // The members all contributed in cycle 1, so re-contribute would hit AlreadyContributed first.
    // To hit AlreadyDistributed we need a member who is in the list but hasn't yet contributed.
    // Build a separate round to isolate the branch.
    let ctx2 = setup(2);
    init_round(&ctx2, 500, 100);
    let m0 = ctx2.members.get(0).unwrap();
    let m1 = ctx2.members.get(1).unwrap();
    ctx2.client.contribute(&m0, &1);
    ctx2.client.contribute(&m1, &1);
    ctx2.env.ledger().with_mut(|l| l.timestamp = 1_000_000 + 200);
    ctx2.client.distribute_payout(&1);
    // Now have m0 try to contribute to cycle 1 again -> double contribute fires
    // BEFORE the payout check; but the payout check ordering is BEFORE
    // double-contribute check. Verify the contract's actual ordering: code
    // checks payout flag first, so AlreadyDistributed should win.
    let r = ctx2.client.try_contribute(&m0, &1);
    assert!(matches!(r, Err(Ok(Error::AlreadyDistributed))));
}

#[test]
fn contribute_when_completed_errors() {
    let ctx = setup(1);
    init_round(&ctx, 500, 100);
    let m0 = ctx.members.get(0).unwrap();
    ctx.client.contribute(&m0, &1);
    ctx.env.ledger().with_mut(|l| l.timestamp = 1_000_000 + 200);
    ctx.client.distribute_payout(&1);
    ctx.client.close_round();
    let r = ctx.client.try_contribute(&m0, &1);
    assert!(matches!(r, Err(Ok(Error::WrongState))));
}

// ---------------------------------------------------------------------------
// distribute_payout
// ---------------------------------------------------------------------------

#[test]
fn distribute_payout_happy_path_returns_recipient() {
    let ctx = setup(3);
    init_round(&ctx, 500, 100);
    for i in 0..3u32 {
        ctx.client.contribute(&ctx.members.get(i).unwrap(), &1);
    }
    ctx.env.ledger().with_mut(|l| l.timestamp = 1_000_000 + 200);
    let recipient = ctx.client.distribute_payout(&1);
    assert_eq!(recipient, ctx.members.get(0).unwrap());
}

#[test]
fn distribute_before_deadline_errors() {
    let ctx = setup(2);
    init_round(&ctx, 500, 1000);
    ctx.client.contribute(&ctx.members.get(0).unwrap(), &1);
    ctx.client.contribute(&ctx.members.get(1).unwrap(), &1);
    // Still well before deadline.
    let r = ctx.client.try_distribute_payout(&1);
    assert!(matches!(r, Err(Ok(Error::CycleNotReady))));
}

#[test]
fn distribute_with_incomplete_contribs_errors() {
    let ctx = setup(3);
    init_round(&ctx, 500, 100);
    ctx.client.contribute(&ctx.members.get(0).unwrap(), &1);
    // only 1 of 3 contributed.
    ctx.env.ledger().with_mut(|l| l.timestamp = 1_000_000 + 200);
    let r = ctx.client.try_distribute_payout(&1);
    assert!(matches!(r, Err(Ok(Error::CycleNotReady))));
}

#[test]
fn distribute_twice_errors() {
    let ctx = setup(2);
    init_round(&ctx, 500, 100);
    ctx.client.contribute(&ctx.members.get(0).unwrap(), &1);
    ctx.client.contribute(&ctx.members.get(1).unwrap(), &1);
    ctx.env.ledger().with_mut(|l| l.timestamp = 1_000_000 + 200);
    ctx.client.distribute_payout(&1);
    let r = ctx.client.try_distribute_payout(&1);
    assert!(matches!(r, Err(Ok(Error::AlreadyDistributed))));
}

#[test]
fn distribute_before_init_errors() {
    let env = Env::default();
    env.mock_all_auths();
    let id = env.register(PaluwaganContract, ());
    let client = PaluwaganContractClient::new(&env, &id);
    let r = client.try_distribute_payout(&1);
    assert!(matches!(r, Err(Ok(Error::NotInitialized))));
}

#[test]
fn distribute_cycle_out_of_range() {
    let ctx = setup(2);
    init_round(&ctx, 500, 100);
    let r0 = ctx.client.try_distribute_payout(&0);
    assert!(matches!(r0, Err(Ok(Error::CycleOutOfRange))));
    let r2 = ctx.client.try_distribute_payout(&99);
    assert!(matches!(r2, Err(Ok(Error::CycleOutOfRange))));
}

#[test]
fn distribute_when_completed_errors() {
    let ctx = setup(1);
    init_round(&ctx, 500, 100);
    ctx.client.contribute(&ctx.members.get(0).unwrap(), &1);
    ctx.env.ledger().with_mut(|l| l.timestamp = 1_000_000 + 200);
    ctx.client.distribute_payout(&1);
    ctx.client.close_round();
    let r = ctx.client.try_distribute_payout(&1);
    assert!(matches!(r, Err(Ok(Error::WrongState))));
}

// ---------------------------------------------------------------------------
// close_round
// ---------------------------------------------------------------------------

#[test]
fn close_round_happy_path() {
    let ctx = setup(1);
    init_round(&ctx, 500, 100);
    ctx.client.contribute(&ctx.members.get(0).unwrap(), &1);
    ctx.env.ledger().with_mut(|l| l.timestamp = 1_000_000 + 200);
    ctx.client.distribute_payout(&1);
    ctx.client.close_round();
    let state = ctx.client.get_state();
    assert_eq!(state.status, Status::Completed);
}

#[test]
fn close_round_with_cycles_remaining_errors() {
    let ctx = setup(2);
    init_round(&ctx, 500, 100);
    // No payouts done.
    let r = ctx.client.try_close_round();
    assert!(matches!(r, Err(Ok(Error::CyclesRemaining))));
}

#[test]
fn close_round_already_completed_errors() {
    let ctx = setup(1);
    init_round(&ctx, 500, 100);
    ctx.client.contribute(&ctx.members.get(0).unwrap(), &1);
    ctx.env.ledger().with_mut(|l| l.timestamp = 1_000_000 + 200);
    ctx.client.distribute_payout(&1);
    ctx.client.close_round();
    let r = ctx.client.try_close_round();
    assert!(matches!(r, Err(Ok(Error::WrongState))));
}

#[test]
fn close_before_init_errors() {
    let env = Env::default();
    env.mock_all_auths();
    let id = env.register(PaluwaganContract, ());
    let client = PaluwaganContractClient::new(&env, &id);
    let r = client.try_close_round();
    assert!(matches!(r, Err(Ok(Error::NotInitialized))));
}

// ---------------------------------------------------------------------------
// get_state
// ---------------------------------------------------------------------------

#[test]
fn get_state_before_init_errors() {
    let env = Env::default();
    let id = env.register(PaluwaganContract, ());
    let client = PaluwaganContractClient::new(&env, &id);
    let r = client.try_get_state();
    assert!(matches!(r, Err(Ok(Error::NotInitialized))));
}

#[test]
fn get_state_current_cycle_advances_with_time() {
    let ctx = setup(3);
    init_round(&ctx, 500, 100);
    // at t = start, cycle = 1
    let s1 = ctx.client.get_state();
    assert_eq!(s1.current_cycle, 1);
    ctx.env.ledger().with_mut(|l| l.timestamp = 1_000_000 + 150);
    let s2 = ctx.client.get_state();
    assert_eq!(s2.current_cycle, 2);
    // Way past — capped at cycles.
    ctx.env.ledger().with_mut(|l| l.timestamp = 1_000_000 + 100_000);
    let s3 = ctx.client.get_state();
    assert_eq!(s3.current_cycle, 3);
}

// ---------------------------------------------------------------------------
// End-to-end: 3-member round, 3 cycles, full contribute + payout.
// ---------------------------------------------------------------------------

#[test]
fn e2e_three_cycle_round() {
    let ctx = setup(3);
    let cycle_secs = 100u64;
    init_round(&ctx, 500, cycle_secs);
    let m = [
        ctx.members.get(0).unwrap(),
        ctx.members.get(1).unwrap(),
        ctx.members.get(2).unwrap(),
    ];
    for cycle in 1u32..=3 {
        for member in m.iter() {
            ctx.client.contribute(member, &cycle);
        }
        // Advance past this cycle's deadline.
        ctx.env
            .ledger()
            .with_mut(|l| l.timestamp = 1_000_000 + (cycle as u64) * cycle_secs + 1);
        let recipient = ctx.client.distribute_payout(&cycle);
        assert_eq!(recipient, m[(cycle - 1) as usize]);
    }
    ctx.client.close_round();
    let state = ctx.client.get_state();
    assert_eq!(state.status, Status::Completed);
    // Every cycle paid.
    for cycle in 1u32..=3 {
        assert_eq!(state.payouts.get(cycle).unwrap(), true);
        assert_eq!(state.contributions.get(cycle).unwrap().len(), 3);
    }
}

#[test]
fn vec_macro_compiles_smoke() {
    // Just exercise soroban_sdk::vec! once for coverage of imports.
    let env = Env::default();
    let v: Vec<u32> = vec![&env, 1, 2, 3];
    assert_eq!(v.len(), 3);
}
