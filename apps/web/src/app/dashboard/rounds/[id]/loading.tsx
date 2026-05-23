import { Skeleton } from "@/components/ui/skeleton";

export default function RoundLoading() {
  return (
    <div className="container mx-auto px-5 py-10 lg:px-16 lg:py-14">
      <Skeleton className="h-5 w-40" />
      <Skeleton className="mt-6 h-12 w-80" />
      <Skeleton className="mt-3 h-5 w-72" />
      <div className="mt-10 grid gap-8 lg:grid-cols-[1.4fr_1fr]">
        <div className="space-y-8">
          <Skeleton className="h-96 w-full" />
          <Skeleton className="h-72 w-full" />
        </div>
        <div className="space-y-8">
          <Skeleton className="h-72 w-full" />
          <Skeleton className="h-64 w-full" />
        </div>
      </div>
    </div>
  );
}
