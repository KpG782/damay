#![no_std]
//! DAMAY Reputation Trustline.
//!
//! Portable per-member reputation score. Designed to be read by any future
//! DAMAY product (Paluwagan today, Late-Night Lend tomorrow) so reputation is
//! reusable, not siloed per round.
//!
//! Storage:
//! - `instance` — admin (single allowed writer), config.
//! - `persistent` — per-member raw cumulative score + bounded history.
//!
//! Score formula (CLAUDE.md §6):
//!   +10  per on-time contribution
//!   -25  per default
//!   +1   per payout received
//!   Decay: -1% per 30 days, applied at read time on the raw score.

use soroban_sdk::{
    contract, contracterror, contractimpl, contracttype, symbol_short, Address, Env, Symbol, Vec,
};

// ---------------------------------------------------------------------------
// Constants
// ---------------------------------------------------------------------------

/// Maximum entries kept in a member's history. Older entries are pruned FIFO.
pub const HISTORY_LIMIT: u32 = 100;

/// Score weights (CLAUDE.md §6).
const WEIGHT_CONTRIBUTION: i64 = 10;
const WEIGHT_DEFAULT: i64 = -25;
const WEIGHT_PAYOUT: i64 = 1;

/// Decay: 1% per 30 days, applied at read-time.
const DECAY_NUM: i64 = 99;
const DECAY_DEN: i64 = 100;
const DECAY_PERIOD_SECS: u64 = 30 * 24 * 60 * 60; // 30 days

/// TTL bumps. Instance is small + read constantly; persistent per-member
/// is read by API + frontend on demand. Both bumped on write.
const INSTANCE_BUMP_AMOUNT: u32 = 518_400; // ~30 days at 5s ledgers
const INSTANCE_LIFETIME_THRESHOLD: u32 = 518_400 - 86_400;
const PERSISTENT_BUMP_AMOUNT: u32 = 518_400;
const PERSISTENT_LIFETIME_THRESHOLD: u32 = 518_400 - 86_400;

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

#[contracterror]
#[derive(Copy, Clone, Debug, Eq, PartialEq, PartialOrd, Ord)]
#[repr(u32)]
pub enum Error {
    NotInitialized = 1,
    AlreadyInitialized = 2,
    NotAuthorized = 3,
    ZeroWeight = 4,
}

/// Event kind tag stored in a `ReputationEntry`.
#[contracttype]
#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub enum EventKind {
    Contribution = 0,
    Default = 1,
    Payout = 2,
}

#[contracttype]
#[derive(Clone, Debug, Eq, PartialEq)]
pub struct ReputationEntry {
    pub kind: EventKind,
    /// Signed delta applied to the raw cumulative score.
    pub delta: i64,
    /// Ledger timestamp at the time of the entry.
    pub timestamp: u64,
}

#[contracttype]
#[derive(Clone, Debug, Eq, PartialEq)]
pub struct MemberRecord {
    /// Cumulative raw score (no decay applied).
    pub raw_score: i64,
    /// Timestamp of the most recent mutating event. Used as decay anchor.
    pub last_event_ts: u64,
    /// Bounded ring of recent events.
    pub history: Vec<ReputationEntry>,
}

/// Instance storage keys.
#[contracttype]
enum DataKey {
    Admin,
    /// Persistent storage key per member.
    Member(Address),
}

// ---------------------------------------------------------------------------
// Contract
// ---------------------------------------------------------------------------

#[contract]
pub struct ReputationContract;

#[contractimpl]
impl ReputationContract {
    /// One-time init. Stores admin in instance storage. Admin is the only
    /// principal allowed to call mutating functions (in practice: the DAMAY
    /// backend worker's Stellar account, or the Paluwagan contract itself).
    pub fn init(env: Env, admin: Address) -> Result<(), Error> {
        if env.storage().instance().has(&DataKey::Admin) {
            return Err(Error::AlreadyInitialized);
        }
        admin.require_auth();
        env.storage().instance().set(&DataKey::Admin, &admin);
        env.storage()
            .instance()
            .extend_ttl(INSTANCE_LIFETIME_THRESHOLD, INSTANCE_BUMP_AMOUNT);
        env.events()
            .publish((symbol_short!("rep"), symbol_short!("init")), admin);
        Ok(())
    }

    /// Record an on-time contribution: +10 * weight_multiplier (caller-defined).
    /// `weight` is a multiplier (typically 1). 0 is rejected to keep the
    /// history meaningful.
    pub fn record_contribution(env: Env, member: Address, weight: u32) -> Result<(), Error> {
        if weight == 0 {
            return Err(Error::ZeroWeight);
        }
        let admin = Self::admin(&env)?;
        admin.require_auth();
        let delta = WEIGHT_CONTRIBUTION.saturating_mul(weight as i64);
        Self::apply_event(&env, &member, EventKind::Contribution, delta);
        env.events().publish(
            (symbol_short!("rep"), symbol_short!("contrib")),
            (member, weight),
        );
        Ok(())
    }

