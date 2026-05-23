import { Skeleton } from "@/components/ui/skeleton";

export default function DashboardLoading() {
  return (
    <div className="container mx-auto px-5 py-10 lg:px-16 lg:py-14">
      <div className="flex flex-wrap items-end justify-between gap-6">
        <div>
          <Skeleton className="h-12 w-72" />
          <Skeleton className="mt-3 h-5 w-40" />
        </div>
        <Skeleton className="h-12 w-44" />
      </div>
      <Skeleton className="mt-12 h-8 w-48" />
      <div className="mt-6 grid gap-6 sm:grid-cols-2 xl:grid-cols-3">
        {Array.from({ length: 3 }).map((_, i) => (
          <Skeleton key={i} className="h-64 w-full" />
        ))}
      </div>
      <Skeleton className="mt-14 h-8 w-48" />
      <Skeleton className="mt-6 h-48 w-full" />
    </div>
  );
}
