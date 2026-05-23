"use client";

import { useState } from "react";
import Link from "next/link";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Logo } from "@/components/brand/Logo";
import { LoginSchema, type LoginInput } from "@/lib/schemas";
import { getBrowserSupabase } from "@/lib/supabase";
import { isDemoMode } from "@/lib/env";
import { toast } from "sonner";

export default function LoginPage() {
  const [sent, setSent] = useState(false);
  const [pending, setPending] = useState(false);

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<LoginInput>({ resolver: zodResolver(LoginSchema) });

  async function onSubmit(values: LoginInput) {
    setPending(true);
    try {
      const supabase = getBrowserSupabase();
      if (!supabase || isDemoMode) {
        // Demo mode — pretend we sent the link and let the user click through.
        setSent(true);
        toast.success("Demo mode — pretend magic link sent.");
        return;
      }
      const { error } = await supabase.auth.signInWithOtp({
        email: values.email,
        options: {
          emailRedirectTo: `${window.location.origin}/callback`,
        },
      });
      if (error) throw error;
      setSent(true);
      toast.success("Magic link sent. Check your inbox.");
    } catch (err) {
      toast.error("Hindi naipadala. Subukan ulit.");
      // eslint-disable-next-line no-console
      console.error(err);
    } finally {
      setPending(false);
    }
  }

  return (
    <div className="min-h-screen bg-bg-base">
      <header className="container mx-auto px-5 py-6 lg:px-16">
        <Logo />
      </header>
      <main className="container mx-auto flex max-w-md flex-col px-5 pb-20 pt-8 lg:px-0">
        <Card>
          <CardHeader>
            <CardTitle className="font-display text-3xl">Mag-sign in</CardTitle>
            <CardDescription>
              Para sa mga organizer lang. Members, WhatsApp pa rin kayo.
            </CardDescription>
          </CardHeader>
          <CardContent>
            {sent ? (
              <div className="space-y-4">
                <p className="text-base text-fg-base">
                  Naipadala na ang magic link sa email mo. Pakitignan ang inbox.
                </p>
                {isDemoMode ? (
                  <Button asChild variant="primary" className="w-full">
                    <Link href="/dashboard">Pumunta sa dashboard (demo)</Link>
                  </Button>
                ) : null}
                <Button variant="ghost" onClick={() => setSent(false)} className="w-full">
                  Mag-send ulit
                </Button>
              </div>
            ) : (
              <form onSubmit={handleSubmit(onSubmit)} className="space-y-4" noValidate>
                <div className="space-y-1.5">
                  <Label htmlFor="email">Email</Label>
                  <Input
                    id="email"
                    type="email"
                    inputMode="email"
                    autoComplete="email"
                    placeholder="ikaw@halimbawa.com"
                    {...register("email")}
                  />
                  {errors.email ? (
                    <p className="text-xs text-danger">{errors.email.message}</p>
                  ) : null}
                </div>
                <Button type="submit" variant="primary" className="w-full" disabled={pending}>
                  {pending ? "Sending..." : "Send magic link"}
                </Button>
                <p className="text-center text-xs text-fg-subtle">
                  Walang password. I-click lang ang link sa email.
                </p>
              </form>
            )}
          </CardContent>
        </Card>
        <p className="mt-6 text-center text-sm text-fg-muted">
          Bago ka pa lang sa DAMAY?{" "}
          <Link href="/" className="text-accent underline-offset-4 hover:underline">
            Balik sa intro
          </Link>
        </p>
      </main>
    </div>
  );
}