    /// Record a default: -25 * weight.
    pub fn record_default(env: Env, member: Address, weight: u32) -> Result<(), Error> {
        if weight == 0 {
            return Err(Error::ZeroWeight);
        }
        let admin = Self::admin(&env)?;
        admin.require_auth();
        let delta = WEIGHT_DEFAULT.saturating_mul(weight as i64);
        Self::apply_event(&env, &member, EventKind::Default, delta);
        env.events().publish(
            (symbol_short!("rep"), symbol_short!("default")),
            (member, weight),
        );
        Ok(())
    }

    /// Record a payout received: +1.
    pub fn record_payout_received(env: Env, member: Address) -> Result<(), Error> {
        let admin = Self::admin(&env)?;
        admin.require_auth();
        Self::apply_event(&env, &member, EventKind::Payout, WEIGHT_PAYOUT);
        env.events()
            .publish((symbol_short!("rep"), symbol_short!("payout")), member);
        Ok(())
    }

    /// Read current score with decay applied against the current ledger
    /// timestamp. Returns 0 if member has no record.
    pub fn get_score(env: Env, member: Address) -> i64 {
        match Self::load_member(&env, &member) {
            None => 0,
            Some(rec) => apply_decay(rec.raw_score, rec.last_event_ts, env.ledger().timestamp()),
        }
    }

    /// Return the bounded history (oldest-first).
    pub fn get_history(env: Env, member: Address) -> Vec<ReputationEntry> {
        match Self::load_member(&env, &member) {
            None => Vec::new(&env),
            Some(rec) => rec.history,
        }
    }

    /// Read the configured admin. Useful for debugging + verifying setup.
    pub fn get_admin(env: Env) -> Result<Address, Error> {
        Self::admin(&env)
    }

    // -----------------------------------------------------------------------
    // Internal helpers
    // -----------------------------------------------------------------------

    fn admin(env: &Env) -> Result<Address, Error> {
        env.storage()
            .instance()
            .get(&DataKey::Admin)
            .ok_or(Error::NotInitialized)
    }

    fn load_member(env: &Env, member: &Address) -> Option<MemberRecord> {
        let key = DataKey::Member(member.clone());
        env.storage().persistent().get(&key)
    }

    fn save_member(env: &Env, member: &Address, rec: &MemberRecord) {
        let key = DataKey::Member(member.clone());
        env.storage().persistent().set(&key, rec);
        env.storage().persistent().extend_ttl(
            &key,
            PERSISTENT_LIFETIME_THRESHOLD,
            PERSISTENT_BUMP_AMOUNT,
        );
    }

    fn apply_event(env: &Env, member: &Address, kind: EventKind, delta: i64) {
        let ts = env.ledger().timestamp();
        let mut rec = Self::load_member(env, member).unwrap_or(MemberRecord {
            raw_score: 0,
            last_event_ts: ts,
            history: Vec::new(env),
        });
        rec.raw_score = rec.raw_score.saturating_add(delta);
        rec.last_event_ts = ts;
        let entry = ReputationEntry { kind, delta, timestamp: ts };
        rec.history.push_back(entry);
        // FIFO prune to keep storage bounded.
        while rec.history.len() > HISTORY_LIMIT {
            rec.history.pop_front();
        }
        Self::save_member(env, member, &rec);
        env.storage()
            .instance()
            .extend_ttl(INSTANCE_LIFETIME_THRESHOLD, INSTANCE_BUMP_AMOUNT);
    }
}

/// Apply 1% / 30-day decay to a raw cumulative score.
///
/// We compute floor((now - last) / 30d) decay periods; each period multiplies
/// the score by 99/100 using saturating integer math. Capped at 240 periods
/// (~20 years) so a never-touched member trends to zero without runaway work.
fn apply_decay(raw_score: i64, last_event_ts: u64, now: u64) -> i64 {
    if raw_score == 0 || now <= last_event_ts {
        return raw_score;
    }
    let elapsed = now - last_event_ts;
    let mut periods = elapsed / DECAY_PERIOD_SECS;
    if periods > 240 {
        periods = 240;
    }
    let mut score = raw_score;
    let mut i: u64 = 0;
    while i < periods && score != 0 {
        score = score.saturating_mul(DECAY_NUM) / DECAY_DEN;
        i += 1;
    }
    score
}

// Re-export common symbols so callers (and the Paluwagan contract) can
// reference them by name.
pub const TOPIC_REP: Symbol = symbol_short!("rep");

#[cfg(test)]
mod test;
