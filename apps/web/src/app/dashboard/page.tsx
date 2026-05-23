import Link from "next/link";
import { Plus, Sparkles } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { RoundCard } from "@/components/brand/RoundCard";
import { EmptyState } from "@/components/brand/EmptyState";
import { OnChainBadge } from "@/components/brand/OnChainBadge";
import { fetchRounds } from "@/lib/api";
import { getSession } from "@/lib/auth";
import { seedContributionsByRound, seedMembers } from "@/lib/mock-data";
import { formatPhp, timeAgo } from "@/lib/utils";

export const dynamic = "force-dynamic";

export default async function DashboardPage() {
  const { organizer } = await getSession();
  const { data, isLive } = await fetchRounds();
  const rounds = data.data ?? [];

  // Recent activity — flatten all contributions, take 6 most recent.
  const recent = Object.values(seedContributionsByRound)
    .flat()
    .sort((a, b) => new Date(b.createdAt).getTime() - new Date(a.createdAt).getTime())
    .slice(0, 6);

  const firstName = organizer?.display_name.split(" ")[0] ?? "Organizer";

  return (
    <div className="container mx-auto px-5 py-10 lg:px-16 lg:py-14">
      <div className="flex flex-wrap items-end justify-between gap-6">
        <div>
          <h1 className="font-display text-4xl font-semibold tracking-tight text-fg-base sm:text-[2.75rem]">
            Kumusta, {firstName}.
          </h1>
          <p className="mt-2 text-base text-fg-muted">
            {rounds.length} round{rounds.length === 1 ? "" : "s"} active.
            {isLive ? null : (
              <span className="ml-2 inline-flex">
                <Badge variant="warning">Offline — demo data</Badge>
              </span>
            )}
          </p>
        </div>
        <Button asChild variant="primary" size="lg">
          <Link href="/dashboard/rounds/new">
            <Plus className="h-4 w-4" aria-hidden />
            Create round
          </Link>
        </Button>
      </div>

      <section className="mt-12">
        <h2 className="font-display text-3xl font-semibold tracking-tight text-fg-base">
          Active rounds
        </h2>

        {rounds.length === 0 ? (
          <div className="mt-6">
            <EmptyState
              icon={<Sparkles className="h-7 w-7" aria-hidden />}
              title="Wala pang round. Mag-start na?"
              body="Mag-create ng paluwagan circle para sa pamilya o barangay. Five minutes lang."
              action={
                <Button asChild variant="primary" size="lg">
                  <Link href="/dashboard/rounds/new">
                    <Plus className="h-4 w-4" aria-hidden /> Create round
                  </Link>
                </Button>
              }
            />
          </div>
        ) : (
          <div className="mt-6 grid gap-6 sm:grid-cols-2 xl:grid-cols-3">
            {rounds.map((r) => {
              const contribs = seedContributionsByRound[r.id] ?? [];
              const confirmed = contribs.filter((c) => c.status === "confirmed").length;
              return (
                <RoundCard
                  key={r.id}
                  round={r}
                  contributedCount={confirmed}
                  cycleNumber={Math.min(3, r.memberCount)}
                  cycleTotal={r.memberCount}
                  nextPayoutName={r.id === "rnd_kapitbahay" ? "Rey" : undefined}
                  nextPayoutInDays={r.id === "rnd_kapitbahay" ? 2 : undefined}
                  doneCopy={r.id === "rnd_tindera" ? "Done na — closing soon" : undefined}
                />
              );
            })}
          </div>
        )}
      </section>

      <section className="mt-14">
        <h2 className="font-display text-3xl font-semibold tracking-tight text-fg-base">
          Recent activity
        </h2>
        {recent.length === 0 ? (
          <Card className="mt-6 p-6 text-fg-muted">
            Walang pa activity. Pag-contribute si Carmela, lalabas dito.
          </Card>
        ) : (
          <Card className="mt-6 divide-y divide-border-subtle">
            {recent.map((c) => {
              const m = Object.values(seedMembers).find((mm) => mm.id === c.memberId);
              const roundName =
                c.roundId === "rnd_kapitbahay"
                  ? "Kapitbahay"
                  : c.roundId === "rnd_pamilya"
                    ? "Pamilya Pot"
                    : "Tindera Circle";
              return (
                <div key={c.id} className="flex items-center justify-between gap-4 px-6 py-4">
                  <div className="min-w-0">
                    <p className="text-base text-fg-base">
                      <span className="font-medium">{m?.displayName ?? "Member"}</span>{" "}
                      <span className="text-fg-muted">
                        nag-contribute {formatPhp(c.amountPhp)} to {roundName}
                      </span>
                    </p>
                  </div>
                  <div className="flex shrink-0 items-center gap-3">
                    <OnChainBadge txHash={c.stellarTxHash} status={c.status === "confirmed" ? "confirmed" : "pending"} />
                    <span className="text-xs text-fg-subtle">{timeAgo(c.createdAt)}</span>
                  </div>
                </div>
              );
            })}
          </Card>
        )}
      </section>
    </div>
  );
}
