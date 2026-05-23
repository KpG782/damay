"use client";

import { AlertTriangle } from "lucide-react";
import { Button } from "@/components/ui/button";

interface ErrorViewProps {
  title?: string;
  body?: string;
  onRetry?: () => void;
}

/**
 * Friendly error UI matching the style guide. Used by `error.tsx` route files
 * and as a standalone block.
 */
export function ErrorView({
  title = "Naku, may problema sa connection.",
  body = "Hindi ma-load ang data mo. Subukan natin ulit.",
  onRetry,
}: ErrorViewProps) {
  return (
    <div className="mx-auto flex max-w-lg flex-col items-center justify-center rounded-lg border border-danger/20 bg-danger/5 px-6 py-14 text-center">
      <div className="mb-5 flex h-16 w-16 items-center justify-center rounded-full bg-danger/10 text-danger">
        <AlertTriangle className="h-7 w-7" aria-hidden />
      </div>
      <h2 className="font-display text-3xl font-semibold text-fg-base">{title}</h2>
      <p className="mt-3 max-w-md text-base text-fg-muted">{body}</p>
      {onRetry ? (
        <Button variant="secondary" className="mt-6" onClick={onRetry}>
          Try again
        </Button>
      ) : null}
      <p className="mt-4 text-sm text-fg-subtle">
        May tanong? Mag-message sa support.
      </p>
    </div>
  );
}
