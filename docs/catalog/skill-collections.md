# External skill collections

Curated index of upstream skill collections, marketplaces, and adjacent
projects we track. Most are *not* vendored into this repo — listing them
here gives the manual-install path and a recorded vendoring decision.

This page replaces the historical [`Collections.md`](https://github.com/daviddwlee84/agent-skills/blob/main/Collections.md)
at repo root (kept as a stub for backlink stability) and absorbs the
"Resources" section that used to live in [`README.md`](https://github.com/daviddwlee84/agent-skills/blob/main/README.md).

--8<-- "_snippets/external-install.md"

## Skills managers

The CLIs / runtimes that install and discover agent skills. The install
snippet at the top of this site uses the first one.

| Tool | Upstream | Status | Notes |
|---|---|---|---|
| `npx skills` | [`vercel-labs/skills`](https://github.com/vercel-labs/skills) | `vendored`-as-tool | The CLI this repo standardizes on. See [npx skills metadata model](../reference/npx-skills-metadata.md) for how `marketplace.json` drives the grouped picker. |
| The Agent Skills Directory | [`skills.sh`](https://skills.sh/) | `evaluated` | Hosted directory of `npx skills`-compatible skills. Useful for discovery. |
| Skill.Fish | [`knoxgraeme/skillfish`](https://github.com/knoxgraeme/skillfish) ([site](https://www.skill.fish/)) | `evaluated` | Alternative skill manager. Not used here; tracked for awareness. |

## General-purpose collections

Multi-skill repos covering broad engineering / authoring topics. Several
are partially vendored (specific skills cherry-picked into
[`vendor.yaml`](https://github.com/daviddwlee84/agent-skills/blob/main/vendor.yaml)).

| Collection | Upstream | Status | Notes |
|---|---|---|---|
| Anthropic's first-party skills | [`anthropics/skills`](https://github.com/anthropics/skills) | `vendored` (partial) | We vendor `skill-creator`, `frontend-design`, `webapp-testing`, `mcp-builder`. |
| Vercel Labs agent skills | [`vercel-labs/agent-skills`](https://github.com/vercel-labs/agent-skills) | `vendored` (partial) | We vendor `web-design-guidelines` into `fullstack-nextjs` series. |
| Vercel plugin skills | [`vercel/vercel-plugin`](https://github.com/vercel/vercel-plugin) | `vendored` (partial) | We vendor `nextjs`, `shadcn`, `react-best-practices`, `vercel-storage` into `fullstack-nextjs` series. |
| Supabase agent skills | [`supabase/agent-skills`](https://github.com/supabase/agent-skills) | `vendored` (partial) | We vendor `supabase` and `supabase-postgres-best-practices` into `fullstack-nextjs` series. |
| marimo team skills | [`marimo-team/skills`](https://github.com/marimo-team/skills) | `vendored` (partial) | We vendor `marimo-notebook`, `streamlit-to-marimo`, `anywidget`. |
| Streamlit agent skills | [`streamlit/agent-skills`](https://github.com/streamlit/agent-skills) | `wishlist` | Not yet evaluated; mirrors the marimo-team pattern. |
| Matt Pocock's skills | [`mattpocock/skills`](https://github.com/mattpocock/skills) | `vendored` (partial) | We vendor the 15-skill end-to-end flow (grill → spec → tickets → implement → review) into the `engineering-fundamentals` series — see [`reference/mattpocock-skills.md`](../reference/mattpocock-skills.md) for the flow, the full list, and what we skip. |
| GarryTan / OpenClaw skills | [`garrytan/gstack`](https://github.com/garrytan/gstack) | `vendored` (partial) | We vendor 4 skills into `product-planning` series. |
| Warp Oz skills | [`warpdotdev/oz-skills`](https://github.com/warpdotdev/oz-skills) | `vendored` (partial) | 6 of 15 vendored — see [`reference/warp-oz-skills.md`](../reference/warp-oz-skills.md) for what was skipped and why. |
| 199-biotechnologies deep-research | [`199-biotechnologies/deep-research`](https://github.com/199-biotechnologies/deep-research) | `vendored` | Single-skill series. See [`reference/deep-research-landscape.md`](../reference/deep-research-landscape.md). |
| The Minimalist Entrepreneur skills | [`slavingia/skills`](https://github.com/slavingia/skills) | `evaluated` | Skills based on Sahil Lavingia's [The Minimalist Entrepreneur](https://www.amazon.com/Minimalist-Entrepreneur-Great-Founders-More/dp/0593192397). Persona-style; useful as a model for opinionated single-author skill packs. |
| `last30days` topic synthesizer | [`mvanhorn/last30days-skill`](https://github.com/mvanhorn/last30days-skill) | `evaluated` | Researches a topic across Reddit, X, YouTube, HN, Polymarket, web → grounded summary. |

## Domain-specific collections

Domain-focused skill packs and plugin marketplaces — see the
corresponding [domain hub](domains/index.md) for cross-references.

| Collection | Upstream | Status | Domain | Notes |
|---|---|---|---|---|
| Claude for Financial Services | [`anthropics/financial-services`](https://github.com/anthropics/financial-services) | `wishlist` | [Finance](domains/finance.md) | Massive marketplace: 11 named agents, 7 vertical plugins, partner plugins (LSEG, S&P Global). 21.5k ⭐. |
| Awesome Finance Skills | [`RKiding/Awesome-finance-skills`](https://github.com/RKiding/Awesome-finance-skills) | `wishlist` | [Finance](domains/finance.md) | 8 plug-and-play finance skills (news, stock data, sentiment, forecasting, signal tracking, viz, reporting, web search). |
| AI Research Skills library | [`Orchestra-Research/AI-research-SKILLs`](https://github.com/Orchestra-Research/AI-research-SKILLs) | `wishlist` | [AI/ML Research](domains/ai-ml-research.md) | 98 skills across 23 categories — full research lifecycle. Has its own npm wrapper: `npx @orchestra-research/ai-research-skills`. |
| Knowledge Work Plugins | [`anthropics/knowledge-work-plugins`](https://github.com/anthropics/knowledge-work-plugins) | `wishlist` | [Knowledge Work](domains/knowledge-work.md) | 11 job-function plugins (sales, legal, finance, data, bio-research, etc.). 12.1k ⭐. |

## Articles & adjacent reading

| Title | Source | Notes |
|---|---|---|
| [Building Agent Skills with skill-creator](https://medium.com/google-cloud/building-agent-skills-with-skill-creator-855f18e785cf) | Google Cloud / Medium | Walkthrough of the [`skill-creator`](../skills/skill-creator.md) workflow (vendored). |
| [Introducing: React Best Practices](https://vercel.com/blog/introducing-react-best-practices) | Vercel blog | Pairs with the vendored [`react-best-practices`](../skills/react-best-practices.md) skill. |
| [Six skills for financial service professionals](https://claude.com/resources/tutorials/claude-for-financial-services-skills) | Claude resources | Cross-listed in [Finance](domains/finance.md). |

## Skill candidates (under evaluation)

Reference projects that *could* become a vendored skill or inform a local
one — not formally evaluated yet.

| Candidate | Upstream | Status | Notes |
|---|---|---|---|
| 12-factor agents | [`humanlayer/12-factor-agents`](https://github.com/humanlayer/12-factor-agents) | `wishlist` | Adjacent design philosophy; could inform a `12-factor-agent-review` skill. |
| The Twelve-Factor App | [12factor.net](https://12factor.net/) | `evaluated` | Original 12-factor manifesto. Inspiration source, not a skill. |
| `agent-skill-creator` | [`FrancyJGLisboa/agent-skill-creator`](https://github.com/FrancyJGLisboa/agent-skill-creator) | `wishlist` | Alternative authoring tool; compare with our [`skill-author`](../skills/skill-author.md) + vendored `skill-creator`. |
| `find-skills` | [`vercel-labs/skills/find-skills`](https://skills.sh/vercel-labs/skills/find-skills) | `evaluated` | Discovery skill from `vercel-labs/skills`. Useful pattern. |

## Vendoring policy

We vendor a skill when:

1. The upstream has stable canonical authority (Vercel for Next.js, Supabase for Supabase, etc.).
2. The skill fills a gap not already covered by another vendored or local skill.
3. The license is compatible with the [agentskills.io specification](https://agentskills.io/specification).

We **do not** vendor when:

- The upstream is itself a marketplace / collection (we cherry-pick instead).
- Plugin-format collections (e.g., `anthropics/knowledge-work-plugins`) require `claude plugin install` rather than `npx skills add` — we record them here for manual install.
- The skill duplicates an already-vendored one from a more authoritative source.
- The skill is too narrow for general use (host-specific, BigQuery-specific, etc.).

For the full workflow — including how to move an entry from `wishlist` →
`deferred` → `vendored` — see
[Adding catalog entries](../workflows/adding-catalog-entries.md).
