import { Skeleton } from "@/components/ui/skeleton";

export default function ReputationLoading() {
  return (
    <div className="container mx-auto max-w-3xl px-5 py-10 lg:px-16 lg:py-14">
      <Skeleton className="h-5 w-24" />
      <div className="mt-10 flex flex-col items-center">
        <Skeleton className="h-20 w-20 rounded-full" />
        <Skeleton className="mt-5 h-10 w-56" />
        <Skeleton className="mt-2 h-4 w-40" />
      </div>
      <Skeleton className="mx-auto mt-10 h-56 w-full max-w-md" />
      <Skeleton className="mt-10 h-40 w-full" />
      <Skeleton className="mt-10 h-72 w-full" />
    </div>
  );
}
