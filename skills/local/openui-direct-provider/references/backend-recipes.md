# Backend recipes (direct provider)

Read this when wiring step 4 of the workflow. Every recipe has the same shape:

1. Build `generateSystemPrompt({ library: spec, promptOptions })` once per request (or once at module load if it never changes).
2. Call the provider with that system prompt plus the conversation.
3. Stream text back in the protocol the frontend adapter expects.

Verify import paths against the installed packages. These are sketches, not
pinned APIs.

## Contents

- [OpenAI SDK, Chat Completions](#openai-sdk-chat-completions)
- [Vercel AI SDK, any provider](#vercel-ai-sdk-any-provider)
- [OpenAI-compatible and local endpoints](#openai-compatible-and-local-endpoints)
- [Plain text stream for a custom chat UI](#plain-text-stream-for-a-custom-chat-ui)
- [LangGraph and other agent frameworks](#langgraph-and-other-agent-frameworks)

## OpenAI SDK, Chat Completions

```ts
// app/api/chat/route.ts
import OpenAI from "openai";
import { generateSystemPrompt, type LibrarySpec } from "@openuidev/lang-core";
import spec from "@/lib/openui.spec.json";

const client = new OpenAI(); // reads OPENAI_API_KEY; no baseURL override
const system = generateSystemPrompt({ library: spec as LibrarySpec });

export async function POST(req: Request) {
  const { messages } = await req.json();
  const completion = await client.chat.completions.create(
    { model: process.env.OPENAI_MODEL ?? "gpt-5", stream: true,
      messages: [{ role: "system", content: system }, ...messages] },
    { signal: req.signal },
  );
  // toReadableStream() emits NDJSON (one chunk per line, no `data:` prefix)
  return new Response(completion.toReadableStream(), {
    headers: { "Content-Type": "application/x-ndjson" },
  });
}
```

Frontend: `fetchLLM({ url: "/api/chat", streamAdapter: openAIReadableStreamAdapter() })`.
If you forward raw SSE chunks instead of `toReadableStream()`, use `openAIAdapter()`.
For the Responses API, use `openAIResponsesAdapter()`.

## Vercel AI SDK, any provider

This is the most portable option: swap `@ai-sdk/openai` for `@ai-sdk/anthropic`,
`@ai-sdk/google`, and so on. It mirrors the official `openui-self-hosted` template's
`vercel-ai-sdk` overlay.

```ts
import { anthropic } from "@ai-sdk/anthropic";            // or openai / google / …
import { generateSystemPrompt } from "@openuidev/lang-core";
import { convertToModelMessages, createUIMessageStreamResponse, stepCountIs,
         streamText, toUIMessageStream, type UIMessage } from "ai";
import spec from "@/generated/spec.json";

export async function POST(req: Request) {
  const { messages } = (await req.json()) as { messages: UIMessage[] };
  const result = streamText({
    model: anthropic(process.env.MODEL_ID!),   // the provider's own model id
    system: generateSystemPrompt({ library: spec }),
    messages: await convertToModelMessages(messages),
    tools,                                       // agent-side tools, unchanged
    stopWhen: stepCountIs(5),
    abortSignal: req.signal,
  });
  return createUIMessageStreamResponse({ stream: toUIMessageStream({ stream: result.stream }) });
}
```

Frontend: `fetchLLM({ url: "/api/chat", streamAdapter: vercelAIAdapter(), messageFormat: vercelAIMessageFormat })`.

## OpenAI-compatible and local endpoints

For Ollama, vLLM, LM Studio, OpenRouter, Azure, and similar: keep the OpenAI
client and point it at **the user's** endpoint from env:

```ts
const client = new OpenAI({ baseURL: process.env.OPENAI_BASE_URL, apiKey: process.env.OPENAI_API_KEY });
// AI SDK: createOpenAI({ baseURL: process.env.OPENAI_BASE_URL, apiKey: … }).chat(modelId)
```

Small local models write noticeably more invalid OpenUI Lang. Keep the library
small, and set up the [self-repair loop](self-repair.md) from day one.

## Plain text stream for a custom chat UI

When the chat UI just accumulates text:

```ts
const encoder = new TextEncoder();
const body = new ReadableStream({
  async start(controller) {
    for await (const chunk of completion) {
      const text = chunk.choices[0]?.delta?.content;
      if (text) controller.enqueue(encoder.encode(text));
    }
    controller.close();
  },
});
return new Response(body, { headers: { "Content-Type": "text/plain; charset=utf-8" } });
```

The chat UI appends the text into `content` and passes it to `<Renderer isStreaming>`.

## LangGraph and other agent frameworks

Nothing about the agent loop changes. Append the generated OpenUI prompt to the
agent's system prompt, and keep its model client on the user's provider. Then
pick the matching frontend adapter: `langGraphAdapter()`, or `agUIAdapter()` for
AG-UI servers such as `@openuidev/langchain`. For the self-hosted LangGraph
wiring, see `templates/openui-self-hosted/` and
`examples/agent-frameworks/*` in the OpenUI repo. Ignore any `THESYS_API_KEY` /
`api.thesys.dev` lines in examples.
