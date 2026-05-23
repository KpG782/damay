import Link from "next/link";
import { ArrowLeft, ExternalLink } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { OnChainBadge } from "@/components/brand/OnChainBadge";
import { ReputationScore } from "@/components/brand/ReputationScore";
import { EmptyState } from "@/components/brand/EmptyState";
import { fetchReputation } from "@/lib/api";
import { seedMemberById } from "@/lib/mock-data";
import { stellarExpertAccountUrl } from "@/lib/stellar";
import { initials, timeAgo } from "@/lib/utils";
import { Star } from "lucide-react";

export const dynamic = "force-dynamic";

interface PageProps {
  params: Promise<{ memberId: string }>;
}

export default async function ReputationPage({ params }: PageProps) {
  const { memberId } = await params;
  const { data } = await fetchReputation(memberId);
  const member = seedMemberById(memberId);
  const isEmpty = data.events.length === 0;

  const latest = data.events[0];
  const weeklyContribs = data.events.filter(
    (e) => e.eventType === "contribution" && Date.now() - new Date(e.createdAt).getTime() < 7 * 24 * 60 * 60 * 1000
  );
  const weeklyDelta = weeklyContribs.reduce((acc, e) => acc + e.weight, 0);

  return (
    <div className="container mx-auto max-w-3xl px-5 py-10 lg:px-16 lg:py-14">
      <Link
        href="/dashboard"
        className="inline-flex items-center gap-1 rounded text-sm text-fg-muted transition-colors hover:text-fg-base focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand focus-visible:ring-offset-2 focus-visible:ring-offset-bg-base px-1 py-1"
      >
        <ArrowLeft className="h-4 w-4" aria-hidden /> Back
      </Link>

      <header className="mt-10 flex flex-col items-center text-center">
        <div className="flex h-20 w-20 items-center justify-center rounded-full bg-bg-subtle font-display text-2xl text-fg-muted">
          {initials(member?.displayName ?? "Member")}
        </div>
        <h1 className="mt-5 font-display text-4xl font-semibold tracking-tight text-fg-base">
          {member?.displayName ?? "Member"}
        </h1>
        <p className="mt-1 text-sm text-fg-muted">
          {member ? `Member since ${new Date(member.createdAt).toLocaleDateString("en-PH", { month: "short", year: "numeric" })}` : "Member"}
        </p>
      </header>

      <div className="mt-10">
        <ReputationScore
          score={data.score}
          weeklyDelta={weeklyDelta > 0 ? weeklyDelta : undefined}
          weeklyContribs={weeklyContribs.length || undefined}
          contractId={member?.stellarAccount ?? null}
          latestTxHash={latest?.stellarTxHash ?? null}
          empty={isEmpty}
        />
      </div>

      <Card className="mt-10">
        <CardHeader>
          <CardTitle className="font-display text-2xl">How this score works</CardTitle>
        </CardHeader>
        <CardContent>
          <ul className="space-y-2 text-base text-fg-muted">
            <li>
              <span className="font-mono font-semibold text-success">+10</span> bawat on-time contribution
            </li>
            <li>
              <span className="font-mono font-semibold text-success">+1</span> bawat payout natanggap nang tama
            </li>
            <li>
              <span className="font-mono font-semibold text-danger">−25</span> kapag nag-default (hindi nakapag-contribute)
            </li>
            <li>Decays 1% kada 30 days kapag tahimik.</li>
          </ul>
          <p className="mt-4 text-sm text-fg-subtle">
            Naka-record lahat sa Stellar — hindi pwedeng i-edit.
          </p>
        </CardContent>
      </Card>

      <section className="mt-10">
        <h2 className="font-display text-2xl font-semibold tracking-tight text-fg-base">
          History
        </h2>
        {isEmpty ? (
          <div className="mt-4">
            <EmptyState
              icon={<Star className="h-7 w-7" aria-hidden />}
              title="Walang pa history."
              body={`Pag-contribute si ${member?.displayName ?? "siya"}, lalabas dito ang lahat — naka-record sa Stellar.`}
            />
          </div>
        ) : (
          <Card className="mt-4">
            <ul className="divide-y divide-border-subtle">
              {data.events.map((e) => {
                const positive = e.weight > 0;
                const label =
                  e.eventType === "contribution"
                    ? "Contribution"
                    : e.eventType === "payout"
                      ? "Payout received"
                      : "Default";
                const round = (e.context?.round as string) ?? "—";
                return (
                  <li
                    key={e.id}
                    className="flex flex-wrap items-center gap-3 px-6 py-4"
                  >
                    <span
                      className={
                        "w-12 shrink-0 font-mono text-base font-semibold " +
                        (positive ? "text-success" : "text-danger")
                      }
                    >
                      {positive ? "+" : ""}
                      {e.weight}
                    </span>
                    <div className="min-w-0 flex-1">
                      <p className="text-base text-fg-base">{label}</p>
                      <p className="text-sm text-fg-muted">{round}</p>
                    </div>
                    <OnChainBadge txHash={e.stellarTxHash} />
                    <span className="text-xs text-fg-subtle">{timeAgo(e.createdAt)}</span>
                  </li>
                );
              })}
            </ul>
          </Card>
        )}
      </section>

      {member?.stellarAccount ? (
        <div className="mt-10">
          <a
            href={stellarExpertAccountUrl(member.stellarAccount)}
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center gap-2 rounded text-sm font-medium text-accent underline-offset-4 hover:underline hover:text-accent-hover focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand focus-visible:ring-offset-2 focus-visible:ring-offset-bg-base px-1 py-1"
          >
            Verify lahat sa Stellar Expert
            <ExternalLink className="h-4 w-4" aria-hidden />
          </a>
        </div>
      ) : null}
    </div>
  );
}
