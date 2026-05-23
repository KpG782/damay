import type {
  Round,
  RoundDetail,
  Member,
  Contribution,
  Payout,
  ReputationEvent,
  GetReputationResponse,
} from "@damay/types";

/**
 * Demo-mode seed data. Used when Supabase is not configured OR when the API
 * is unreachable, so the demo never blanks out. Filipino names per style guide.
 */

const now = new Date();
const iso = (offsetMin: number) =>
  new Date(now.getTime() - offsetMin * 60_000).toISOString();

const today = now.toISOString().slice(0, 10);

export const seedMembers: Record<string, Member> = {
  carmela: {
    id: "mbr_carmela",
    whatsappE164: "+639171000001",
    displayName: "Carmela Reyes",
    stellarAccount: "GCXY7AB3C4D5E6F7G8H9I0J1K2L3M4N5O6P7Q8R9S0T1U2V3W4X5K9P2",
    createdAt: iso(60 * 24 * 90),
    updatedAt: iso(60),
  },
  rey: {
    id: "mbr_rey",
    whatsappE164: "+639171000002",
    displayName: "Rey Cabrera",
    stellarAccount: "GAXR3F2D1C0B9A8Z7Y6X5W4V3U2T1S0R9Q8P7N6M5L4K3J2H1G0F9D4E1",
    createdAt: iso(60 * 24 * 80),
    updatedAt: iso(60 * 2),
  },
  joelle: {
    id: "mbr_joelle",
    whatsappE164: "+639171000003",
    displayName: "Joelle Santos",
    stellarAccount: "GBQR2T3S4U5V6W7X8Y9Z0A1B2C3D4E5F6G7H8I9J0K1L2M3N4O5P6Q9F3",
    createdAt: iso(60 * 24 * 75),
    updatedAt: iso(60 * 5),
  },
  marites: {
    id: "mbr_marites",
    whatsappE164: "+639171000004",
    displayName: "Marites Aquino",
    stellarAccount: "GCMA1R2I3T4E5S6A7Q8U9I0N1O2D3E4M5O6N7S8T9R0A1T2I3O4N5P6T7",
    createdAt: iso(60 * 24 * 30),
    updatedAt: iso(60 * 30),
  },
  joaquin: {
    id: "mbr_joaquin",
    whatsappE164: "+639171000005",
    displayName: "Joaquin Dela Cruz",
    stellarAccount: "GDJO2A3Q4U5I6N7D8E9L0A1C2R3U4Z5D6E7M8O9N0S1T2R3A4T5I6O7N8",
    createdAt: iso(60 * 24 * 60),
    updatedAt: iso(60 * 60),
  },
  aileen: {
    id: "mbr_aileen",
    whatsappE164: "+639171000006",
    displayName: "Aileen Bautista",
    stellarAccount: "GEAI3L4E5E6N7B8A9U0T1I2S3T4A5D6E7M8O9N0S1T2R3A4T5I6O7N8P9",
    createdAt: iso(60 * 24 * 45),
    updatedAt: iso(60 * 90),
  },
};

export const seedRounds: Round[] = [
  {
    id: "rnd_kapitbahay",
    organizerId: "org_demo_carmela",
    name: "Kapitbahay Savings",
    code: "KAPIT-21",
    contributionAmountPhp: 500,
    memberCount: 6,
    frequency: "weekly",
    startDate: "2026-04-25",
    status: "active",
    paluwaganContractId: "CCXYK9P2A3B4C5D6E7F8G9H0I1J2K3L4M5N6O7P8Q9R0S1T2U3V4W5X6",
    createdAt: iso(60 * 24 * 28),
    updatedAt: iso(60),
  },
  {
    id: "rnd_pamilya",
    organizerId: "org_demo_carmela",
    name: "Pamilya Pot",
    code: "PAMILYA-08",
    contributionAmountPhp: 1000,
    memberCount: 8,
    frequency: "weekly",
    startDate: "2026-05-27",
    status: "active",
    paluwaganContractId: "CCPAMILYA8Z7Y6X5W4V3U2T1S0R9Q8P7O6N5M4L3K2J1H0G9F8E7D6C5",
    createdAt: iso(60 * 24 * 14),
    updatedAt: iso(60 * 4),
  },
  {
    id: "rnd_tindera",
    organizerId: "org_demo_carmela",
    name: "Tindera Circle",
    code: "TINDERA-06",
    contributionAmountPhp: 300,
    memberCount: 6,
    frequency: "weekly",
    startDate: "2026-03-01",
    status: "active",
    paluwaganContractId: "CCTINDERA6F5E4D3C2B1A0Z9Y8X7W6V5U4T3S2R1Q0P9O8N7M6L5K4J3H2",
    createdAt: iso(60 * 24 * 70),
    updatedAt: iso(60 * 24),
  },
];

