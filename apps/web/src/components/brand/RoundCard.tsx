import Link from "next/link";
import { ArrowRight } from "lucide-react";
import { Card } from "@/components/ui/card";
import { OnChainBadge } from "./OnChainBadge";
import { formatPhp } from "@/lib/utils";
import type { Round } from "@damay/types";

interface RoundCardProps {
  round: Round;
  contributedCount?: number;
  cycleNumber?: number;
  cycleTotal?: number;
  nextPayoutName?: string;
  nextPayoutInDays?: number;
  doneCopy?: string;
}

export function RoundCard({
  round,
  contributedCount = 0,
  cycleNumber = 1,
  cycleTotal,
  nextPayoutName,
  nextPayoutInDays,
  doneCopy,
}: RoundCardProps) {
  const total = cycleTotal ?? round.memberCount;
  const dots = Array.from({ length: round.memberCount }, (_, i) => i < contributedCount);
  const isDone = round.status === "completed" || (doneCopy && contributedCount >= round.memberCount);

  return (
    <Card className="flex flex-col gap-4 p-6">
      <div className="flex items-start justify-between gap-3">
        <div>
          <h3 className="font-sans text-xl font-semibold text-fg-base">{round.name}</h3>
          <p className="mt-1 text-sm text-fg-muted">
            Cycle {cycleNumber}
            {cycleTotal ? ` of ${cycleTotal}` : ""}
          </p>
        </div>
        {round.paluwaganContractId ? <OnChainBadge txHash={round.paluwaganContractId} /> : null}
      </div>

      <p className="text-sm text-fg-muted">
        {formatPhp(round.contributionAmountPhp)}/{round.frequency === "weekly" ? "week" : round.frequency === "biweekly" ? "2 weeks" : "month"} ·{" "}
        {round.memberCount} members
      </p>

      <div className="flex items-center gap-2" aria-label={`${contributedCount} of ${round.memberCount} contributed`}>
        <div className="flex gap-1.5" aria-hidden>
          {dots.map((on, i) => (
            <span
              key={i}
              className={
                "h-2.5 w-2.5 rounded-full " +
                (on ? "bg-success" : "bg-bg-subtle border border-border-base")
              }
            />
          ))}
        </div>
        <span className="text-sm text-fg-muted">
          {isDone ? (doneCopy ?? "Done na — closing soon") : `${contributedCount} of ${round.memberCount} contributed`}
        </span>
      </div>

      {!isDone && nextPayoutName ? (
        <p className="text-sm text-fg-muted">
          Next payout: <span className="font-medium text-fg-base">{nextPayoutName}</span>
          {typeof nextPayoutInDays === "number" ? ` · in ${nextPayoutInDays} day${nextPayoutInDays === 1 ? "" : "s"}` : null}
        </p>
      ) : null}

      <div className="mt-auto">
        <Link
          href={`/dashboard/rounds/${round.id}`}
          className="group inline-flex items-center gap-1 text-sm font-medium text-fg-muted transition-colors duration-fast ease-damay hover:text-fg-base focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand focus-visible:ring-offset-2 focus-visible:ring-offset-bg-raised rounded"
        >
          Open round
          <ArrowRight className="h-4 w-4 transition-transform duration-fast ease-damay group-hover:translate-x-0.5" aria-hidden />
        </Link>
      </div>
    </Card>
  );
}
