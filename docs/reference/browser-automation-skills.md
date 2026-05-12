# Browser automation skills & MCPs

This page compares the popular **browser automation tools shipped as
agent skills or MCP servers**. Browser automation is one of the highest-
value capabilities you can give a coding agent — but the design choices
across these tools differ substantially. This page records the trade-offs
so the choice is explicit, and explains why this repo currently does
*not* vendor any of them.

## At a glance

Five well-known options, all roughly the same goal — let an agent open a
real browser and interact with pages — but very different shapes:

| Tool | ⭐ | Form | Auth/session | Cost model | Token-efficient surface |
|---|---:|---|---|---|---|
| [`microsoft/playwright-cli`](https://github.com/microsoft/playwright-cli) | 10k | CLI + 1 SKILL.md | Local Chromium / your profile | Free, local | a11y-tree snapshot + `eN` refs |
| [`vercel-labs/agent-browser`](https://github.com/vercel-labs/agent-browser) | 33k | CLI + 1 SKILL.md | Local Chromium, profile, Vercel Sandbox, AWS Bedrock AgentCore cloud | Free CLI; Vercel/AWS pay-as-you-go for cloud | a11y-tree snapshot + compact `@eN` refs |
| [`browser-use/browser-use`](https://github.com/browser-use/browser-use) | 93k | CLI + 4 SKILL.md (`browser-use`, `cloud`, `open-source`, `remote-browser`) | Local + Browser Use Cloud | Open-source local; Cloud SaaS | Persistent daemon (~50 ms/call); MCP also available |
| [`browserbase/stagehand`](https://github.com/browserbase/stagehand) | 23k | TypeScript SDK | Browserbase cloud (or local Playwright) | Browserbase metered | Code-first (`page.act("click sign in")`); not a SKILL.md |
| [Playwright MCP](https://playwright.dev/agent-cli/introduction) | (part of Playwright) | MCP server | Local Chromium | Free, local | a11y tree, but full MCP schema overhead |

> Star counts are repo totals (the project, not just the skill). Don't
> use them to compare per-skill quality — `browser-use/browser-use` is a
> framework with very high stars; the SKILL.md inside it is one
> deliverable among many.

## The design axes that actually matter

Pick on these, not on stars:

### 1. CLI vs MCP vs SDK

- **CLI + SKILL.md** — `playwright-cli`, `agent-browser`, `browser-use`
  (CLI mode). The agent shells out to `playwright-cli click e15`. Each
  command is one short tool call; no MCP schema to load. **Best for
  token efficiency** when the agent has Bash access. The Microsoft
  README and the agent-browser README both argue this beats the MCP
  approach for high-throughput agent loops.
- **MCP server** — Playwright MCP, `browser-use` MCP. The agent calls
  `mcp_call("playwright.click", {...})`. Loads the full schema once;
  cleaner for agents without Bash but pays the MCP overhead. Token cost
  per call is higher than CLI for the same operation.
- **SDK** — Stagehand. You write TypeScript that calls `page.act("…")`.
  Powerful for *application code* you ship; not a skill the agent
  invokes ad-hoc.

### 2. Snapshot strategy — a11y tree vs DOM vs vision

- **Accessibility-tree snapshot + element refs** (`playwright-cli`,
  `agent-browser`, Playwright MCP). The agent sees a structured tree
  with stable `eN` / `@eN` refs and uses them directly. Token-cheap,
  reliable, no fragile selectors.
- **DOM + selectors** (older Playwright / Selenium patterns). Larger
  context, brittle.
- **Vision-first** (`magnitudedev/browser-agent`, 4k⭐). Agent reasons
  over screenshots. Robust against DOM changes; high token + latency
  cost; useful when the page is an opaque webapp.

### 3. Where the browser actually runs

- **Local Chromium** (default for all CLIs above) — fast, free, uses
  your machine.
- **Local Chrome with your real profile** (`agent-browser`,
  `browser-use`) — sees your real cookies and logged-in state. Powerful;
  also a security surface.
- **Cloud browser** — Vercel Sandbox / AWS Bedrock AgentCore
  (`agent-browser`); Browser Use Cloud (`browser-use`); Browserbase
  (`stagehand`). Pay-per-session; required for headless servers, scale,
  or compliance.

### 4. Persistent session vs cold-start per call

- **Persistent daemon** (`browser-use` CLI) — keeps Chromium alive
  between commands; ~50 ms per call. Best for long agent loops on the
  same site.
- **Per-call session** (`playwright-cli` defaults, Playwright MCP) —
  starts/stops cleanly; safer for one-shot tasks. Higher per-call latency.

## Recommendation matrix

| Need | Pick |
|---|---|
| Token-efficient browser CLI for any agent with Bash | `agent-browser` or `playwright-cli` |
| Already on Playwright in CI | `playwright-cli` (same engine, same selectors) |
| Long-running session, lowest per-call latency | `browser-use` CLI |
| Production agents, cloud parallel browsers | `agent-browser` (Vercel/AWS) or `stagehand` (Browserbase) |
| Pages that defeat DOM scraping (heavy canvases, anti-bot) | Vision-first (`magnitudedev/browser-agent`) |
| Want code-level control inside a TypeScript app | `stagehand` SDK |
| Agent doesn't have Bash, only MCP | Playwright MCP or `browser-use` MCP |

## What this repo vendors

**None of these.** Recorded so future agents don't relitigate it:

- **Heavy install surface** — Chromium download, persistent profiles,
  daemon processes, optional cloud accounts. Vendoring as a SKILL.md
  doesn't actually install the underlying CLI; users still need
  `npm i -g agent-browser`, `pip install browser-use`, etc.
- **Per-project rather than user-global** — browser automation skills
  often touch real auth/cookies and per-site quirks. Better installed
  per project where the operator can review the SKILL.md, hooks, and
  any MCP config first.
- **Security audit signal** — Skills.sh shows a failed Gen Agent Trust
  Hub audit on `browser-use/browser-use` at the time of writing. Good
  enough reason to defer until the situation clarifies.
- **Anthropic `webapp-testing` already covers the common case** — for
  agent-driven QA of a web app this repo already vendors
  [`anthropics/skills/webapp-testing`](../skills/webapp-testing.md)
  under the [`fullstack-nextjs`](../skills/index.md) series, which uses
  Playwright under the hood without committing to a specific browser
  CLI.

If you decide you need one, install per project:

```bash
# Token-efficient CLI route (recommended for OpenCode / Claude Code / Codex)
npx skills add vercel-labs/agent-browser

# Long-running daemon route
npx skills add browser-use/browser-use

# Same engine as your CI Playwright tests
npx skills add microsoft/playwright-cli
```

These compose with this repo's research and SDD skills — a deep-research
session that needs a real browser can pair `vendor/deep-research` with
any of the above without conflict.

## See also

- [Deep Research landscape](deep-research-landscape.md) — browser
  automation is layer 4 in the deep-research stack
- [SDD frameworks & agent harnesses](sdd-and-harnesses.md) — same
  CLI vs MCP vs framework distinction applied to spec-driven dev
- [`anthropics/webapp-testing`](../skills/webapp-testing.md) — the
  Playwright-based testing skill already vendored in this repo
- [Agent skill compatibility](agent-skill-compatibility.md) — portable
  `SKILL.md` constraints all the CLIs above respect
