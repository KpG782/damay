#![no_std]
//! DAMAY Paluwagan — rotating savings round state machine.
//!
//! One deployed contract instance == one round. Lifecycle:
//!
//!   Init  --init_round-->  Active  --(all cycles complete)--> Completed
//!                            |
//!                            +-- contribute (per member, per cycle)
//!                            +-- distribute_payout (per cycle, permissionless after deadline)
//!
//! Storage:
//! - `instance`   — round config (organizer, members, amount, cycles, cadence, status, start_ts).
//! - `persistent` — per-cycle contribution sets + payout flags.
//!
//! Auth (CLAUDE.md §6):
//! - `init_round`: organizer.
//! - `contribute`: member (must be in roster).
//! - `distribute_payout`: permissionless, but gated by cycle deadline.
//! - `close_round`: organizer.

use soroban_sdk::{
    contract, contracterror, contractimpl, contracttype, symbol_short, Address, Env, Map, Vec,
};

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
    InvalidConfig = 4,
    WrongState = 5,
    MemberNotInRound = 6,
    CycleOutOfRange = 7,
    AlreadyContributed = 8,
    CycleNotReady = 9,
    AlreadyDistributed = 10,
    CyclesRemaining = 11,
}

#[contracttype]
#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub enum Status {
    Init = 0,
    Active = 1,
    Completed = 2,
}

#[contracttype]
#[derive(Clone, Debug, Eq, PartialEq)]
pub struct Config {
    pub organizer: Address,
    pub members: Vec<Address>,
    pub amount: i128,
    pub cycles: u32,
    pub cycle_seconds: u64,
    pub start_ts: u64,
    pub status: Status,
}

/// Public view of the round, returned by `get_state`.
#[contracttype]
#[derive(Clone, Debug, Eq, PartialEq)]
pub struct RoundState {
    pub status: Status,
    pub current_cycle: u32,
    pub organizer: Address,
    pub members: Vec<Address>,
    pub amount: i128,
    pub cycles: u32,
    pub cycle_seconds: u64,
    pub start_ts: u64,
    /// For each cycle index (1..=cycles), list of members who contributed.
    pub contributions: Map<u32, Vec<Address>>,
    /// For each cycle index, true if payout has been distributed.
    pub payouts: Map<u32, bool>,
}

#[contracttype]
enum DataKey {
    Config,
    /// `Vec<Address>` of contributors for cycle N.
    Contributions(u32),
    /// `bool` (true once distributed) for cycle N.
    Payout(u32),
}

// TTL bumps.
const INSTANCE_BUMP: u32 = 518_400;
const INSTANCE_THRESHOLD: u32 = 518_400 - 86_400;
const PERSISTENT_BUMP: u32 = 518_400;
const PERSISTENT_THRESHOLD: u32 = 518_400 - 86_400;

// ---------------------------------------------------------------------------
// Contract
// ---------------------------------------------------------------------------

#[contract]
pub struct PaluwaganContract;

#[contractimpl]
impl PaluwaganContract {
    /// Initialize the round. Members list also doubles as the payout
    /// schedule: members[i] receives the payout for cycle (i+1).
    pub fn init_round(
        env: Env,
        organizer: Address,
        members: Vec<Address>,
        amount: i128,
        cycles: u32,
        cycle_seconds: u64,
    ) -> Result<(), Error> {
        if env.storage().instance().has(&DataKey::Config) {
            return Err(Error::AlreadyInitialized);
        }
        organizer.require_auth();
        if cycles == 0 || cycle_seconds == 0 || amount <= 0 {
            return Err(Error::InvalidConfig);
        }
        if members.len() != cycles {
            return Err(Error::InvalidConfig);
        }
        let cfg = Config {
            organizer: organizer.clone(),
            members: members.clone(),
            amount,
            cycles,
            cycle_seconds,
            start_ts: env.ledger().timestamp(),
            status: Status::Active,
        };
        env.storage().instance().set(&DataKey::Config, &cfg);
        env.storage()
            .instance()
            .extend_ttl(INSTANCE_THRESHOLD, INSTANCE_BUMP);
        env.events().publish(
            (symbol_short!("pal"), symbol_short!("init")),
            (organizer, amount, cycles),
        );
        Ok(())
    }

    /// Member records a contribution for the given cycle. Cycle must be the
    /// currently-open cycle (or earlier, allowing late contributions until
    /// payout has been distributed).
    pub fn contribute(env: Env, member: Address, cycle: u32) -> Result<(), Error> {
        member.require_auth();
        let cfg = Self::config(&env)?;
        if cfg.status != Status::Active {
            return Err(Error::WrongState);
        }
        if cycle == 0 || cycle > cfg.cycles {
            return Err(Error::CycleOutOfRange);
        }
        if !contains(&cfg.members, &member) {
            return Err(Error::MemberNotInRound);
        }
        // Cannot contribute to a cycle that has already been paid out.
        let payout_key = DataKey::Payout(cycle);
        if env
            .storage()
            .persistent()
            .get::<_, bool>(&payout_key)
            .unwrap_or(false)
        {
            return Err(Error::AlreadyDistributed);
        }
        let key = DataKey::Contributions(cycle);
        let mut list: Vec<Address> = env
            .storage()
            .persistent()
            .get(&key)
            .unwrap_or_else(|| Vec::new(&env));
        if contains(&list, &member) {
            return Err(Error::AlreadyContributed);
        }
        list.push_back(member.clone());
        env.storage().persistent().set(&key, &list);
        env.storage()
            .persistent()
            .extend_ttl(&key, PERSISTENT_THRESHOLD, PERSISTENT_BUMP);
        env.events().publish(
            (symbol_short!("pal"), symbol_short!("contrib")),
            (member, cycle),
        );
        Ok(())
    }

