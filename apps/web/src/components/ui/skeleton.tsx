import { cn } from "@/lib/utils";

function Skeleton({ className, ...props }: React.HTMLAttributes<HTMLDivElement>) {
  return (
    <div
      className={cn(
        "relative overflow-hidden rounded bg-bg-subtle",
        "before:absolute before:inset-0 before:-translate-x-full before:animate-[shimmer_1.6s_cubic-bezier(0.2,0.8,0.2,1)_infinite]",
        "before:bg-gradient-to-r before:from-transparent before:via-white/60 before:to-transparent",
        className
      )}
      {...props}
    />
  );
}

export { Skeleton };
