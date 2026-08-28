import OpenAI from "openai";
import { issueRefund } from "./tools";
import { loadThread, saveThread } from "./state";

const client = new OpenAI();
const SYSTEM_PROMPT = "You are a refund agent. Decide what to do next.";

export async function runRefundAgent(threadId: string, request: string) {
  const thread = loadThread(threadId);
  thread.messages.push({ role: "user", content: request });

  while (true) {
    const response = await client.chat.completions.create({
      model: "gpt-4.1",
      messages: [
        { role: "system", content: SYSTEM_PROMPT },
        ...thread.messages,
      ],
      response_format: { type: "json_object" },
    });
    const next = JSON.parse(response.choices[0].message.content ?? "{}");
    thread.messages.push({ role: "assistant", content: JSON.stringify(next) });

    if (next.intent === "refund") {
      await issueRefund(next.orderId, next.amountUsd);
      thread.messages.push({ role: "tool", content: "refund issued" });
      continue;
    }
    if (next.intent === "reply") {
      saveThread(thread);
      return next.message;
    }
  }
}
