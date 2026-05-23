#![cfg(test)]

use super::*;
use soroban_sdk::{
    testutils::{Address as _, Events, Ledger},
    Env,
};

fn setup() -> (Env, Address, ReputationContractClient<'static>) {
    let env = Env::default();
    env.mock_all_auths();
    let contract_id = env.register(ReputationContract, ());
    let client = ReputationContractClient::new(&env, &contract_id);
    let admin = Address::generate(&env);
    client.init(&admin);
    (env, admin, client)
}

#[test]
fn init_sets_admin() {
    let (_env, admin, client) = setup();
    assert_eq!(client.get_admin(), admin);
}

#[test]
fn init_twice_errors() {
    let env = Env::default();
    env.mock_all_auths();
    let id = env.register(ReputationContract, ());
    let client = ReputationContractClient::new(&env, &id);
    let admin = Address::generate(&env);
    client.init(&admin);
    let again = Address::generate(&env);
    let res = client.try_init(&again);
    assert!(matches!(res, Err(Ok(Error::AlreadyInitialized))));
}

#[test]
fn get_admin_before_init_errors() {
    let env = Env::default();
    let id = env.register(ReputationContract, ());
    let client = ReputationContractClient::new(&env, &id);
    let res = client.try_get_admin();
    assert!(matches!(res, Err(Ok(Error::NotInitialized))));
}

#[test]
fn record_contribution_increments_score_and_history() {
    let (env, _admin, client) = setup();
    let member = Address::generate(&env);
    client.record_contribution(&member, &1);
    assert_eq!(client.get_score(&member), 10);
    let history = client.get_history(&member);
    assert_eq!(history.len(), 1);
    let entry = history.get(0).unwrap();
    assert_eq!(entry.kind, EventKind::Contribution);
    assert_eq!(entry.delta, 10);
}

#[test]
fn record_default_decrements_score() {
    let (env, _admin, client) = setup();
    let member = Address::generate(&env);
    client.record_contribution(&member, &1);
    client.record_default(&member, &1);
    assert_eq!(client.get_score(&member), 10 - 25);
}

#[test]
fn record_payout_received_adds_one() {
    let (env, _admin, client) = setup();
    let member = Address::generate(&env);
    client.record_payout_received(&member);
    assert_eq!(client.get_score(&member), 1);
    let hist = client.get_history(&member);
    assert_eq!(hist.get(0).unwrap().kind, EventKind::Payout);
}

#[test]
fn unknown_member_score_is_zero() {
    let (env, _admin, client) = setup();
    let stranger = Address::generate(&env);
    assert_eq!(client.get_score(&stranger), 0);
    assert_eq!(client.get_history(&stranger).len(), 0);
}

#[test]
fn weight_multiplier_applies() {
    let (env, _admin, client) = setup();
    let member = Address::generate(&env);
    client.record_contribution(&member, &3);
    assert_eq!(client.get_score(&member), 30);
    client.record_default(&member, &2);
    assert_eq!(client.get_score(&member), 30 - 50);
}

#[test]
fn zero_weight_contribution_errors() {
    let (env, _admin, client) = setup();
    let member = Address::generate(&env);
    let res = client.try_record_contribution(&member, &0);
    assert!(matches!(res, Err(Ok(Error::ZeroWeight))));
}

#[test]
fn zero_weight_default_errors() {
    let (env, _admin, client) = setup();
    let member = Address::generate(&env);
    let res = client.try_record_default(&member, &0);
    assert!(matches!(res, Err(Ok(Error::ZeroWeight))));
}

#[test]
fn mutating_calls_before_init_error() {
    let env = Env::default();
    env.mock_all_auths();
    let id = env.register(ReputationContract, ());
    let client = ReputationContractClient::new(&env, &id);
    let member = Address::generate(&env);
    let r1 = client.try_record_contribution(&member, &1);
    assert!(matches!(r1, Err(Ok(Error::NotInitialized))));
    let r2 = client.try_record_default(&member, &1);
    assert!(matches!(r2, Err(Ok(Error::NotInitialized))));
    let r3 = client.try_record_payout_received(&member);
    assert!(matches!(r3, Err(Ok(Error::NotInitialized))));
}

