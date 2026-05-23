"use client";

import { useRealtimeContributions } from "@/lib/realtime";
import { ContributionRow } from "./ContributionRow";
import { EmptyState } from "./EmptyState";
import { Inbox } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import type { Contribution, Member } from "@damay/types";

interface Props {
  roundId: string;
  initial: Contribution[];
  membersById: Record<string, Member>;
}

export function ContributionTimeline({ roundId, initial, membersById }: Props) {
  const { contributions, isLive } = useRealtimeContributions(roundId, initial);

  if (contributions.length === 0) {
    return (
      <EmptyState
        icon={<Inbox className="h-7 w-7" aria-hidden />}
        title="Walang pa naka-contribute sa cycle na ito."
        body="Naka-notify na sina Carmela, Rey, at iba pa sa WhatsApp. Lalabas dito pag may nag-send na."
      />
    );
  }

  return (
    <div className="space-y-2">
      <div className="flex items-center justify-between">
        <h3 className="font-sans text-xl font-semibold text-fg-base">Activity timeline</h3>
        <Badge variant={isLive ? "success" : "neutral"} aria-live="polite">
          {isLive ? "Live" : "Polling"}
        </Badge>
      </div>
      <ul className="rounded-md border border-border-subtle bg-bg-raised px-6 shadow-sm">
        {contributions.map((c) => (
          <li key={c.id} className="animate-slide-in">
            <ContributionRow contribution={c} member={membersById[c.memberId]} />
          </li>
        ))}
      </ul>
    </div>
  );
}
