"use client";

import { useTransition } from "react";
import Link from "next/link";
import { ArrowLeft } from "lucide-react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { CreateRoundSchema, type CreateRoundInput } from "@/lib/schemas";
import { createRoundAction } from "@/server-actions/createRound";
import { toast } from "sonner";

export default function NewRoundPage() {
  const [pending, startTransition] = useTransition();
  const {
    register,
    handleSubmit,
    setValue,
    watch,
    formState: { errors },
  } = useForm<CreateRoundInput>({
    resolver: zodResolver(CreateRoundSchema),
    defaultValues: {
      name: "",
      contributionAmountPhp: 500,
      memberCount: 6,
      frequency: "weekly",
      startDate: new Date(Date.now() + 7 * 24 * 60 * 60 * 1000).toISOString().slice(0, 10),
    },
  });

  const frequency = watch("frequency");

  const onSubmit = (values: CreateRoundInput) => {
    startTransition(async () => {
      const res = await createRoundAction(values);
      if (!res.ok) {
        toast.error(res.error);
      }
      // success → server action redirects; no client toast needed.
    });
  };

  return (
    <div className="container mx-auto max-w-2xl px-5 py-10 lg:px-16 lg:py-14">
      <Link
        href="/dashboard"
        className="inline-flex items-center gap-1 rounded text-sm text-fg-muted transition-colors hover:text-fg-base focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand focus-visible:ring-offset-2 focus-visible:ring-offset-bg-base px-1 py-1"
      >
        <ArrowLeft className="h-4 w-4" aria-hidden /> Back to dashboard
      </Link>

      <h1 className="mt-6 font-display text-4xl font-semibold tracking-tight text-fg-base">
        Create round
      </h1>
      <p className="mt-2 text-base text-fg-muted">
        Mag-set up ng paluwagan. Pwede mong invite-an sina Carmela, Rey, at iba pa mamaya.
      </p>

      <Card className="mt-8">
        <CardHeader>
          <CardTitle className="font-sans text-2xl">Round details</CardTitle>
          <CardDescription>Ito yung papakita sa miyembro pag nag-join sila.</CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit(onSubmit)} className="space-y-5" noValidate>
            <div className="space-y-1.5">
              <Label htmlFor="name">Name</Label>
              <Input id="name" placeholder="hal: Kapitbahay Savings" {...register("name")} />
              {errors.name ? <p className="text-xs text-danger">{errors.name.message}</p> : null}
            </div>

            <div className="grid gap-5 sm:grid-cols-2">
              <div className="space-y-1.5">
                <Label htmlFor="amount">Contribution (₱)</Label>
                <Input
                  id="amount"
                  type="number"
                  inputMode="numeric"
                  min={1}
                  {...register("contributionAmountPhp")}
                />
                {errors.contributionAmountPhp ? (
                  <p className="text-xs text-danger">{errors.contributionAmountPhp.message}</p>
                ) : null}
              </div>
              <div className="space-y-1.5">
                <Label htmlFor="count">Member count</Label>
                <Input
                  id="count"
                  type="number"
                  inputMode="numeric"
                  min={2}
                  max={20}
                  {...register("memberCount")}
                />
                {errors.memberCount ? (
                  <p className="text-xs text-danger">{errors.memberCount.message}</p>
                ) : null}
              </div>
            </div>

            <div className="grid gap-5 sm:grid-cols-2">
              <div className="space-y-1.5">
                <Label htmlFor="freq">Frequency</Label>
                <select
                  id="freq"
                  value={frequency}
                  onChange={(e) => setValue("frequency", e.target.value as CreateRoundInput["frequency"])}
                  className="flex h-11 w-full rounded border border-border-base bg-bg-raised px-3 py-2 text-base text-fg-base shadow-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand focus-visible:ring-offset-2 focus-visible:ring-offset-bg-base"
                >
                  <option value="weekly">Weekly</option>
                  <option value="biweekly">Every 2 weeks</option>
                  <option value="monthly">Monthly</option>
                </select>
              </div>
              <div className="space-y-1.5">
                <Label htmlFor="start">Start date</Label>
                <Input id="start" type="date" {...register("startDate")} />
                {errors.startDate ? (
                  <p className="text-xs text-danger">{errors.startDate.message}</p>
                ) : null}
              </div>
            </div>

            <div className="flex items-center justify-end gap-3 pt-2">
              <Button asChild variant="ghost" type="button">
                <Link href="/dashboard">Cancel</Link>
              </Button>
              <Button type="submit" variant="primary" disabled={pending}>
                {pending ? "Creating..." : "Confirm pa"}
              </Button>
            </div>
          </form>
        </CardContent>
      </Card>
    </div>
  );
}
