-- DAMAY seed migration (0002) — demo data for judge walkthrough.
-- Idempotent: every insert uses ON CONFLICT DO NOTHING; safe to re-run.
-- IMPORTANT: phone numbers below are FAKE / demo-only. stellar_account is
-- left NULL on seed; the backend assigns real testnet G-addresses on first
-- member registration via the Stellar SDK (see apps/api/.../clients/stellar.py).
-- The schema CHECK on stellar_account permits NULL, so the demo flow works
-- end-to-end after deploy_testnet.sh + a one-time member sync.
--
-- Seeded entities:
--   * 1 organizer (Ate Lourdes Mendoza) — id matches a Supabase auth.users
--     row created by the deploy script. If running locally without Supabase
--     auth, use the service role to insert; the FK to organizers.id is
--     respected, but auth.uid() will be null in psql sessions.
--   * 6 members with realistic Filipino names + WhatsApp numbers.
--   * 1 active round "Kapitbahay Kalsada 7" (cycle 1, payout position 1 = Marites).
--   * 3 past rounds (status='completed') with reputation history.
--
-- Past-round reputation totals (target, sum of weights):
--   Carmela +30   Rey +29   Joelle +30   Marites +20 (one default −25, recovered)
--   Joaquin +30   Aileen +28

begin;

-- --------------------------------------------------------------------------
-- Organizer
-- --------------------------------------------------------------------------
insert into organizers (id, email, display_name, phone)
values
    ('11111111-1111-1111-1111-111111111111',
     'lourdes.mendoza+demo@damay.kenbuilds.tech',
     'Ate Lourdes Mendoza',
     '+639170000001')
on conflict (id) do nothing;

-- --------------------------------------------------------------------------
-- Members (6 — demo cast for Kapitbahay Kalsada 7)
-- whatsapp_e164 values are FAKE. stellar_account left NULL — assigned by the
-- backend on first registration via Stellar SDK (testnet keypair + friendbot).
-- --------------------------------------------------------------------------
insert into members (id, whatsapp_e164, display_name, stellar_account)
values
    ('22222222-2222-2222-2222-222222222201', '+639171234567', 'Carmela Reyes',          null),
    ('22222222-2222-2222-2222-222222222202', '+639172345678', 'Reynaldo "Rey" Aquino',  null),
    ('22222222-2222-2222-2222-222222222203', '+639173456789', 'Joelle dela Cruz',       null),
    ('22222222-2222-2222-2222-222222222204', '+639174567890', 'Marites Soriano',        null),
    ('22222222-2222-2222-2222-222222222205', '+639175678901', 'Joaquin Bautista',       null),
    ('22222222-2222-2222-2222-222222222206', '+639178901234', 'Aileen Mendoza',         null)
on conflict (id) do nothing;

-- --------------------------------------------------------------------------
-- Past rounds (3) — all completed
-- Codes: KK4, KK5, KK6.   Active demo round below uses KK7.
-- --------------------------------------------------------------------------
insert into rounds (id, organizer_id, name, code, contribution_amount_php,
                    member_count, frequency, start_date, status,
                    paluwagan_contract_id)
values
    ('33333333-3333-3333-3333-333333333304',
     '11111111-1111-1111-1111-111111111111',
     'Kapitbahay Kalsada 4', 'KK4', 500, 6, 'weekly', '2025-09-06', 'completed',
     null),
    ('33333333-3333-3333-3333-333333333305',
     '11111111-1111-1111-1111-111111111111',
     'Kapitbahay Kalsada 5', 'KK5', 500, 6, 'weekly', '2025-11-15', 'completed',
     null),
    ('33333333-3333-3333-3333-333333333306',
     '11111111-1111-1111-1111-111111111111',
     'Kapitbahay Kalsada 6', 'KK6', 500, 6, 'weekly', '2026-02-07', 'completed',
     null)
on conflict (id) do nothing;

