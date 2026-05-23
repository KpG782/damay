import Link from "next/link";
import { Button } from "@/components/ui/button";
import { EmptyState } from "@/components/brand/EmptyState";
import { Compass } from "lucide-react";

export default function NotFound() {
  return (
    <div className="container mx-auto px-5 py-16 lg:px-16">
      <EmptyState
        icon={<Compass className="h-7 w-7" aria-hidden />}
        title="Wala dito ang hinahanap mo."
        body="Baka mali ang link, o tinanggal na ang round."
        action={
          <Button asChild variant="primary">
            <Link href="/dashboard">Balik sa dashboard</Link>
          </Button>
        }
      />
    </div>
  );
}
