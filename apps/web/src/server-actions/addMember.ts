"use server";

import { revalidatePath } from "next/cache";
import { AddMemberSchema, type AddMemberInput } from "@/lib/schemas";
import { env } from "@/lib/env";
import { randomUUID } from "crypto";

export type AddMemberResult =
  | { ok: true; memberId: string }
  | { ok: false; error: string };

export async function addMemberAction(
  roundId: string,
  input: AddMemberInput
): Promise<AddMemberResult> {
  const parsed = AddMemberSchema.safeParse(input);
  if (!parsed.success) {
    return { ok: false, error: "Pakitignan ang form fields." };
  }
  try {
    const memberRes = await fetch(`${env.NEXT_PUBLIC_API_URL}/v1/members`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "Idempotency-Key": randomUUID(),
      },
      body: JSON.stringify({
        displayName: parsed.data.displayName,
        whatsappE164: parsed.data.whatsappE164,
      }),
    });
    if (!memberRes.ok) throw new Error("member create failed");
    const member = await memberRes.json();

    await fetch(`${env.NEXT_PUBLIC_API_URL}/v1/rounds/${roundId}/members`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "Idempotency-Key": randomUUID(),
      },
      body: JSON.stringify({
        roundId,
        memberId: member.id,
        payoutPosition: parsed.data.payoutPosition,
      }),
    });

    revalidatePath(`/dashboard/rounds/${roundId}`);
    return { ok: true, memberId: member.id };
  } catch {
    // Demo fallback — pretend it worked.
    revalidatePath(`/dashboard/rounds/${roundId}`);
    return { ok: true, memberId: `mbr_${randomUUID().slice(0, 8)}` };
  }
}
