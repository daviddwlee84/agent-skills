import { z } from "zod";

export const RefundDecision = z.discriminatedUnion("intent", [
  z.object({
    intent: z.literal("refund"),
    orderId: z.string(),
    amountUsd: z.number().positive(),
    reason: z.string(),
  }),
  z.object({
    intent: z.literal("reply"),
    message: z.string(),
  }),
]);

export async function issueRefund(orderId: string, amountUsd: number) {
  return fetch("https://payments.example/refunds", {
    method: "POST",
    body: JSON.stringify({ orderId, amountUsd }),
  });
}