export const seedContributionsByRound: Record<string, Contribution[]> = {
  rnd_kapitbahay: [
    {
      id: "ctr_1",
      roundId: "rnd_kapitbahay",
      memberId: "mbr_carmela",
      cycleNumber: 3,
      amountPhp: 500,
      stellarTxHash: "a1f23c9d4e88b7a6c5f4e3d2c1b0a9f8e7d6c5b4a39281706050403020100ffee",
      status: "confirmed",
      sourceMessageSid: "SMdemo01",
      createdAt: iso(60 * 26),
      updatedAt: iso(60 * 26),
    },
    {
      id: "ctr_2",
      roundId: "rnd_kapitbahay",
      memberId: "mbr_rey",
      cycleNumber: 3,
      amountPhp: 500,
      stellarTxHash: "b2f4d9e1a7c8b3a4d5e6f7a8b9c0d1e2f3a4b5c6d7e8f9a0b1c2d3e4f5a6b7c8",
      status: "confirmed",
      sourceMessageSid: "SMdemo02",
      createdAt: iso(60 * 24),
      updatedAt: iso(60 * 24),
    },
    {
      id: "ctr_3",
      roundId: "rnd_kapitbahay",
      memberId: "mbr_joelle",
      cycleNumber: 3,
      amountPhp: 500,
      stellarTxHash: "c3d7a8f1e2b4c5d6e7f8a9b0c1d2e3f4a5b6c7d8e9f0a1b2c3d4e5f6a7b8c9d0",
      status: "confirmed",
      sourceMessageSid: "SMdemo03",
      createdAt: iso(60 * 5),
      updatedAt: iso(60 * 5),
    },
    {
      id: "ctr_4",
      roundId: "rnd_kapitbahay",
      memberId: "mbr_marites",
      cycleNumber: 3,
      amountPhp: 500,
      stellarTxHash: null,
      status: "pending",
      sourceMessageSid: "SMdemo04",
      createdAt: iso(2),
      updatedAt: iso(2),
    },
  ],
  rnd_pamilya: [],
  rnd_tindera: [
    {
      id: "ctr_t1",
      roundId: "rnd_tindera",
      memberId: "mbr_carmela",
      cycleNumber: 6,
      amountPhp: 300,
      stellarTxHash: "f6e5d4c3b2a1908f7e6d5c4b3a29180716253443526170809a0b1c2d3e4f5a6b",
      status: "confirmed",
      sourceMessageSid: "SMdemoT1",
      createdAt: iso(60 * 48),
      updatedAt: iso(60 * 48),
    },
  ],
};

export const seedPayoutsByRound: Record<string, Payout[]> = {
  rnd_kapitbahay: [
    {
      id: "pay_1",
      roundId: "rnd_kapitbahay",
      memberId: "mbr_carmela",
      cycleNumber: 1,
      amountPhp: 3000,
      stellarTxHash: "d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0c1d2e3f4a5b6c7d8e9f0a1b2c3d4e5",
      status: "confirmed",
      createdAt: iso(60 * 24 * 14),
      updatedAt: iso(60 * 24 * 14),
    },
    {
      id: "pay_2",
      roundId: "rnd_kapitbahay",
      memberId: "mbr_aileen",
      cycleNumber: 2,
      amountPhp: 3000,
      stellarTxHash: "e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0c1d2e3f4a5b6c7d8e9f0a1b2c3d4e5f6",
      status: "confirmed",
      createdAt: iso(60 * 24 * 7),
      updatedAt: iso(60 * 24 * 7),
    },
  ],
  rnd_pamilya: [],
  rnd_tindera: [],
};

