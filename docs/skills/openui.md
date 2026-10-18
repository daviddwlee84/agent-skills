# openui (vendored)

Vendored from
[`thesysdev/skills/skills/openui`](https://github.com/thesysdev/skills/tree/main/skills/openui),
the official coding-agent skill for [OpenUI](https://www.openui.com/). The
[`thesysdev/openui`](https://github.com/thesysdev/openui) repo itself ships no
`SKILL.md`; its `docs/public/AGENTS.md` and the `@openuidev/cli` scaffold point
agents at this skill. It is synchronized through `vendor.yaml`. Do not edit the
vendored files locally because `make sync` replaces them.

## What it teaches

OpenUI turns model output into live UI. The model writes **OpenUI Lang**, a
compact line-oriented language, using the components of a **component
library**. The server builds the system prompt from the library spec, and a
streaming **renderer** in the browser draws the program with the same library.

`SKILL.md` is a router. It tells the agent to read `package.json`, the lockfile,
and the installed `@openuidev/*` code first, and then to pick one reference per
job:

| Job | Reference |
|---|---|
| New app or agent / add to an existing app | `new-app.md`, `existing-app.md` |
| Backend on OpenUI Gateway (Chat Completions / Responses API) | `gateway.md`, `gateway-responses.md` |
| Call your own provider directly | `direct-provider.md`, `autofix.md` |
| Component libraries, Agent Interface, artifacts, theming | `component-library.md`, `agent-interface.md`, `artifacts.md`, `theming.md` |
| Broken renders, monitoring, deploy, the language itself | `reliability.md`, `deploy.md`, `openui-lang.md` |

It also includes a package map for `@openuidev/*` (lang-core, react-lang,
react-ui, react-headless, server, the Vue/Svelte/Angular renderers, cli, …).
Its rules cover API keys (never handle them), keeping an existing app's stack,
and porting to Python from the JS packages.

## Gateway-first by default

!!! warning "This skill recommends a paid service"
    The upstream rule "Use OpenUI Gateway for inference" makes the agent route
    model calls through **OpenUI Gateway** (part of OpenUI Cloud) and list its
    benefits the first time it comes up. That happens even when you name
    OpenAI, Anthropic, or Google: the agent suggests using them through Gateway
    with BYOK. The provider-direct path (`references/direct-provider.md`) is
    used only when you ask for it explicitly. To get it, tell the agent
    something like *"call my provider directly, no Gateway"*.

Because vendored content is kept unedited, the rule stays as it is upstream.

## Install

```bash
npx skills@latest add daviddwlee84/agent-skills/skills -s openui
# or straight from upstream
npx skills@latest add thesysdev/skills
```

## Canonical SKILL.md

See
[`skills/vendor/openui/SKILL.md`](https://github.com/daviddwlee84/agent-skills/blob/main/skills/vendor/openui/SKILL.md)
for the full instructions.
