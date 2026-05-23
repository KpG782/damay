import type {
  GetRoundsResponse,
  GetRoundResponse,
  GetReputationResponse,
  GetHealthzResponse,
  PostDevSimulateMessageRequest,
  PostDevSimulateMessageResponse,
  Round,
  RoundDetail,
} from "@damay/types";
import { env } from "./env";
import {
  seedRounds,
  seedRoundDetail,
  seedReputation,
} from "./mock-data";

const API_BASE = env.NEXT_PUBLIC_API_URL;

const DEFAULT_TIMEOUT_MS = 4000;

async function call<T>(
  path: string,
  init: RequestInit & { fallback?: () => T } = {}
): Promise<{ data: T; isLive: boolean }> {
  const controller = new AbortController();
  const t = setTimeout(() => controller.abort(), DEFAULT_TIMEOUT_MS);
  try {
    const res = await fetch(`${API_BASE}${path}`, {
      ...init,
      signal: controller.signal,
      headers: {
        "Content-Type": "application/json",
        ...(init.headers ?? {}),
      },
      cache: "no-store",
    });
    if (!res.ok) throw new Error(`api ${res.status}`);
    const data = (await res.json()) as T;
    return { data, isLive: true };
  } catch {
    if (init.fallback) return { data: init.fallback(), isLive: false };
    throw new Error("Upstream unavailable and no fallback provided");
  } finally {
    clearTimeout(t);
  }
}

// ----- Public typed wrappers ------------------------------------------------

export async function fetchHealthz() {
  return call<GetHealthzResponse>("/v1/healthz", {
    fallback: () => ({
      status: "degraded" as const,
      checks: { db: "fail", horizon: "fail", twilio: "fail", soroban_rpc: "fail" },
      version: "demo",
    }),
  });
}

export async function fetchRounds() {
  return call<GetRoundsResponse>("/v1/rounds", {
    fallback: () => ({ data: seedRounds as Round[], nextCursor: null }),
  });
}

export async function fetchRound(id: string) {
  return call<GetRoundResponse>(`/v1/rounds/${id}`, {
    fallback: () => {
      const detail = seedRoundDetail(id);
      if (!detail) {
        // Return a minimal-shape stub to keep the page renderable; the page
        // will render an empty/not-found UI.
        return {
          id,
          organizerId: "org_demo_carmela",
          name: "Unknown round",
          code: "UNKNOWN",
          contributionAmountPhp: 0,
          memberCount: 0,
          frequency: "weekly",
          startDate: new Date().toISOString().slice(0, 10),
          status: "draft",
          paluwaganContractId: null,
          createdAt: new Date().toISOString(),
          updatedAt: new Date().toISOString(),
          members: [],
          contributions: [],
          payouts: [],
        } as RoundDetail;
      }
      return detail;
    },
  });
}

export async function fetchReputation(memberId: string) {
  return call<GetReputationResponse>(`/v1/reputation/${memberId}`, {
    fallback: () => seedReputation(memberId),
  });
}

export async function postSimulateMessage(body: PostDevSimulateMessageRequest) {
  return call<PostDevSimulateMessageResponse>("/v1/dev/simulate-message", {
    method: "POST",
    body: JSON.stringify(body),
    fallback: () => ({
      accepted: true as const,
      twilioSid: `SMdemo-${Math.random().toString(36).slice(2, 10)}`,
    }),
  });
}
