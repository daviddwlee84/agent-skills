# Catalog

A curated index of **external skills, MCP servers, and domain hubs** —
distinct from [Skills](../skills/index.md) (what we ship) and
[Reference](../reference/scripts.md) (how *our* tooling works).

The catalog exists because:

- Some skills are worth knowing about but not vendoring (license,
  scope, niche, plugin-only) — we still want them findable from the
  docs.
- MCP servers don't fit cleanly into the skill model — they need a
  separate record area.
- A domain practitioner (finance, ML, quant, …) wants one entry point
  that lists relevant local + vendored + external skills + MCPs +
  backlog items together.

## What's in here

| Subarea | Purpose | Start here |
|---|---|---|
| [Domains](domains/index.md) | One hub page per professional domain — pulls together skills + MCPs + backlog from the domain's perspective. | [Finance](domains/finance.md) is the most-populated example. |
| [External skills](skill-collections.md) | Single curated index of upstream skill collections + adjacent reading. Replaces the historical `Collections.md` + README "Resources" section. | The full table at the top of the page. |
| [Curiosity shelf](curiosities.md) | Docs-only collection of amusing, provocative, or highly personal skills that should not enter routine discovery or workflows. | Persona and meta-skill experiments. |
| [MCP wiki](mcp/index.md) | Personal-knowledge area for MCP servers — one page per MCP with frontmatter for future automation. | [Financial Datasets MCP](mcp/financialdatasets-ai.md) is the first populated entry. |

## How catalog status works

Every external entry carries a `status:` value (`vendored / deferred /
skipped / evaluated / wishlist`) that doubles as a vendoring decision
log. The full enum lives in
[`docs/_snippets/external-install.md`](https://github.com/daviddwlee84/agent-skills/blob/main/docs/_snippets/external-install.md)
and is included at the top of every catalog page that lists external
entries.

Workflow for status changes — see
[Adding catalog entries](../workflows/adding-catalog-entries.md).

## See also (Reference landscapes)

The [Reference](../reference/scripts.md) section already contains
landscape pages for tooling we *consume* but don't ship:

- [Browser automation skills & MCPs](../reference/browser-automation-skills.md)
  — Playwright vs agent-browser vs browser-use vs stagehand vs
  Playwright MCP comparison.
- [Deep Research landscape](../reference/deep-research-landscape.md) —
  survey of deep-research tools and personas.
- [SDD frameworks & agent harnesses](../reference/sdd-and-harnesses.md)
  — spec-kit / GSD / GSD-2 / OpenClaw / Pi SDK comparison. Cross-listed
  in the [Agent Harness](domains/agent-harness.md) hub.
- [Warp Oz skills](../reference/warp-oz-skills.md) — Warp Oz skills
  vendoring rationale.
- [Karpathy's LLM Wiki pattern](../reference/llm-wiki-pattern.md) — the
  pattern the [MCP wiki](mcp/index.md) is modeled after.

These pages stay in `Reference` (not `Catalog`) because they document
*conventions* we follow, not *external entries* we track. Catalog
cross-links them where relevant.