export function seedRoundDetail(id: string): RoundDetail | null {
  const round = seedRounds.find((r) => r.id === id);
  if (!round) return null;
  const memberIdsByRound: Record<string, string[]> = {
    rnd_kapitbahay: ["mbr_carmela", "mbr_aileen", "mbr_rey", "mbr_joelle", "mbr_marites", "mbr_joaquin"],
    rnd_pamilya: ["mbr_carmela", "mbr_rey", "mbr_joelle", "mbr_marites", "mbr_joaquin", "mbr_aileen", "mbr_rey", "mbr_joelle"],
    rnd_tindera: ["mbr_carmela", "mbr_aileen", "mbr_rey", "mbr_joelle", "mbr_marites", "mbr_joaquin"],
  };
  const ids = memberIdsByRound[id] ?? [];
  return {
    ...round,
    members: ids.map((mid, idx) => ({
      roundId: id,
      memberId: mid,
      payoutPosition: idx + 1,
      joinedAt: iso(60 * 24 * 30),
      member: seedMembers[mid.replace("mbr_", "")] ?? seedMembers.carmela,
    })),
    contributions: seedContributionsByRound[id] ?? [],
    payouts: seedPayoutsByRound[id] ?? [],
  };
}

export function seedReputation(memberId: string): GetReputationResponse {
  const events: ReputationEvent[] = [
    {
      id: "rep_1",
      memberId,
      eventType: "contribution",
      weight: 10,
      stellarTxHash: "a1f23c9d4e88b7a6c5f4e3d2c1b0a9f8e7d6c5b4a39281706050403020100ffee",
      context: { round: "Kapitbahay c3" },
      createdAt: iso(60 * 26),
    },
    {
      id: "rep_2",
      memberId,
      eventType: "contribution",
      weight: 10,
      stellarTxHash: "b2f4d9e1a7c8b3a4d5e6f7a8b9c0d1e2f3a4b5c6d7e8f9a0b1c2d3e4f5a6b7c8",
      context: { round: "Kapitbahay c2" },
      createdAt: iso(60 * 24 * 14),
    },
    {
      id: "rep_3",
      memberId,
      eventType: "payout",
      weight: 1,
      stellarTxHash: "c3d7a8f1e2b4c5d6e7f8a9b0c1d2e3f4a5b6c7d8e9f0a1b2c3d4e5f6a7b8c9d0",
      context: { round: "Kapitbahay c2" },
      createdAt: iso(60 * 24 * 14),
    },
    {
      id: "rep_4",
      memberId,
      eventType: "contribution",
      weight: 10,
      stellarTxHash: "d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0c1d2e3f4a5b6c7d8e9f0a1b2c3d4e5",
      context: { round: "Kapitbahay c1" },
      createdAt: iso(60 * 24 * 21),
    },
    {
      id: "rep_5",
      memberId,
      eventType: "contribution",
      weight: 10,
      stellarTxHash: "e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0c1d2e3f4a5b6c7d8e9f0a1b2c3d4e5f6",
      context: { round: "Tindera c6" },
      createdAt: iso(60 * 24 * 28),
    },
    {
      id: "rep_6",
      memberId,
      eventType: "default",
      weight: -25,
      stellarTxHash: "f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0c1d2e3f4a5b6c7d8e9f0a1b2c3d4e5f6a7",
      context: { round: "Pamilya c4" },
      createdAt: iso(60 * 24 * 70),
    },
    {
      id: "rep_7",
      memberId,
      eventType: "contribution",
      weight: 10,
      stellarTxHash: "07a8b9c0d1e2f3a4b5c6d7e8f9a0b1c2d3e4f5a6b7c8d9e0f1a2b3c4d5e6f7a8",
      context: { round: "Pamilya c3" },
      createdAt: iso(60 * 24 * 77),
    },
  ];
  const score = events.reduce((acc, e) => acc + e.weight, 0) + 116; // baseline
  return { memberId, score, events };
}

export function seedMemberById(id: string): Member | null {
  for (const m of Object.values(seedMembers)) if (m.id === id) return m;
  return null;
}

export { today };