#[test]
fn decay_applies_after_30d() {
    let (env, _admin, client) = setup();
    let member = Address::generate(&env);
    env.ledger().with_mut(|l| l.timestamp = 1_000_000);
    client.record_contribution(&member, &10); // raw +100
    assert_eq!(client.get_score(&member), 100);
    // Advance 30 days -> one decay period -> 99.
    env.ledger()
        .with_mut(|l| l.timestamp = 1_000_000 + 30 * 24 * 60 * 60);
    assert_eq!(client.get_score(&member), 99);
    // 60 days total -> two periods -> floor(99*99/100)=98 then floor(98*99/100)=97...
    env.ledger()
        .with_mut(|l| l.timestamp = 1_000_000 + 60 * 24 * 60 * 60);
    let s = client.get_score(&member);
    assert!(s <= 98 && s >= 96, "expected ~97-98 got {}", s);
}

#[test]
fn decay_does_not_amplify_negative_scores_unexpectedly() {
    // Decay shrinks magnitude toward zero in both directions.
    let (env, _admin, client) = setup();
    let member = Address::generate(&env);
    env.ledger().with_mut(|l| l.timestamp = 1_000_000);
    client.record_default(&member, &4); // raw -100
    assert_eq!(client.get_score(&member), -100);
    env.ledger()
        .with_mut(|l| l.timestamp = 1_000_000 + 30 * 24 * 60 * 60);
    assert_eq!(client.get_score(&member), -99);
}

#[test]
fn decay_no_op_when_time_not_advanced() {
    let (env, _admin, client) = setup();
    let member = Address::generate(&env);
    env.ledger().with_mut(|l| l.timestamp = 1_000_000);
    client.record_contribution(&member, &1);
    // Same timestamp + reading -> no decay.
    assert_eq!(client.get_score(&member), 10);
}

#[test]
fn history_is_capped_at_limit() {
    let (env, _admin, client) = setup();
    let member = Address::generate(&env);
    for i in 0..(HISTORY_LIMIT + 5) {
        env.ledger().with_mut(|l| l.timestamp = 1000 + i as u64);
        client.record_contribution(&member, &1);
    }
    let hist = client.get_history(&member);
    assert_eq!(hist.len(), HISTORY_LIMIT);
    // Oldest pruned: first surviving entry's timestamp should be the 6th written (index 5).
    let first = hist.get(0).unwrap();
    assert_eq!(first.timestamp, 1000 + 5);
}

#[test]
fn history_order_is_chronological() {
    let (env, _admin, client) = setup();
    let member = Address::generate(&env);
    env.ledger().with_mut(|l| l.timestamp = 100);
    client.record_contribution(&member, &1);
    env.ledger().with_mut(|l| l.timestamp = 200);
    client.record_default(&member, &1);
    env.ledger().with_mut(|l| l.timestamp = 300);
    client.record_payout_received(&member);
    let h = client.get_history(&member);
    assert_eq!(h.len(), 3);
    assert_eq!(h.get(0).unwrap().kind, EventKind::Contribution);
    assert_eq!(h.get(1).unwrap().kind, EventKind::Default);
    assert_eq!(h.get(2).unwrap().kind, EventKind::Payout);
}

#[test]
fn saturating_math_does_not_panic_on_huge_weights() {
    // Even if a buggy caller passes u32::MAX repeatedly, we should not panic.
    let (env, _admin, client) = setup();
    let member = Address::generate(&env);
    for _ in 0..5 {
        client.record_contribution(&member, &u32::MAX);
    }
    // Score is some non-panicking i64 (likely saturated).
    let _ = client.get_score(&member);
}

#[test]
fn events_published_on_each_mutation() {
    // `env.events().all()` returns events from the most recent invocation only.
    // We verify each mutation publishes at least one event by checking after
    // each call.
    let (env, _admin, client) = setup();
    let member = Address::generate(&env);

    client.record_contribution(&member, &1);
    assert!(!env.events().all().is_empty(), "contribution event missing");

    client.record_default(&member, &1);
    assert!(!env.events().all().is_empty(), "default event missing");

    client.record_payout_received(&member);
    assert!(!env.events().all().is_empty(), "payout event missing");
}
