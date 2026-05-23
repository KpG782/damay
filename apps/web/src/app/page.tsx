import Link from "next/link";
import { ArrowRight, Check, ShieldCheck, MessageCircle, Activity } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Logo } from "@/components/brand/Logo";
import { Badge } from "@/components/ui/badge";

export default function LandingPage() {
  return (
    <div className="relative min-h-screen overflow-hidden bg-bg-base">
      {/* Atmosphere: soft brand-tinted gradient + subtle grain */}
      <div
        aria-hidden
        className="pointer-events-none absolute inset-0 -z-10"
        style={{
          backgroundImage:
            "radial-gradient(60% 50% at 80% 0%, rgba(254, 215, 170, 0.45) 0%, rgba(254, 215, 170, 0) 60%), radial-gradient(40% 35% at 0% 100%, rgba(15, 118, 110, 0.10) 0%, rgba(15, 118, 110, 0) 60%)",
        }}
      />
      <div aria-hidden className="pointer-events-none absolute inset-0 -z-10 grain opacity-60" />

      <header className="container mx-auto flex items-center justify-between px-5 py-6 lg:px-16">
        <Logo />
        <nav className="flex items-center gap-3">
          <Link
            href="/login"
            className="rounded text-sm font-medium text-fg-muted transition-colors hover:text-fg-base focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand focus-visible:ring-offset-2 focus-visible:ring-offset-bg-base px-2 py-1"
          >
            Mag-sign in
          </Link>
          <Button asChild variant="primary" size="md">
            <Link href="/dashboard">
              Try the demo
              <ArrowRight className="h-4 w-4" aria-hidden />
            </Link>
          </Button>
        </nav>
      </header>

      <main className="container mx-auto px-5 pb-24 pt-10 lg:px-16 lg:pt-16">
        <section className="grid items-center gap-12 lg:grid-cols-[1.15fr_1fr]">
          <div>
            <Badge variant="neutral" className="bg-bg-subtle text-fg-muted">
              <span className="font-mono text-[10px] tracking-widest uppercase">Stellar PH Hackathon</span>
            </Badge>
            <h1 className="mt-5 font-display text-5xl font-semibold leading-[1.05] tracking-tight text-fg-base sm:text-[3.75rem] lg:text-[4.25rem] text-balance">
              Paluwagan,{" "}
              <span className="relative inline-block">
                <span className="relative z-10">naka-record sa Stellar.</span>
                <span
                  aria-hidden
                  className="absolute inset-x-0 bottom-1 -z-0 h-3 rounded-sm bg-brand-subtle/70"
                />
              </span>
            </h1>
            <p className="mt-6 max-w-xl text-lg leading-relaxed text-fg-muted">
              Filipino savings circles, na hindi nababasag pag may nag-ghost. Mga miyembro nasa WhatsApp pa rin — yung trust na lang ang nasa Stellar.
            </p>
            <div className="mt-8 flex flex-wrap items-center gap-3">
              <Button asChild variant="primary" size="lg">
                <Link href="/dashboard">
                  Try the demo
                  <ArrowRight className="h-4 w-4" aria-hidden />
                </Link>
              </Button>
              <Button asChild variant="secondary" size="lg">
                <Link href="/login">Mag-sign in bilang organizer</Link>
              </Button>
            </div>
            <ul className="mt-10 grid max-w-xl gap-3 text-sm text-fg-muted sm:grid-cols-2">
              {[
                "Walang KYC. Testnet muna.",
                "Members nasa WhatsApp pa rin.",
                "Reputation naka-record on-chain.",
                "Audit-friendly bawat contribution.",
              ].map((line) => (
                <li key={line} className="flex items-start gap-2">
                  <span className="mt-0.5 flex h-5 w-5 shrink-0 items-center justify-center rounded-full bg-accent/10 text-accent">
                    <Check className="h-3 w-3" aria-hidden />
                  </span>
                  <span>{line}</span>
                </li>
              ))}
            </ul>
          </div>

          {/* Right panel: stylized device mock-up */}
          <div className="relative">
            <div
              aria-hidden
              className="absolute -inset-x-6 -inset-y-8 -z-10 rounded-[32px]"
              style={{
                background:
                  "linear-gradient(135deg, rgba(254, 215, 170, 0.35), rgba(15, 118, 110, 0.08) 70%)",
              }}
            />
            <div className="rounded-xl border border-border-base bg-bg-raised p-7 shadow-lg">
              <div className="flex items-center justify-between">
                <div className="font-display text-xl font-semibold text-fg-base">Kapitbahay Savings</div>
                <Badge variant="accent">
                  <Check className="h-3 w-3" aria-hidden /> On-chain
                </Badge>
              </div>
              <p className="mt-1 text-sm text-fg-muted">Cycle 3 of 6 · ₱500/week</p>
              <div className="mt-5 flex items-center gap-1.5" aria-hidden>
                {[true, true, true, true, false, false].map((on, i) => (
                  <span
                    key={i}
                    className={
                      "h-2.5 w-2.5 rounded-full " +
                      (on ? "bg-success" : "bg-bg-subtle border border-border-base")
                    }
                  />
                ))}
                <span className="ml-2 text-sm text-fg-muted">4 of 6 contributed</span>
              </div>
              <ul className="mt-6 divide-y divide-border-subtle">
                {[
                  { name: "Carmela", time: "Mon 9:14am", status: "confirmed" as const },
                  { name: "Rey", time: "Mon 11:02am", status: "confirmed" as const },
                  { name: "Joelle", time: "Tue 7:48am", status: "confirmed" as const },
                  { name: "Marites", time: "sent reminder", status: "pending" as const },
                ].map((row) => (
                  <li key={row.name} className="flex items-center justify-between gap-3 py-3 text-sm">
                    <span className="text-fg-base">{row.name} contributed ₱500</span>
                    <Badge variant={row.status === "confirmed" ? "accent" : "warning"}>
                      {row.status === "confirmed" ? (
                        <>
                          <Check className="h-3 w-3" aria-hidden /> On-chain
                        </>
                      ) : (
                        "Pending"
                      )}
                    </Badge>
                  </li>
                ))}
              </ul>
              <div className="mt-6 rounded-md border border-border-subtle bg-bg-subtle px-4 py-3 font-mono text-xs text-fg-muted">
                contract: GCXY7…K9P2
              </div>
            </div>
          </div>
        </section>

        <section className="mt-24 grid gap-6 sm:grid-cols-3">
          {[
            {
              icon: MessageCircle,
              title: "Members nasa WhatsApp.",
              body: "Walang bagong app na kailangan i-install. Reply lang ng PAY at done na.",
            },
            {
              icon: ShieldCheck,
              title: "Trust nasa Stellar.",
              body: "Bawat contribution at payout naka-record on-chain. Reusable reputation trustline.",
            },
            {
              icon: Activity,
              title: "Organizer nakikita lahat.",
              body: "Real-time timeline. Sino nag-send, sino hindi pa, lahat verifiable.",
            },
          ].map(({ icon: Icon, title, body }) => (
            <article key={title} className="rounded-md border border-border-subtle bg-bg-raised p-6 shadow-sm">
              <div className="flex h-10 w-10 items-center justify-center rounded-full bg-bg-subtle text-fg-muted">
                <Icon className="h-5 w-5" aria-hidden />
              </div>
              <h3 className="mt-4 font-sans text-xl font-semibold text-fg-base">{title}</h3>
              <p className="mt-2 text-sm text-fg-muted">{body}</p>
            </article>
          ))}
        </section>
      </main>

      <footer className="container mx-auto flex flex-col items-start justify-between gap-3 border-t border-border-subtle px-5 py-8 text-sm text-fg-subtle lg:flex-row lg:items-center lg:px-16">
        <p>DAMAY · Paluwagan by Damay · Built for Stellar Philippines Hackathon</p>
        <p className="font-mono text-xs">testnet · v0.1.0</p>
      </footer>
    </div>
  );
}
