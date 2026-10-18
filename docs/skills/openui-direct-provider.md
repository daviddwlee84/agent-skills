# openui-direct-provider

Local, provider-neutral companion to the vendored [`openui`](openui.md) skill.
It teaches an agent to add [OpenUI](https://www.openui.com/) generative UI to an
app **while keeping inference on the user's own model provider**: OpenAI,
Anthropic, Google, or any OpenAI-compatible or local endpoint. No hosted service
sits in the request path.

## Why it exists

The official skill defaults to the paid OpenUI Gateway (see
[Gateway-first by default](openui.md#gateway-first-by-default)). The OpenUI
language, prompt generator, parser, and renderer are MIT-licensed packages that
work with any provider. This skill builds on those packages and the MIT
[`thesysdev/openui`](https://github.com/thesysdev/openui) docs, and adds a
**neutrality rule**: Gateway and Autofix come up only if the user asks, or needs
something only they provide. Even then, the agent labels them as paid hosted
services and names the self-hosted alternative.

The pairing works like [`skill-author`](skill-author.md) (local) and
[`skill-creator`](skill-creator.md) (vendored): each covers its own half and
defers to the other. Both skills trigger on "OpenUI", so install the one that
matches how you run inference:

| You want | Install |
|---|---|
| Your own provider, keys, and storage | `openui-direct-provider` |
| OpenUI Gateway / Cloud, managed history, Reliability Monitoring | `openui` |

## What it teaches

- The core flow:
  1. `defineComponent` / `createLibrary`
  2. `openui generate --spec`
  3. `generateSystemPrompt({ library, promptOptions })` **without** `cloud: true`
  4. the provider's own SDK
  5. `<Renderer>` with `onAction` / `onError`
- Backend recipes ([`references/backend-recipes.md`](https://github.com/daviddwlee84/agent-skills/blob/main/skills/local/openui-direct-provider/references/backend-recipes.md)): OpenAI SDK, Vercel AI SDK with any provider, OpenAI-compatible/local base URLs, plain-text streams, and LangGraph, each paired with its Agent Interface stream adapter.
- Self-hosted repair ([`references/self-repair.md`](https://github.com/daviddwlee84/agent-skills/blob/main/skills/local/openui-direct-provider/references/self-repair.md)):
  - prevent errors with library design;
  - detect them with the streaming parser or `Renderer onError`;
  - repair with one bounded retry on the user's own model.
- Gotchas:
  - agent runs of `openui create` scaffold the **Cloud** template (ask the user to pick *OpenUI Self-hosted* interactively);
  - the CLI sends telemetry (`--no-telemetry`);
  - npm lags behind `main`;
  - model-id formats differ from Gateway's;
  - UI-side `Query`/`Mutation` arguments are untrusted.

## Install

```bash
npx skills@latest add daviddwlee84/agent-skills/skills -s openui-direct-provider
```

## Canonical SKILL.md

See
[`skills/local/openui-direct-provider/SKILL.md`](https://github.com/daviddwlee84/agent-skills/blob/main/skills/local/openui-direct-provider/SKILL.md).
