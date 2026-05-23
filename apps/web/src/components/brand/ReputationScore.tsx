import { TrendingUp } from "lucide-react";
import { OnChainBadge } from "./OnChainBadge";
import { truncateHash } from "@/lib/utils";

interface ReputationScoreProps {
  score: number;
  weeklyDelta?: number;
  weeklyContribs?: number;
  contractId?: string | null;
  latestTxHash?: string | null;
  empty?: boolean;
}

/**
 * Score is the hero of the reputation page. Fraunces 5xl, on-chain badge under
 * it. No brand color anywhere — this is a truth page, not an action page.
 */
export function ReputationScore({
  score,
  weeklyDelta,
  weeklyContribs,
  contractId,
  latestTxHash,
  empty,
}: ReputationScoreProps) {
  return (
    <div className="mx-auto w-full max-w-md rounded-lg border border-border-base bg-bg-raised p-9 text-center shadow-md">
      <div className="text-xs font-semibold uppercase tracking-[0.18em] text-fg-muted">
        Reputation
      </div>
      <div
        className={
          "mt-4 font-display text-5xl font-semibold leading-none tracking-tight " +
          (empty ? "text-fg-subtle" : "text-fg-base")
        }
      >
        {score}
      </div>
      {!empty && latestTxHash ? (
        <div className="mt-5 flex flex-col items-center gap-2">
          <OnChainBadge txHash={latestTxHash} />
          {contractId ? (
            <div className="font-mono text-xs text-fg-subtle">
              {truncateHash(contractId, 6, 6)} · tx {truncateHash(latestTxHash, 4, 4)}
            </div>
          ) : null}
        </div>
      ) : null}
      {!empty && typeof weeklyDelta === "number" ? (
        <div className="mt-4 inline-flex items-center gap-1 text-sm font-medium text-success">
          <TrendingUp className="h-4 w-4" aria-hidden />+{weeklyDelta} this week
          {weeklyContribs ? <span className="text-fg-muted"> ({weeklyContribs} contribs)</span> : null}
        </div>
      ) : null}
      {empty ? (
        <p className="mt-4 text-base text-fg-muted">
          Bago ka pa lang. Pag-contribute ka, lalakas ang score mo.
        </p>
      ) : null}
    </div>
  );
}
