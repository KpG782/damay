import { z } from "zod";

/**
 * Zod schemas mirror Pydantic shapes in apps/api. Hand-maintained; verified
 * against /home/user/damay/packages/types/src/index.ts.
 */

export const RoundFrequencySchema = z.enum(["weekly", "biweekly", "monthly"]);

export const CreateRoundSchema = z.object({
  name: z.string().min(2, "Pakilagyan ng name.").max(80),
  contributionAmountPhp: z.coerce
    .number()
    .int("Whole pesos lang muna.")
    .positive("Greater than zero.")
    .max(100_000),
  memberCount: z.coerce.number().int().min(2, "At least 2 members.").max(20),
  frequency: RoundFrequencySchema,
  startDate: z.string().regex(/^\d{4}-\d{2}-\d{2}$/, "Pakipili ng date."),
});
export type CreateRoundInput = z.infer<typeof CreateRoundSchema>;

export const AddMemberSchema = z.object({
  displayName: z.string().min(2, "Pakilagyan ng name.").max(60),
  whatsappE164: z
    .string()
    .regex(/^\+\d{8,15}$/, "Format: +639171234567"),
  payoutPosition: z.coerce.number().int().min(1).max(20),
});
export type AddMemberInput = z.infer<typeof AddMemberSchema>;

export const SimulateMessageSchema = z.object({
  from: z.string().regex(/^\+\d{8,15}$/, "Format: +639171234567"),
  body: z.string().min(1).max(280),
});
export type SimulateMessageInput = z.infer<typeof SimulateMessageSchema>;

export const LoginSchema = z.object({
  email: z.string().email("Hindi tama ang email."),
});
export type LoginInput = z.infer<typeof LoginSchema>;
