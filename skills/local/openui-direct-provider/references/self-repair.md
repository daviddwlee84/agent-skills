# Repairing invalid OpenUI Lang without a hosted service

Read this when the renderer shows blank or partial UI, when `onError` fires, or
when you're hardening an app for production.

Without Gateway, nothing rewrites bad output while it streams. Use three layers,
cheapest first.

## 1. Prevent

- Short, specific `description` on every component. It is printed in the prompt.
- Group related components with `createLibrary({ componentGroups: [...] })`.
- Keep the library small. Every component and prop adds prompt tokens and chances to get it wrong.
- Add `promptOptions.examples` / `additionalRules` for the patterns the model keeps getting wrong.
- Use `root` so output always starts with a known container.

## 2. Detect, once, after the stream ends

Server side, with the same spec as the renderer:

```ts
import { createStreamingParser, type ParseResult } from "@openuidev/lang-core";

const parser = createStreamingParser(spec.schema, spec.root);
let result: ParseResult = parser.getResult();
for await (const delta of textDeltas) { result = parser.push(delta); forward(delta); }

const valid = !result.meta.incomplete && result.meta.errors.length === 0 &&
  result.meta.unresolved.length === 0 && result.meta.orphaned.length === 0 && result.root !== null;
```

For a full string, use `createParser(spec.schema, spec.root).parse(text)`. `parse`
and `push` never throw.

Client side, `<Renderer onError={(errors) => …}>` receives structured errors (`code`,
`source`, `statementId`, `message`, `hint`). It is called with `[]` once they are
resolved. Without `onError`, errors go to `console.warn`.

Common codes: `unknown-component`, `missing-required`, `null-required`,
`type-mismatch`, `excess-args` (extras dropped, still renders), `inline-reserved`
(Query/Mutation used inline), `unresolved`, `orphaned`, `no-root`,
`tool-not-found`, `tool-error`, `render-error`.

## 3. Repair with the user's own model

Send the errors back to **the same provider** as a follow-up turn and replace the
rendered message with the corrected program:

```ts
const report = errors
  .map((e) => `[${e.code}] ${e.statementId ? `"${e.statementId}": ` : ""}${e.message}${e.hint ? `\nHint: ${e.hint}` : ""}`)
  .join("\n");

const retry = [
  ...messages,
  { role: "assistant", content: generation },
  { role: "user", content: `Your OpenUI Lang had errors. Return the complete corrected program only.\n\n${report}` },
];
// call the provider again (non-streaming is fine), re-parse, and swap the message content if valid
```

Rules:

- Make **one** retry, maybe two, and then fall back: show the text, or a generic "couldn't render" state. Never loop.
- Hide the repair turn from the visible chat. Store only the final valid program as the assistant message.
- Log the error codes. They tell you which component descriptions to improve, which feeds back into layer 1.

## Hosted option (only if the user asks)

OpenUI also sells **Autofix** (`POST https://api.thesys.dev/v1/autofix`,
`createAutofix` in `@openuidev/server`): a paid, per-fix Thesys API that repairs a
finished generation while keeping your provider for inference. It needs
`THESYS_API_KEY` and sends the conversation to Thesys. Mention it only when the user
asks for a managed fix, and present it as an alternative to layer 3. For setup,
defer to the vendored `openui` skill (`references/autofix.md`).
