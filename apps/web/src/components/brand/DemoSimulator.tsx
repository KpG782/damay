"use client";

import { useState, useTransition } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { Send } from "lucide-react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
import { SimulateMessageSchema, type SimulateMessageInput } from "@/lib/schemas";
import { simulateMessageAction } from "@/server-actions/simulateMessage";
import { toast } from "sonner";

interface DemoSimulatorProps {
  members: Array<{ id: string; displayName: string; whatsappE164: string }>;
}

/**
 * Organizer-visible widget on round detail. Drives the demo without needing
 * a paired WhatsApp number — hits POST /v1/dev/simulate-message via a Server Action.
 */
export function DemoSimulator({ members }: DemoSimulatorProps) {
  const [pending, startTransition] = useTransition();
  const [lastSid, setLastSid] = useState<string | null>(null);

  const {
    register,
    handleSubmit,
    setValue,
    watch,
    formState: { errors },
  } = useForm<SimulateMessageInput>({
    resolver: zodResolver(SimulateMessageSchema),
    defaultValues: {
      from: members[0]?.whatsappE164 ?? "+639171000001",
      body: "PAY",
    },
  });

  const selectedFrom = watch("from");

  const onSubmit = (values: SimulateMessageInput) => {
    startTransition(async () => {
      const res = await simulateMessageAction(values);
      if (res.ok) {
        setLastSid(res.twilioSid);
        toast.success("Simulated message sent", {
          description: `Twilio SID ${res.twilioSid}`,
        });
      } else {
        toast.error("Hindi naipadala", { description: res.error });
      }
    });
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-xl">Simulate member message</CardTitle>
        <CardDescription>
          Demo backdoor. Pumili ng member at i-send ang "PAY" para makita ang flow nang walang Twilio pairing.
        </CardDescription>
      </CardHeader>
      <CardContent>
        <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
          <div className="space-y-1.5">
            <Label htmlFor="sim-from">Member</Label>
            <select
              id="sim-from"
              {...register("from")}
              className="flex h-11 w-full rounded border border-border-base bg-bg-raised px-3 py-2 text-base text-fg-base shadow-sm transition-colors duration-fast ease-damay focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand focus-visible:ring-offset-2 focus-visible:ring-offset-bg-base"
              onChange={(e) => setValue("from", e.target.value)}
              value={selectedFrom}
            >
              {members.map((m) => (
                <option key={m.id} value={m.whatsappE164}>
                  {m.displayName} — {m.whatsappE164}
                </option>
              ))}
            </select>
            {errors.from ? <p className="text-xs text-danger">{errors.from.message}</p> : null}
          </div>

          <div className="space-y-1.5">
            <Label htmlFor="sim-body">Message body</Label>
            <Input id="sim-body" {...register("body")} placeholder="PAY" />
            {errors.body ? <p className="text-xs text-danger">{errors.body.message}</p> : null}
          </div>

          <div className="flex items-center justify-between gap-3">
            <Button type="submit" disabled={pending} variant="primary">
              <Send className="h-4 w-4" aria-hidden />
              {pending ? "Sending..." : "Send simulated PAY"}
            </Button>
            {lastSid ? (
              <Badge variant="success">
                Sent · <span className="font-mono">{lastSid}</span>
              </Badge>
            ) : null}
          </div>
        </form>
      </CardContent>
    </Card>
  );
}