    /// Permissionless: distribute a cycle's payout to its scheduled
    /// recipient. Requires (a) cycle deadline reached, (b) all members
    /// contributed, (c) not already distributed.
    pub fn distribute_payout(env: Env, cycle: u32) -> Result<Address, Error> {
        let cfg = Self::config(&env)?;
        if cfg.status != Status::Active {
            return Err(Error::WrongState);
        }
        if cycle == 0 || cycle > cfg.cycles {
            return Err(Error::CycleOutOfRange);
        }
        let now = env.ledger().timestamp();
        // Deadline for cycle N == start_ts + N * cycle_seconds.
        let deadline = cfg
            .start_ts
            .saturating_add((cycle as u64).saturating_mul(cfg.cycle_seconds));
        if now < deadline {
            return Err(Error::CycleNotReady);
        }
        let payout_key = DataKey::Payout(cycle);
        if env
            .storage()
            .persistent()
            .get::<_, bool>(&payout_key)
            .unwrap_or(false)
        {
            return Err(Error::AlreadyDistributed);
        }
        let contrib_key = DataKey::Contributions(cycle);
        let list: Vec<Address> = env
            .storage()
            .persistent()
            .get(&contrib_key)
            .unwrap_or_else(|| Vec::new(&env));
        if list.len() != cfg.members.len() {
            // Not all members have contributed for this cycle.
            return Err(Error::CycleNotReady);
        }
        // Recipient = members[cycle - 1].
        let recipient = cfg.members.get(cycle - 1).ok_or(Error::CycleOutOfRange)?;
        env.storage().persistent().set(&payout_key, &true);
        env.storage()
            .persistent()
            .extend_ttl(&payout_key, PERSISTENT_THRESHOLD, PERSISTENT_BUMP);
        env.events().publish(
            (symbol_short!("pal"), symbol_short!("payout")),
            (recipient.clone(), cycle),
        );
        Ok(recipient)
    }

    /// Organizer closes the round once every cycle has been distributed.
    pub fn close_round(env: Env) -> Result<(), Error> {
        let mut cfg = Self::config(&env)?;
        cfg.organizer.require_auth();
        if cfg.status != Status::Active {
            return Err(Error::WrongState);
        }
        // Confirm every cycle paid out.
        let mut c: u32 = 1;
        while c <= cfg.cycles {
            let paid = env
                .storage()
                .persistent()
                .get::<_, bool>(&DataKey::Payout(c))
                .unwrap_or(false);
            if !paid {
                return Err(Error::CyclesRemaining);
            }
            c += 1;
        }
        cfg.status = Status::Completed;
        env.storage().instance().set(&DataKey::Config, &cfg);
        env.storage()
            .instance()
            .extend_ttl(INSTANCE_THRESHOLD, INSTANCE_BUMP);
        env.events()
            .publish((symbol_short!("pal"), symbol_short!("closed")), cfg.organizer);
        Ok(())
    }

    /// View the round state. Heavier read; intended for indexers / dashboards
    /// rather than tight inner loops.
    pub fn get_state(env: Env) -> Result<RoundState, Error> {
        let cfg = Self::config(&env)?;
        let now = env.ledger().timestamp();
        let elapsed = now.saturating_sub(cfg.start_ts);
        // Current cycle index (1-based). Capped at cfg.cycles.
        let mut current_cycle = if cfg.cycle_seconds == 0 {
            1
        } else {
            (elapsed / cfg.cycle_seconds) as u32 + 1
        };
        if current_cycle > cfg.cycles {
            current_cycle = cfg.cycles;
        }
        let mut contributions = Map::new(&env);
        let mut payouts = Map::new(&env);
        let mut c: u32 = 1;
        while c <= cfg.cycles {
            let list: Vec<Address> = env
                .storage()
                .persistent()
                .get(&DataKey::Contributions(c))
                .unwrap_or_else(|| Vec::new(&env));
            contributions.set(c, list);
            let paid = env
                .storage()
                .persistent()
                .get::<_, bool>(&DataKey::Payout(c))
                .unwrap_or(false);
            payouts.set(c, paid);
            c += 1;
        }
        Ok(RoundState {
            status: cfg.status,
            current_cycle,
            organizer: cfg.organizer,
            members: cfg.members,
            amount: cfg.amount,
            cycles: cfg.cycles,
            cycle_seconds: cfg.cycle_seconds,
            start_ts: cfg.start_ts,
            contributions,
            payouts,
        })
    }

    // -----------------------------------------------------------------------
    // Internal
    // -----------------------------------------------------------------------

    fn config(env: &Env) -> Result<Config, Error> {
        env.storage()
            .instance()
            .get(&DataKey::Config)
            .ok_or(Error::NotInitialized)
    }
}

fn contains(list: &Vec<Address>, needle: &Address) -> bool {
    let mut i: u32 = 0;
    while i < list.len() {
        if &list.get(i).unwrap() == needle {
            return true;
        }
        i += 1;
    }
    false
}

#[cfg(test)]
mod test;
