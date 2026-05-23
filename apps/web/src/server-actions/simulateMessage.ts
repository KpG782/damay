"use server";

import { revalidatePath } from "next/cache";
import { postSimulateMessage } from "@/lib/api";
import { SimulateMessageSchema, type SimulateMessageInput } from "@/lib/schemas";

export type SimulateMessageResult =
  | { ok: true; twilioSid: string }
  | { ok: false; error: string };

export async function simulateMessageAction(
  input: SimulateMessageInput
): Promise<SimulateMessageResult> {
  const parsed = SimulateMessageSchema.safeParse(input);
  if (!parsed.success) {
    return { ok: false, error: "Pakitignan ang form fields." };
  }
  try {
    const { data } = await postSimulateMessage(parsed.data);
    revalidatePath("/dashboard", "layout");
    return { ok: true, twilioSid: data.twilioSid };
  } catch {
    return { ok: false, error: "Hindi maabot ang backend. Subukan ulit." };
  }
}
