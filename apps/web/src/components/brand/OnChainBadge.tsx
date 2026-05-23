import { Check, Clock } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { stellarExpertTxUrl } from "@/lib/stellar";
import { truncateHash } from "@/lib/utils";

interface OnChainBadgeProps {
  txHash: string | null | undefined;
  status?: "confirmed" | "pending" | "failed";
  label?: string;
}

/**
 * The single most important component for trust signaling on this product.
 * - Confirmed → accent teal pill, click → Stellar Expert.
 * - Pending → warning pill, no link.
 * - Failed → danger pill, no link.
 */
export function OnChainBadge({ txHash, status = "confirmed", label }: OnChainBadgeProps) {
  if (status === "pending") {
    return (
      <Badge variant="warning" aria-label="Pending — awaiting Stellar confirmation">
        <Clock className="h-3 w-3" aria-hidden />
        Pending
      </Badge>
    );
  }
  if (status === "failed" || !txHash) {
    return (
      <Badge variant="danger" aria-label="Failed">
        Failed
      </Badge>
    );
  }
  return (
    <a
      href={stellarExpertTxUrl(txHash)}
      target="_blank"
      rel="noopener noreferrer"
      title={`tx ${truncateHash(txHash, 6, 6)} — click to view on Stellar Expert`}
      className="inline-flex rounded-full focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand focus-visible:ring-offset-2 focus-visible:ring-offset-bg-base"
    >
      <Badge variant="accent">
        <Check className="h-3 w-3" aria-hidden />
        {label ?? "On-chain"}
      </Badge>
    </a>
  );
}
