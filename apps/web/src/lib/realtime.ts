"use client";

import { useEffect, useRef, useState } from "react";
import { getBrowserSupabase } from "./supabase";
import type { Contribution } from "@damay/types";

type PostgresPayload = {
  eventType: string;
  new: Contribution | null;
  old: Contribution | null;
};

/**
 * Subscribes to Supabase Realtime for the `contributions` table filtered by
 * round_id. Falls back to polling every 5s if the channel can't be opened
 * (e.g., demo mode without Supabase).
 */
export function useRealtimeContributions(
  roundId: string,
  initial: Contribution[]
): { contributions: Contribution[]; isLive: boolean } {
  const [contributions, setContributions] = useState<Contribution[]>(initial);
  const [isLive, setIsLive] = useState(false);
  const initialRef = useRef(initial);

  useEffect(() => {
    initialRef.current = initial;
    setContributions(initial);
  }, [initial]);

  useEffect(() => {
    const supabase = getBrowserSupabase();
    if (!supabase) {
      setIsLive(false);
      const id = setInterval(() => {
        setContributions((curr) => [...curr]);
      }, 5000);
      return () => clearInterval(id);
    }

    // Supabase-js typing for `.on('postgres_changes', ...)` requires a
    // generic-literal overload that's awkward to type at runtime. We go through
    // an `unknown` cast and validate the payload shape ourselves.
    const channel = (supabase.channel(`contributions:${roundId}`) as unknown as {
      on: (
        event: string,
        opts: Record<string, string>,
        cb: (payload: PostgresPayload) => void
      ) => { subscribe: (cb: (status: string) => void) => unknown };
    })
      .on(
        "postgres_changes",
        {
          event: "*",
          schema: "public",
          table: "contributions",
          filter: `round_id=eq.${roundId}`,
        },
        (payload) => {
          setContributions((curr) => {
            if (payload.eventType === "INSERT" && payload.new) {
              return [payload.new, ...curr];
            }
            if (payload.eventType === "UPDATE" && payload.new) {
              return curr.map((c) => (c.id === payload.new!.id ? payload.new! : c));
            }
            if (payload.eventType === "DELETE" && payload.old) {
              return curr.filter((c) => c.id !== payload.old!.id);
            }
            return curr;
          });
        }
      )
      .subscribe((status) => {
        setIsLive(status === "SUBSCRIBED");
      });

    return () => {
      const sb = getBrowserSupabase();
      if (sb && channel) {
        try {
          (sb as unknown as { removeChannel: (c: unknown) => void }).removeChannel(channel);
        } catch {
          /* noop */
        }
      }
    };
  }, [roundId]);

  return { contributions, isLive };
}
