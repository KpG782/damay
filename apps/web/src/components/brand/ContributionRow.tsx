import { OnChainBadge } from "./OnChainBadge";
import { formatPhp, timeAgo, truncateHash } from "@/lib/utils";
import { stellarExpertTxUrl } from "@/lib/stellar";
import type { Contribution, Member } from "@damay/types";

interface ContributionRowProps {
  contribution: Contribution;
  member?: Member;
}

export function ContributionRow({ contribution, member }: ContributionRowProps) {
  const name = member?.displayName ?? "Member";
  return (
    <li className="flex items-start justify-between gap-3 border-b border-border-subtle py-3 last:border-b-0">
      <div className="min-w-0 flex-1">
        <div className="text-base text-fg-base">
          <span className="font-medium">{name}</span>{" "}
          <span className="text-fg-muted">contributed {formatPhp(contribution.amountPhp)}</span>
        </div>
        {contribution.stellarTxHash ? (
          <a
            href={stellarExpertTxUrl(contribution.stellarTxHash)}
            target="_blank"
            rel="noopener noreferrer"
            className="mt-1 inline-block font-mono text-xs text-fg-subtle hover:text-accent focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand rounded"
          >
            tx: {truncateHash(contribution.stellarTxHash, 4, 4)}
          </a>
        ) : (
          <div className="mt-1 font-mono text-xs text-fg-subtle">naghihintay ng tx</div>
        )}
      </div>
      <div className="flex shrink-0 flex-col items-end gap-1">
        <OnChainBadge
          txHash={contribution.stellarTxHash}
          status={contribution.status === "confirmed" ? "confirmed" : contribution.status === "failed" ? "failed" : "pending"}
        />
        <span className="text-xs text-fg-subtle">{timeAgo(contribution.createdAt)}</span>
      </div>
    </li>
  );
}