-- --------------------------------------------------------------------------
-- Active demo round — Kapitbahay Kalsada 7
-- Cycle 1 payout position = 1 = Marites (the "even with one late payment she
-- still got paid" moment).
-- --------------------------------------------------------------------------
insert into rounds (id, organizer_id, name, code, contribution_amount_php,
                    member_count, frequency, start_date, status,
                    paluwagan_contract_id)
values
    ('33333333-3333-3333-3333-333333333307',
     '11111111-1111-1111-1111-111111111111',
     'Kapitbahay Kalsada 7', 'KK7', 500, 6, 'weekly', '2026-05-23', 'active',
     null)
on conflict (id) do nothing;

-- --------------------------------------------------------------------------
-- round_members — payout positions for the active round.
-- Position 1 = Marites (cycle 1 recipient — demo beat).
-- --------------------------------------------------------------------------
insert into round_members (round_id, member_id, payout_position)
values
    ('33333333-3333-3333-3333-333333333307',
     '22222222-2222-2222-2222-222222222204', 1),  -- Marites
    ('33333333-3333-3333-3333-333333333307',
     '22222222-2222-2222-2222-222222222201', 2),  -- Carmela
    ('33333333-3333-3333-3333-333333333307',
     '22222222-2222-2222-2222-222222222202', 3),  -- Rey
    ('33333333-3333-3333-3333-333333333307',
     '22222222-2222-2222-2222-222222222203', 4),  -- Joelle
    ('33333333-3333-3333-3333-333333333307',
     '22222222-2222-2222-2222-222222222205', 5),  -- Joaquin
    ('33333333-3333-3333-3333-333333333307',
     '22222222-2222-2222-2222-222222222206', 6)   -- Aileen
on conflict (round_id, member_id) do nothing;

-- Past-round membership (used by reputation_events RLS join + organizer access)
insert into round_members (round_id, member_id, payout_position)
values
    -- KK4
    ('33333333-3333-3333-3333-333333333304', '22222222-2222-2222-2222-222222222201', 1),
    ('33333333-3333-3333-3333-333333333304', '22222222-2222-2222-2222-222222222202', 2),
    ('33333333-3333-3333-3333-333333333304', '22222222-2222-2222-2222-222222222203', 3),
    ('33333333-3333-3333-3333-333333333304', '22222222-2222-2222-2222-222222222204', 4),
    ('33333333-3333-3333-3333-333333333304', '22222222-2222-2222-2222-222222222205', 5),
    ('33333333-3333-3333-3333-333333333304', '22222222-2222-2222-2222-222222222206', 6),
    -- KK5
    ('33333333-3333-3333-3333-333333333305', '22222222-2222-2222-2222-222222222201', 1),
    ('33333333-3333-3333-3333-333333333305', '22222222-2222-2222-2222-222222222202', 2),
    ('33333333-3333-3333-3333-333333333305', '22222222-2222-2222-2222-222222222203', 3),
    ('33333333-3333-3333-3333-333333333305', '22222222-2222-2222-2222-222222222204', 4),
    ('33333333-3333-3333-3333-333333333305', '22222222-2222-2222-2222-222222222205', 5),
    ('33333333-3333-3333-3333-333333333305', '22222222-2222-2222-2222-222222222206', 6),
    -- KK6
    ('33333333-3333-3333-3333-333333333306', '22222222-2222-2222-2222-222222222201', 1),
    ('33333333-3333-3333-3333-333333333306', '22222222-2222-2222-2222-222222222202', 2),
    ('33333333-3333-3333-3333-333333333306', '22222222-2222-2222-2222-222222222203', 3),
    ('33333333-3333-3333-3333-333333333306', '22222222-2222-2222-2222-222222222204', 4),
    ('33333333-3333-3333-3333-333333333306', '22222222-2222-2222-2222-222222222205', 5),
    ('33333333-3333-3333-3333-333333333306', '22222222-2222-2222-2222-222222222206', 6)
on conflict (round_id, member_id) do nothing;

-- --------------------------------------------------------------------------
-- reputation_events — synthetic on-chain history.
-- stellar_tx_hash values are 64-char lowercase hex placeholders; they pass
-- the CHECK constraint and the (tx_hash, event_type) uniqueness.
-- Sum of weights per member matches target totals (commented above).
-- --------------------------------------------------------------------------

-- Carmela — clean: 3 × +10 = 30
insert into reputation_events (member_id, event_type, weight, stellar_tx_hash, context)
values
    ('22222222-2222-2222-2222-222222222201', 'contribution', 10,
     'a1a1a1a1a1a1a1a1a1a1a1a1a1a1a1a1a1a1a1a1a1a1a1a1a1a1a1a1a1a1a101',
     '{"round_code":"KK4","cycle":1}'),
    ('22222222-2222-2222-2222-222222222201', 'contribution', 10,
     'a1a1a1a1a1a1a1a1a1a1a1a1a1a1a1a1a1a1a1a1a1a1a1a1a1a1a1a1a1a1a102',
     '{"round_code":"KK5","cycle":1}'),
    ('22222222-2222-2222-2222-222222222201', 'contribution', 10,
     'a1a1a1a1a1a1a1a1a1a1a1a1a1a1a1a1a1a1a1a1a1a1a1a1a1a1a1a1a1a1a103',
     '{"round_code":"KK6","cycle":1}')
on conflict (stellar_tx_hash, event_type) do nothing;

-- Rey — +10, +10, +9 (one late-but-paid → reduced weight) = 29
insert into reputation_events (member_id, event_type, weight, stellar_tx_hash, context)
values
    ('22222222-2222-2222-2222-222222222202', 'contribution', 10,
     'a2a2a2a2a2a2a2a2a2a2a2a2a2a2a2a2a2a2a2a2a2a2a2a2a2a2a2a2a2a2a201',
     '{"round_code":"KK4","cycle":2}'),
    ('22222222-2222-2222-2222-222222222202', 'contribution', 10,
     'a2a2a2a2a2a2a2a2a2a2a2a2a2a2a2a2a2a2a2a2a2a2a2a2a2a2a2a2a2a2a202',
     '{"round_code":"KK5","cycle":2}'),
    ('22222222-2222-2222-2222-222222222202', 'contribution', 9,
     'a2a2a2a2a2a2a2a2a2a2a2a2a2a2a2a2a2a2a2a2a2a2a2a2a2a2a2a2a2a2a203',
     '{"round_code":"KK6","cycle":2,"note":"late-but-paid"}')
on conflict (stellar_tx_hash, event_type) do nothing;

-- Joelle — clean: 3 × +10 = 30
insert into reputation_events (member_id, event_type, weight, stellar_tx_hash, context)
values
    ('22222222-2222-2222-2222-222222222203', 'contribution', 10,
     'a3a3a3a3a3a3a3a3a3a3a3a3a3a3a3a3a3a3a3a3a3a3a3a3a3a3a3a3a3a3a301',
     '{"round_code":"KK4","cycle":3}'),
    ('22222222-2222-2222-2222-222222222203', 'contribution', 10,
     'a3a3a3a3a3a3a3a3a3a3a3a3a3a3a3a3a3a3a3a3a3a3a3a3a3a3a3a3a3a3a302',
     '{"round_code":"KK5","cycle":3}'),
    ('22222222-2222-2222-2222-222222222203', 'contribution', 10,
     'a3a3a3a3a3a3a3a3a3a3a3a3a3a3a3a3a3a3a3a3a3a3a3a3a3a3a3a3a3a3a303',
     '{"round_code":"KK6","cycle":3}')
on conflict (stellar_tx_hash, event_type) do nothing;

-- Marites — the demo story.
--   +10 (KK4 c4 contrib) + 1 (KK4 c4 payout received) + 10 (KK5 c1) − 25 (KK5 c3 DEFAULT)
--   + 10 (KK5 c4 recovery) + 10 (KK6 c4) + 4 (KK6 c5 decay-adjusted) = +20
insert into reputation_events (member_id, event_type, weight, stellar_tx_hash, context)
values
    ('22222222-2222-2222-2222-222222222204', 'contribution', 10,
     'a4a4a4a4a4a4a4a4a4a4a4a4a4a4a4a4a4a4a4a4a4a4a4a4a4a4a4a4a4a4a401',
     '{"round_code":"KK4","cycle":4}'),
    ('22222222-2222-2222-2222-222222222204', 'payout', 1,
     'a4a4a4a4a4a4a4a4a4a4a4a4a4a4a4a4a4a4a4a4a4a4a4a4a4a4a4a4a4a4a402',
     '{"round_code":"KK4","cycle":4,"received_php":3000}'),
    ('22222222-2222-2222-2222-222222222204', 'contribution', 10,
     'a4a4a4a4a4a4a4a4a4a4a4a4a4a4a4a4a4a4a4a4a4a4a4a4a4a4a4a4a4a4a403',
     '{"round_code":"KK5","cycle":1}'),
    ('22222222-2222-2222-2222-222222222204', 'default', -25,
     'a4a4a4a4a4a4a4a4a4a4a4a4a4a4a4a4a4a4a4a4a4a4a4a4a4a4a4a4a4a4a404',
     '{"round_code":"KK5","cycle":3,"note":"missed deadline by 48h"}'),
    ('22222222-2222-2222-2222-222222222204', 'contribution', 10,
     'a4a4a4a4a4a4a4a4a4a4a4a4a4a4a4a4a4a4a4a4a4a4a4a4a4a4a4a4a4a4a405',
     '{"round_code":"KK5","cycle":4,"note":"recovery cycle"}'),
    ('22222222-2222-2222-2222-222222222204', 'contribution', 10,
     'a4a4a4a4a4a4a4a4a4a4a4a4a4a4a4a4a4a4a4a4a4a4a4a4a4a4a4a4a4a4a406',
     '{"round_code":"KK6","cycle":4}'),
    ('22222222-2222-2222-2222-222222222204', 'contribution', 4,
     'a4a4a4a4a4a4a4a4a4a4a4a4a4a4a4a4a4a4a4a4a4a4a4a4a4a4a4a4a4a4a407',
     '{"round_code":"KK6","cycle":5,"note":"partial-credit decay adjustment"}')
on conflict (stellar_tx_hash, event_type) do nothing;

-- Joaquin — clean: 3 × +10 = 30
insert into reputation_events (member_id, event_type, weight, stellar_tx_hash, context)
values
    ('22222222-2222-2222-2222-222222222205', 'contribution', 10,
     'a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a501',
     '{"round_code":"KK4","cycle":5}'),
    ('22222222-2222-2222-2222-222222222205', 'contribution', 10,
     'a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a502',
     '{"round_code":"KK5","cycle":5}'),
    ('22222222-2222-2222-2222-222222222205', 'contribution', 10,
     'a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a503',
     '{"round_code":"KK6","cycle":5}')
on conflict (stellar_tx_hash, event_type) do nothing;

-- Aileen — +10, +10, +8 (one cycle paid slightly late) = 28
insert into reputation_events (member_id, event_type, weight, stellar_tx_hash, context)
values
    ('22222222-2222-2222-2222-222222222206', 'contribution', 10,
     'a6a6a6a6a6a6a6a6a6a6a6a6a6a6a6a6a6a6a6a6a6a6a6a6a6a6a6a6a6a6a601',
     '{"round_code":"KK4","cycle":6}'),
    ('22222222-2222-2222-2222-222222222206', 'contribution', 10,
     'a6a6a6a6a6a6a6a6a6a6a6a6a6a6a6a6a6a6a6a6a6a6a6a6a6a6a6a6a6a6a602',
     '{"round_code":"KK5","cycle":6}'),
    ('22222222-2222-2222-2222-222222222206', 'contribution', 8,
     'a6a6a6a6a6a6a6a6a6a6a6a6a6a6a6a6a6a6a6a6a6a6a6a6a6a6a6a6a6a6a603',
     '{"round_code":"KK6","cycle":6,"note":"late by 12h, reduced weight"}')
on conflict (stellar_tx_hash, event_type) do nothing;

commit;

-- Verify totals (run manually):
--   select member_id, sum(weight) as score
--   from reputation_events
--   group by member_id
--   order by member_id;
-- Expected:
--   Carmela 30, Rey 29, Joelle 30, Marites 20, Joaquin 30, Aileen 28.
