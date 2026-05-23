import Link from "next/link";
import { cn } from "@/lib/utils";

export function Logo({ className, href = "/" }: { className?: string; href?: string }) {
  return (
    <Link
      href={href}
      className={cn(
        "group inline-flex items-center gap-2 font-display text-xl font-semibold tracking-tight text-fg-base focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand focus-visible:ring-offset-2 focus-visible:ring-offset-bg-base rounded",
        className
      )}
      aria-label="DAMAY home"
    >
      <span
        aria-hidden
        className="relative inline-flex h-7 w-7 items-center justify-center rounded-full bg-brand text-white transition-transform duration-base ease-damay group-hover:scale-105"
      >
        <span className="block h-2.5 w-2.5 rounded-full bg-bg-base" />
      </span>
      <span>DAMAY</span>
    </Link>
  );
}
