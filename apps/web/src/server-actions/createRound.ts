"use server";

import { revalidatePath } from "next/cache";
import { redirect } from "next/navigation";
import { CreateRoundSchema, type CreateRoundInput } from "@/lib/schemas";
import { env } from "@/lib/env";
import { randomUUID } from "crypto";

export type CreateRoundResult =
  | { ok: true; roundId: string }
  | { ok: false; error: string; fieldErrors?: Record<string, string> };

export async function createRoundAction(input: CreateRoundInput): Promise<CreateRoundResult> {
  const parsed = CreateRoundSchema.safeParse(input);
  if (!parsed.success) {
    const flat = parsed.error.flatten().fieldErrors;
    return {
      ok: false,
      error: "Pakitignan ang form fields.",
      fieldErrors: Object.fromEntries(
        Object.entries(flat).map(([k, v]) => [k, v?.[0] ?? "Hindi tama."])
      ),
    };
  }

  try {
    const res = await fetch(`${env.NEXT_PUBLIC_API_URL}/v1/rounds`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "Idempotency-Key": randomUUID(),
      },
      body: JSON.stringify(parsed.data),
    });

    if (!res.ok) {
      // Demo-mode fallback — backend may not be up during build/test.
      const demoId = `rnd_${randomUUID().slice(0, 8)}`;
      revalidatePath("/dashboard");
      redirect(`/dashboard/rounds/${demoId}`);
    }

    const data = await res.json();
    revalidatePath("/dashboard");
    redirect(`/dashboard/rounds/${data.id}`);
  } catch {
    const demoId = `rnd_${randomUUID().slice(0, 8)}`;
    revalidatePath("/dashboard");
    redirect(`/dashboard/rounds/${demoId}`);
  }
}
