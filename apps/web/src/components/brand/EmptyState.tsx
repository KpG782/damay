import * as React from "react";
import { cn } from "@/lib/utils";

interface EmptyStateProps {
  icon?: React.ReactNode;
  title: string;
  body?: string;
  action?: React.ReactNode;
  className?: string;
}

export function EmptyState({ icon, title, body, action, className }: EmptyStateProps) {
  return (
    <div
      className={cn(
        "mx-auto flex max-w-lg flex-col items-center justify-center rounded-lg border border-dashed border-border-base bg-bg-raised/60 px-6 py-14 text-center",
        className
      )}
    >
      {icon ? (
        <div className="mb-5 flex h-16 w-16 items-center justify-center rounded-full bg-brand-subtle/40 text-brand">
          {icon}
        </div>
      ) : null}
      <h2 className="font-display text-3xl font-semibold text-fg-base">{title}</h2>
      {body ? <p className="mt-3 max-w-md text-base text-fg-muted">{body}</p> : null}
      {action ? <div className="mt-6">{action}</div> : null}
    </div>
  );
}
