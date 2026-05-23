"use client";

import { useEffect } from "react";
import { ErrorView } from "@/components/brand/ErrorBoundary";

export default function ReputationError({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  useEffect(() => {
    // eslint-disable-next-line no-console
    console.error("[damay/reputation-error]", error);
  }, [error]);
  return (
    <div className="container mx-auto max-w-3xl px-5 py-16 lg:px-16">
      <ErrorView
        title="Hindi ma-fetch ang score sa Stellar."
        body="Subukan ulit para sa latest on-chain data."
        onRetry={reset}
      />
    </div>
  );
}
