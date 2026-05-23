import Link from "next/link";
import { redirect } from "next/navigation";
import { Logo } from "@/components/brand/Logo";
import { Badge } from "@/components/ui/badge";
import { getSession } from "@/lib/auth";
import { isDemoMode } from "@/lib/env";

export default async function DashboardLayout({ children }: { children: React.ReactNode }) {
  const { organizer, isDemo } = await getSession();
  if (!organizer) {
    redirect("/login");
  }

  return (
    <div className="min-h-screen bg-bg-base">
      <header className="sticky top-0 z-20 border-b border-border-subtle bg-bg-raised/85 backdrop-blur supports-[backdrop-filter]:bg-bg-raised/70">
        <div className="container mx-auto flex items-center justify-between gap-4 px-5 py-4 lg:px-16">
          <div className="flex items-center gap-6">
            <Logo href="/dashboard" />
            {isDemo || isDemoMode ? (
              <Badge variant="warning" aria-label="Demo mode">
                Demo mode
              </Badge>
            ) : null}
          </div>
          <div className="flex items-center gap-3 text-sm">
            <span className="hidden text-fg-muted sm:inline">{organizer.display_name}</span>
            <Link
              href="/"
              className="rounded text-fg-muted transition-colors hover:text-fg-base focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand focus-visible:ring-offset-2 focus-visible:ring-offset-bg-raised px-2 py-1"
            >
              Sign out
            </Link>
          </div>
        </div>
      </header>
      <main>{children}</main>
    </div>
  );
}
