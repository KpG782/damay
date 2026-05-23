"use client";

import { useEffect } from "react";
import { ErrorView } from "@/components/brand/ErrorBoundary";

export default function RoundError({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  useEffect(() => {
    // eslint-disable-next-line no-console
    console.error("[damay/round-error]", error);
  }, [error]);
  return (
    <div className="container mx-auto px-5 py-16 lg:px-16">
      <ErrorView
        title="Naku, hindi ma-load ang round na ito."
        body="Baka may connection issue sa Stellar testnet."
        onRetry={reset}
      />
    </div>
  );
}
