import Link from "next/link";
import { ArrowLeft, UserPlus, ExternalLink } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { OnChainBadge } from "@/components/brand/OnChainBadge";
import { ContributionTimeline } from "@/components/brand/ContributionTimeline";
import { DemoSimulator } from "@/components/brand/DemoSimulator";
import { EmptyState } from "@/components/brand/EmptyState";
import { fetchRound } from "@/lib/api";
import { stellarExpertContractUrl } from "@/lib/stellar";
import { formatPhp, truncateHash } from "@/lib/utils";
import type { Member } from "@damay/types";
import { Inbox } from "lucide-react";

export const dynamic = "force-dynamic";

interface PageProps {
  params: Promise<{ id: string }>;
}

export default async function RoundDetailPage({ params }: PageProps) {
  const { id } = await params;
  const { data: round } = await fetchRound(id);

  const membersById: Record<string, Member> = {};
  for (const rm of round.members) membersById[rm.memberId] = rm.member;

  const currentCycle = Math.max(1, Math.min(round.memberCount, 3));
  const cycleContribs = round.contributions.filter((c) => c.cycleNumber === currentCycle);
  const confirmed = cycleContribs.filter((c) => c.status === "confirmed");
  const contributedMemberIds = new Set(cycleContribs.map((c) => c.memberId));
  const allConfirmed = confirmed.length === round.memberCount && round.memberCount > 0;
  const potCollected = confirmed.reduce((acc, c) => acc + c.amountPhp, 0);
  const potTarget = round.contributionAmountPhp * round.memberCount;

  const isEmptyRound = round.members.length === 0;

  return (
    <div className="container mx-auto px-5 py-10 lg:px-16 lg:py-14">
      <div className="flex items-center justify-between gap-4">
        <Link
          href="/dashboard"
          className="inline-flex items-center gap-1 rounded text-sm text-fg-muted transition-colors hover:text-fg-base focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand focus-visible:ring-offset-2 focus-visible:ring-offset-bg-base px-1 py-1"
        >
          <ArrowLeft className="h-4 w-4" aria-hidden /> Back to dashboard
        </Link>
      </div>

      <header className="mt-6 flex flex-wrap items-start justify-between gap-6">
        <div>
          <h1 className="font-display text-4xl font-semibold tracking-tight text-fg-base">
            {round.name}
          </h1>
          <p className="mt-2 text-base text-fg-muted">
            Cycle {currentCycle} of {round.memberCount} · {formatPhp(round.contributionAmountPhp)}/
            {round.frequency === "weekly" ? "week" : round.frequency === "biweekly" ? "2 weeks" : "month"} ·{" "}
            {round.memberCount} members
          </p>
          {round.paluwaganContractId ? (
            <div className="mt-3 flex items-center gap-2">
              <span className="font-mono text-xs text-fg-muted">
                Contract: {truncateHash(round.paluwaganContractId, 6, 6)}
              </span>
              <a
                href={stellarExpertContractUrl(round.paluwaganContractId)}
                target="_blank"
                rel="noopener noreferrer"
                className="rounded focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand"
              >
                <OnChainBadge txHash={round.paluwaganContractId} label="Verified" />
              </a>
            </div>
          ) : null}
        </div>
        <Button variant="primary" size="md">
          <UserPlus className="h-4 w-4" aria-hidden /> Invite member
        </Button>
      </header>

      {isEmptyRound ? (
        <div className="mt-10">
          <EmptyState
            icon={<Inbox className="h-7 w-7" aria-hidden />}
            title="Walang pa member dito."
            body="I-invite na natin sila. Para makakita ng demo flow, dito sa kanan ay may simulator."
            action={
              <Button variant="primary">
                <UserPlus className="h-4 w-4" aria-hidden /> Send invite
              </Button>
            }
          />
        </div>
      ) : (
        <div className="mt-10 grid gap-8 lg:grid-cols-[1.4fr_1fr]">
          <div className="space-y-8">
            <Card>
              <CardHeader>
                <CardTitle className="font-display text-2xl">
                  This cycle{" "}
                  <span className="text-base font-normal text-fg-muted">
                    (closes in {3 - (currentCycle % 4)} days)
                  </span>
                </CardTitle>
              </CardHeader>
              <CardContent className="pt-0">
                <ul className="divide-y divide-border-subtle">
                  {round.members.map((rm) => {
                    const member = rm.member;
                    const contrib = cycleContribs.find((c) => c.memberId === rm.memberId);
                    const contributed = contributedMemberIds.has(rm.memberId);
                    const isPending = contrib?.status === "pending";
                    const isConfirmed = contrib?.status === "confirmed";

                    return (
                      <li
                        key={rm.memberId}
                        className="flex flex-wrap items-center gap-3 py-3 first:pt-0 last:pb-0"
                      >
                        <span
                          className={
                            "inline-block h-2.5 w-2.5 shrink-0 rounded-full " +
                            (isConfirmed
                              ? "bg-success"
                              : isPending
                                ? "bg-warning"
                                : "bg-bg-subtle border border-border-base")
                          }
                          aria-hidden
                        />
                        <div className="min-w-0 flex-1">
                          <Link
                            href={`/dashboard/reputation/${member.id}`}
                            className="rounded text-base font-medium text-fg-base hover:text-accent focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand"
                          >
                            {member.displayName}
                          </Link>
                          <p className="font-mono text-xs text-fg-subtle">
                            {member.whatsappE164}
                          </p>
                        </div>
                        <div className="text-sm text-fg-muted">{formatPhp(round.contributionAmountPhp)}</div>
                        <div className="text-sm text-fg-muted">
                          {isConfirmed ? "Done na" : isPending ? "Pending" : "Hindi pa"}
                        </div>
                        {isConfirmed ? (
                          <OnChainBadge txHash={contrib!.stellarTxHash} />
                        ) : isPending ? (
                          <OnChainBadge txHash={null} status="pending" />
                        ) : (
                          <Button variant="ghost" size="sm">
                            Send pa
                          </Button>
                        )}
                      </li>
                    );
                  })}
                </ul>

                <div className="mt-5 flex flex-wrap items-center justify-between gap-3 border-t border-border-subtle pt-4 text-sm text-fg-muted">
                  <p>
                    Pot this cycle:{" "}
                    <span className="font-medium text-fg-base">
                      {formatPhp(potCollected)} of {formatPhp(potTarget)}
                    </span>
                  </p>
                  <p>
                    Next payout:{" "}
                    <span className="font-medium text-fg-base">
                      {round.members[currentCycle - 1]?.member.displayName ?? "—"}
                    </span>
                  </p>
                </div>

                <div className="mt-5 flex justify-end">
                  <Button variant={allConfirmed ? "primary" : "secondary"} disabled={!allConfirmed}>
                    Trigger payout
                  </Button>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="font-display text-2xl">Payout schedule</CardTitle>
              </CardHeader>
              <CardContent className="pt-0">
                <ul className="divide-y divide-border-subtle">
                  {round.members.map((rm, idx) => {
                    const payout = round.payouts.find((p) => p.memberId === rm.memberId);
                    const upNext = idx + 1 === currentCycle;
                    return (
                      <li
                        key={rm.memberId}
                        className={
                          "flex flex-wrap items-center gap-3 py-3 first:pt-0 last:pb-0 " +
                          (upNext ? "-mx-6 rounded-md bg-bg-subtle px-6" : "")
                        }
                      >
                        <span className="w-6 text-sm font-medium text-fg-muted">#{idx + 1}</span>
                        <span className="min-w-0 flex-1 text-base text-fg-base">
                          {rm.member.displayName}
                        </span>
                        <span className="text-sm text-fg-muted">
                          {formatPhp(round.contributionAmountPhp * round.memberCount)}
                        </span>
                        {payout?.status === "confirmed" ? (
                          <>
                            <span className="text-sm text-success">Done na</span>
                            <OnChainBadge txHash={payout.stellarTxHash} />
                          </>
                        ) : upNext ? (
                          <Badge variant="warning">Up next</Badge>
                        ) : (
                          <span className="text-sm text-fg-subtle">scheduled</span>
                        )}
                      </li>
                    );
                  })}
                </ul>
              </CardContent>
            </Card>
          </div>

          <div className="space-y-8">
            <DemoSimulator
              members={round.members.map((rm) => ({
                id: rm.member.id,
                displayName: rm.member.displayName,
                whatsappE164: rm.member.whatsappE164,
              }))}
            />

            <ContributionTimeline
              roundId={round.id}
              initial={round.contributions.sort(
                (a, b) => new Date(b.createdAt).getTime() - new Date(a.createdAt).getTime()
              )}
              membersById={membersById}
            />

            {round.paluwaganContractId ? (
              <a
                href={stellarExpertContractUrl(round.paluwaganContractId)}
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex items-center gap-2 rounded text-sm font-medium text-accent underline-offset-4 hover:underline focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand focus-visible:ring-offset-2 focus-visible:ring-offset-bg-base px-1 py-1"
              >
                Verify lahat sa Stellar Expert
                <ExternalLink className="h-4 w-4" aria-hidden />
              </a>
            ) : null}
          </div>
        </div>
      )}
    </div>
  );
}
