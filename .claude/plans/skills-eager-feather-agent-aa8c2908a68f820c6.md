# Docs-structure refactor — domains, external catalog, MCP wiki

Status: planning (read-only mode)
Date: 2026-05-13
Related: Collections.md migration, README "Resources" expansion, TODO.md P? items (financial-data-sources, VectorBT, Tardis, MLflow, DVC, fine-tuning, Gradio), https://docs.financialdatasets.ai/mcp-server

## TL;DR — recommended choices

1. **Domains**: ship as a new top-level `Catalog` parent that contains a `domains/` index + per-domain hub pages (option A). Do **not** reorganize `docs/skills/` (option B). Optionally surface a "by-domain" axis inside `docs/skills/index.md` (a slim version of option C) once at least two domain hubs exist.
2. **External skills**: migrate `Collections.md` into `docs/catalog/skill-collections.md` as a single curated index page; only spin off per-collection subpages (like `warp-oz-skills.md` already does) when a collection earns a dedicated page (>3 vendored skills, or significant install/license nuance worth its own page).
3. **MCP wiki**: new `docs/catalog/mcp/` section with `index.md` + per-MCP pages. Use a YAML frontmatter schema so the index can be a generated table later. First entry: `financialdatasets-ai.md`.
4. **Manual install pattern**: a small reusable include (`docs/_snippets/external-install.md`) plus a per-entry frontmatter block. Always include both `npx skills add ...` and the upstream URL; only call out vendoring decisions when the answer is "no, intentionally" with a stated reason.
5. **Nav reshuffle**: introduce a single new top-level **Catalog** parent (Domains, External skills, MCP wiki), and leave Skills / Workflows / Reference / Conventions where they are. This adds **one** sidebar item, not three. `Reference` stays for *meta* docs (formats, recipes, compatibility); `Catalog` is for *external awareness*.
6. **First PR**: ship Collections migration + the new `Catalog` nav skeleton + one finance domain hub + the financialdatasets-ai MCP page. Skip the rest.
7. **Bilingual cost**: every new page needs a `.zh-TW.md` sibling. Three new pages in PR1 (`catalog/index`, `catalog/skill-collections`, `catalog/domains/finance`, `catalog/mcp/index`, `catalog/mcp/financialdatasets-ai`) = 5 EN + 5 zh-TW = **10 files**. Honest cost: ~1 working session per language for translation if doing it carefully; the `mkdocs-i18n` `fallback_to_default: true` means a missing zh-TW page falls back to English so we can land EN-only and translate in a follow-up commit if needed.

---

## Q1. Where do domain hubs live?

**Recommend (A) with a twist: nest under a new top-level `Catalog` parent.**

| Option | Verdict | Why |
|---|---|---|
| (A) New `docs/domains/` section | **Pick** (under `docs/catalog/domains/` to share a parent with external skills + MCP wiki) | Minimal disruption. Hubs read like the existing `reference/*-landscape.md` pages but indexed as their own thing. Lets us add a domain by writing one file. |
| (B) Reorganize `docs/skills/` by domain | Reject | Current flat list works because `vendor.yaml` `series:` already does the grouping; adding a `domain:` axis would require schema changes, marketplace.json reshuffle, and rewriting `skills/index.md` tables. Out of scope. |
| (C) "By-domain" view inside `docs/skills/index.md` | Defer (use only as a small section once 2+ domain hubs exist) | Useful as a discovery aid but redundant with the hub pages. Add a "By domain" subsection that just links to `catalog/domains/*` once those exist. |

Each domain hub is a single page that links to:
- Local skills relevant to the domain (existing pages under `docs/skills/`)
- Vendored skills relevant to the domain (existing pages under `docs/skills/`)
- External skills (entries in `docs/catalog/skill-collections.md`)
- MCPs (pages under `docs/catalog/mcp/`)
- Backlog entries (`backlog/*.md` and TODO `P?` items)

Hubs are **awareness pages**, not registries. They explicitly do not duplicate the skill pages — they link to them. This is the same pattern as `reference/deep-research-landscape.md` ("what this repo vendors" + "adjacent options not vendored").

---

## Q2. Where does the external skills catalog live?

**Recommend: single curated index at `docs/catalog/skill-collections.md`. Spin off per-collection subpages only when warranted.**

Justification:
- `Collections.md` at repo root has 2 entries; the README "Resources" section has the curated 8 we actually care about. Reconciling these into one page kills the duplication.
- The existing `reference/warp-oz-skills.md` is the proof-of-concept for "one collection deserves its own page" (vendoring 6 of 15 skills, AGPL/MIT licensing nuance). That kind of depth justifies a subpage; the 2-line entries in the README "Resources" do not.
- The `reference/` section is for *meta* documentation (formats, recipes, compatibility specs, our own conventions). External upstream catalogs are **not** repo conventions — they're the world outside this repo. Conceptually different. New `Catalog` parent makes that distinction cleaner.
- Keep `warp-oz-skills.md` and `browser-automation-skills.md` and `deep-research-landscape.md` and `sdd-and-harnesses.md` where they are (`reference/`). They're hybrid — partly landscape, partly "why we vendor / why we don't". Migrating them would churn permalinks for no reader benefit. **Add cross-links from the new index, don't move existing pages.**

`Collections.md` at repo root: keep as a thin redirect comment ("→ docs/catalog/skill-collections.md") or delete. Recommend keep + redirect note, since some external readers may have linked it.

---

## Q3. Where does the MCP wiki live?

**Recommend: `docs/catalog/mcp/` with `index.md` + per-MCP pages.**

Per-category pages (`finance.md`, `dev-tools.md`) would force premature taxonomy decisions when we have one entry. Per-MCP pages let the index be a flat table that we can re-group later (or generate the table from frontmatter via a small script — see Q5 below).

**Per-MCP page schema** (YAML frontmatter + body):

```yaml
---
name: Financial Datasets MCP
slug: financialdatasets-ai
upstream_url: https://docs.financialdatasets.ai/mcp-server
upstream_repo: https://github.com/financial-datasets/mcp-server  # optional
transport: [stdio, http, sse]   # which transports it offers
auth: [api_key, oauth]          # auth options
hosting: hosted                 # hosted | local | both
domain: [finance]               # cross-references docs/catalog/domains/*.md
status: documented              # documented | installed | considering
license: MIT                    # spdx
last_verified: "2026-05-13"
---
```

**Body sections** (per page):
1. `## TL;DR` — one paragraph: what tools it exposes, why it exists, who runs it.
2. `## Tools / capabilities` — bullet list of MCP tools (e.g., `get_prices`, `get_company_facts`).
3. `## Auth & install` — copy-paste `.mcp.json` or `claude mcp add` snippet; note OAuth vs API-key paths.
4. `## When to use it` — bullets of trigger scenarios.
5. `## When NOT to use it` — explicit skip cases (cost, coverage gaps, geographic limits).
6. `## Related skills in this repo` — links to skills/domain hubs that pair with this MCP.
7. `## Upstream sources` — links to docs, repo, blog posts.

Index page (`docs/catalog/mcp/index.md`):
- Markdown table generated by hand initially (5 columns: Name, Domain, Auth, Transport, Page).
- Once the count exceeds ~6 entries, replace the manual table with a small script (see Q5) that reads frontmatter and emits the table at build time, so the index never goes stale.
- Add a "Why we don't auto-install MCPs" note explaining the personal-wiki-not-installer framing. This matches the `reference/llm-wiki-pattern.md` framing ("documentation, not a skill").

---

## Q4. Manual-install instructions — recommended template

Two reusable include snippets, plus a per-entry block at the top of each external entry:

### Snippet A — `docs/_snippets/external-install.md`

```markdown
**Install** (manual, not vendored in this repo):

```bash
# Single skill
npx skills@latest add OWNER/REPO/path/to/skill

# Whole collection
npx skills@latest add OWNER/REPO
```

See [Adding vendor skills](../workflows/adding-vendor-skills.md) for how
this repo vendors skills upstream into `skills/vendor/<series>/<name>/`.
```

(The actual snippet would be a real includable, with placeholders the entry overrides.)

### Per-entry block in `docs/catalog/skill-collections.md`

For each collection, a fenced section like:

```markdown
### `RKiding/Awesome-finance-skills`

- **Upstream**: https://github.com/RKiding/Awesome-finance-skills
- **Vendored here?** No — curated awareness. (See [why](#vendoring-policy) below.)
- **Recommended skills to install**:
  - `npx skills add RKiding/Awesome-finance-skills/skills/<name>` — short blurb
- **Domain hub**: [Finance](domains/finance.md)
- **Last surveyed**: 2026-05-13
```

### Vendoring decision footer (page-level, one section, not per-entry)

A single `## Vendoring policy` section at the bottom of `skill-collections.md`:

> Why most entries on this page are *not* vendored:
>
> - We vendor a skill only when (a) it covers a gap our own skills don't, (b) we'll keep the upstream sync running, and (c) including it in `marketplace.json` improves the install UX. Otherwise, **document and let users install per-project**. This keeps `vendor.yaml` from sprawling and keeps the repo install lean.

This avoids per-entry "why not vendored" bloat. Skills that earn vendoring move from this page into `docs/skills/index.md` and `vendor.yaml`, *with* a note here saying "vendored — see skills page".

---

## Q5. Navigation impact — proposed mkdocs.yml nav

**Add one parent (`Catalog`), keep the rest of the nav stable.**

```yaml
nav:
  - Home: index.md
  - Getting Started: getting-started.md
  - Conventions: conventions.md
  - Workflows:
      - Adding vendor skills: workflows/adding-vendor-skills.md
      - Creating local skills: workflows/creating-local-skills.md
      - Project memory: workflows/project-memory.md
  - Skills:
      - Overview: skills/index.md
      - Local: ...                    # unchanged
      - Vendored: ...                 # unchanged
  - Catalog:
      - Overview: catalog/index.md
      - Domains:
          - Overview: catalog/domains/index.md
          - Finance: catalog/domains/finance.md
          # Future: catalog/domains/research.md, catalog/domains/web-dev.md, catalog/domains/ml-ops.md
      - External skills: catalog/skill-collections.md
      - MCP wiki:
          - Overview: catalog/mcp/index.md
          - Financial Datasets: catalog/mcp/financialdatasets-ai.md
          # Future per-MCP pages here
  - Reference:
      # unchanged — the existing 15 reference pages stay put.
      - TODO format: reference/todo-format.md
      - ...
  - Changelog: changelog.md
```

Rationale:
- One new top-level item, three nested groups under it. With `navigation.sections` + `navigation.expand` already enabled, the sidebar is one click deeper but not bloated.
- `catalog/index.md` is a 1-screen landing page that explains what the three sub-sections are for and links to each.
- `Reference` is preserved for *meta* docs (formats, recipes, compatibility, our own landscape pages). Catalog is for *external awareness*.
- Existing landscape pages (`browser-automation-skills.md`, `deep-research-landscape.md`, `sdd-and-harnesses.md`, `warp-oz-skills.md`, `llm-wiki-pattern.md`) **do not move**. The new `catalog/index.md` cross-links to them with a "see also: landscape pages in Reference" callout.
- Add to `mkdocs.yml` `plugins.llmstxt.sections`:
  ```yaml
  Catalog:
    - catalog/*.md
    - catalog/domains/*.md
    - catalog/mcp/*.md
  ```
  so LLM consumers get the new section in `llms.txt` / `llms-full.txt`.

---

## Q6. Migration scope — smallest first PR

**PR1 (this plan):**
1. Create `docs/catalog/index.md` + `.zh-TW.md`.
2. Create `docs/catalog/domains/index.md` + `.zh-TW.md`.
3. Create `docs/catalog/domains/finance.md` + `.zh-TW.md` (the only finance hub).
4. Create `docs/catalog/skill-collections.md` + `.zh-TW.md` (migrate Collections.md + README "Resources" content into it).
5. Create `docs/catalog/mcp/index.md` + `.zh-TW.md`.
6. Create `docs/catalog/mcp/financialdatasets-ai.md` + `.zh-TW.md` (the first MCP entry).
7. Create `docs/_snippets/external-install.md` (single file, no zh-TW needed since snippets render inside whatever page includes them).
8. Update `mkdocs.yml`:
    - Add `Catalog` to `nav`.
    - Add `Catalog` section to `plugins.llmstxt.sections`.
9. Update repo-root `Collections.md` to a short stub that links to `docs/catalog/skill-collections.md`.
10. Update `README.md` "Resources" section to: a one-paragraph pointer to `docs/catalog/skill-collections.md` + a 4-link "highlights" list. Don't fully delete — README readers benefit from a quick-glance list.
11. Update `docs/index.md` "Where to go next" table: add a row "Discover external skills, MCPs, and finance-domain hubs → [Catalog](catalog/index.md)".
12. Update `CLAUDE.md` to point agents at the new structure (one new bullet under "Project Overview" describing the `docs/catalog/` tree).

**File count for PR1:** 10 new docs (5 EN + 5 zh-TW) + 1 snippet + 5 edits (`mkdocs.yml`, `Collections.md`, `README.md`, `docs/index.md`, `CLAUDE.md`) = **16 files touched**. Pre-commit + `make docs-build --strict` should pass.

**PR2 (follow-up, deferred):**
- Add `domains/research.md` (AI/ML research) — links to vendored `deep-research`, the deep-research landscape, etc.
- Add 2–3 more MCP entries (e.g., `chrome-devtools.md` referenced in `warp-oz-skills.md`, `playwright.md`).
- Optional: a `scripts/build-mcp-index.sh` validator that reads frontmatter from `docs/catalog/mcp/*.md` and rebuilds the table in `docs/catalog/mcp/index.md` (see Q5 below).

**PR3 (further follow-up, deferred):**
- Add `domains/ml-ops.md` and `domains/web-dev.md`.
- Add a slim "By domain" subsection in `docs/skills/index.md` once at least 3 domain hubs exist.

---

## Q7. Bilingual cost — honest accounting

For PR1, **5 new EN pages × 1 zh-TW each = 10 doc files**. The actual translation cost depends on how mechanical the page is:

- `catalog/index.md` — short, mostly a router. 30 min translation.
- `catalog/domains/index.md` — short. 30 min.
- `catalog/domains/finance.md` — medium-long (links + tables). 60–90 min.
- `catalog/skill-collections.md` — long (8+ entries with prose). 90–120 min.
- `catalog/mcp/index.md` — short. 30 min.
- `catalog/mcp/financialdatasets-ai.md` — medium. 60 min.

Total zh-TW translation: ~5 hours for PR1.

**Mitigation** (from `mkdocs.yml` already): `fallback_to_default: true` means a missing zh-TW page silently falls back to English. We can land PR1 EN-only and add zh-TW in a follow-up commit before declaring "shipped". This matches the precedent of `mkdocs-2-and-zensical.md` where the zh-TW version is intentionally short (689 bytes vs 1.5k EN) — an acceptable degradation.

---

## File-level plan

### New files (PR1)

```
docs/_snippets/external-install.md
docs/catalog/index.md
docs/catalog/index.zh-TW.md
docs/catalog/domains/index.md
docs/catalog/domains/index.zh-TW.md
docs/catalog/domains/finance.md
docs/catalog/domains/finance.zh-TW.md
docs/catalog/skill-collections.md
docs/catalog/skill-collections.zh-TW.md
docs/catalog/mcp/index.md
docs/catalog/mcp/index.zh-TW.md
docs/catalog/mcp/financialdatasets-ai.md
docs/catalog/mcp/financialdatasets-ai.zh-TW.md
```

### Edited files (PR1)

```
mkdocs.yml                 # nav block + llmstxt sections
README.md                  # "Resources" → pointer + 4-link highlight
Collections.md             # repo root → stub + redirect note
docs/index.md              # "Where to go next" table → add Catalog row
CLAUDE.md                  # Project Overview → mention docs/catalog/
```

### Files NOT touched (anti-scope — DO NOT do these in PR1)

- `vendor.yaml` — unchanged. We are not vendoring new skills in this PR.
- `skills/.claude-plugin/marketplace.json` — unchanged. No new skills, no new plugins.
- `skills/local/`, `skills/vendor/` — unchanged. No skill body edits.
- Existing `docs/skills/*.md` pages — unchanged.
- Existing `docs/reference/*.md` pages — unchanged. The 5 landscape pages stay where they are; we cross-link.
- `TODO.md` — unchanged in this PR; in PR2 we promote-todo the relevant `P?` items as the new finance hub references them.
- `pitfalls/` — unchanged.
- `docs/getting-started.md`, `docs/conventions.md`, `docs/workflows/*.md` — unchanged.

---

## Skeleton headings for each new page

### `docs/catalog/index.md`

```markdown
# Catalog

External-awareness pages: domain hubs, third-party skill collections we
do *not* vendor, and a personal MCP wiki for servers we know about but
have not necessarily installed.

This is the world *outside* `skills/local/` and `skills/vendor/`. For
the skills this repo actually ships, see [Skills](../skills/index.md).

## What's in here

| Area | What it does |
|---|---|
| [Domains](domains/index.md) | Per-domain hub pages — finance, research, ML/ops, web — pointing at relevant local skills, vendored skills, external skills, and MCPs. |
| [External skills](skill-collections.md) | Curated index of upstream skill collections we recommend manually installing per-project. |
| [MCP wiki](mcp/index.md) | Personal reference of useful Model Context Protocol servers — what they expose, how to wire them up, when to use them. |

## See also (Reference)

The Reference section already hosts several landscape-style awareness pages:

- [Deep Research landscape](../reference/deep-research-landscape.md)
- [Browser automation skills & MCPs](../reference/browser-automation-skills.md)
- [SDD frameworks & agent harnesses](../reference/sdd-and-harnesses.md)
- [Warp Oz skills](../reference/warp-oz-skills.md)
- [Karpathy's LLM Wiki pattern](../reference/llm-wiki-pattern.md)

These are not duplicated under Catalog. Reference is for awareness pages
about *patterns*; Catalog is for awareness pages about *what to install*.
```

### `docs/catalog/domains/index.md`

```markdown
# Domain hubs

Each hub is one page summarizing what's relevant to a problem space,
across:

- **Local skills** in this repo
- **Vendored skills** in this repo
- **External skills** (per-project install, see [skill-collections](../skill-collections.md))
- **MCPs** (see [MCP wiki](../mcp/index.md))
- **Backlog** entries (`TODO.md` P?, `backlog/*.md`)

| Domain | Status |
|---|---|
| [Finance](finance.md) | Active — first hub |
| Research (AI/ML) | Planned |
| ML/Ops (MLflow, DVC, marimo, pueue) | Planned |
| Web dev (Next.js, Supabase, browser automation) | Planned |

## How to add a new domain

1. Copy `finance.md` as a template.
2. Fill in the four sections (Local, Vendored, External, MCPs, Backlog).
3. Add a row to the table above.
4. Add the page to `nav.Catalog.Domains` in `mkdocs.yml`.
5. Translate `<domain>.md` → `<domain>.zh-TW.md` (or accept English fallback).
```

### `docs/catalog/domains/finance.md`

```markdown
# Finance

Skills, MCPs, and external collections relevant to quantitative finance,
trading research, and financial-data workflows.

## Local skills

- [`quantatitive-factor-researcher`](../../skills/quantatitive-factor-researcher.md)
  — Python quant-research persona. The current entry point for any
  factor research conversation in this repo.

## Vendored skills

(none yet — see [TODO P? items](#backlog) below)

## External skills (manual install)

From [skill-collections](../skill-collections.md):

- [`RKiding/Awesome-finance-skills`](https://github.com/RKiding/Awesome-finance-skills)
  — community-curated finance skills index.
- [`anthropics/financial-services`](https://github.com/anthropics/financial-services)
  — 11 named agents + 7 verticals + partner plugins for financial services.
- [`anthropics/knowledge-work-plugins`](https://github.com/anthropics/knowledge-work-plugins/tree/main)
  — finance plugin among 11 job-function plugins.

## MCPs

- [Financial Datasets MCP](../mcp/financialdatasets-ai.md) — market data
  (prices, fundamentals, filings) via API key or OAuth. Used by
  `anthropics/financial-services`.

## Backlog (TODO P?)

From [TODO.md](https://github.com/daviddwlee84/agent-skills/blob/main/TODO.md):

- VectorBT skill
- VectorBT Pro skill
- Nautilus Trader skill
- Tardis SDK skill
- [Financial data sources skill set](https://github.com/daviddwlee84/agent-skills/blob/main/backlog/financial-data-sources.md) — research-backed P? item

## See also

- [Deep Research landscape](../../reference/deep-research-landscape.md) —
  finance research often pairs with deep-research workflows.
- [`MLflow tracking`](../../skills/mlflow-tracking.md), [`DVC`](../../skills/dvc-ml-workflow.md)
  — same experiment-tracking stack many quant researchers use.
```

### `docs/catalog/skill-collections.md`

```markdown
# External skill collections

Upstream collections we recommend installing per-project but **do not vendor**
into this repo's `skills/vendor/` tree. See the
[vendoring policy](#vendoring-policy) below for the criterion.

For collections we *do* vendor selectively (e.g., `vercel-labs`, `anthropics`,
`marimo-team`, `mattpocock`, `gstack`, Warp Oz, `199-biotechnologies`), see the
[Skills overview](../skills/index.md).

## Skills managers

- **[`vercel-labs/skills`](https://github.com/vercel-labs/skills)** — `npx skills` itself, plus [The Agent Skills Directory](https://skills.sh/).
- **[`Skill.Fish`](https://www.skill.fish/)** ([`knoxgraeme/skillfish`](https://github.com/knoxgraeme/skillfish)) — alternative skill manager.

## General-purpose collections

(One block per collection — `vercel-labs/agent-skills`, `mattpocock/skills`,
`anthropics/skills`, `anthropics/knowledge-work-plugins`, `marimo-team/skills`,
`streamlit/agent-skills`. Each block uses the per-entry block template from
the plan's Q4.)

## Domain-specific collections

- `RKiding/Awesome-finance-skills` → see [Finance hub](domains/finance.md)
- `Orchestra-Research/AI-research-SKILLs` (98 skills × 23 categories) → see Research hub (planned)

## Articles & adjacent reading

- [Building Agent Skills with skill-creator](https://medium.com/google-cloud/building-agent-skills-with-skill-creator-855f18e785cf)
- [Introducing: React Best Practices (Vercel)](https://vercel.com/blog/introducing-react-best-practices)
- [Six skills for financial service professionals (Claude)](https://claude.com/resources/tutorials/claude-for-financial-services-skills)

## Skill candidates (under evaluation)

- [`humanlayer/12-factor-agents`](https://github.com/humanlayer/12-factor-agents) + [`The Twelve-Factor App`](https://12factor.net/)
- [`FrancyJGLisboa/agent-skill-creator`](https://github.com/FrancyJGLisboa/agent-skill-creator)
- [`find-skills`](https://skills.sh/vercel-labs/skills/find-skills)

## Vendoring policy

Why most entries above are *not* vendored:

We vendor a skill into `skills/vendor/<series>/<name>/` only when:

1. It covers a gap our own skills don't already address.
2. We're committed to running `make sync` on it as upstream evolves.
3. Including it in `skills/.claude-plugin/marketplace.json` improves the
   `npx skills add daviddwlee84/agent-skills/skills` install UX.

Otherwise, **document here and let users install per-project**. This
keeps `vendor.yaml` from sprawling and keeps the repo install lean. If a
collection earns its own page (significant licensing nuance, multi-skill
selection rationale, install caveats), it gets one — see
[`Warp Oz skills`](../reference/warp-oz-skills.md) and [`Browser automation
skills`](../reference/browser-automation-skills.md) for examples.
```

### `docs/catalog/mcp/index.md`

```markdown
# MCP wiki

Personal reference of [Model Context Protocol](https://modelcontextprotocol.io)
servers. **Documentation, not an installer** — entries here are recorded
because they're useful to know about, not because we ship them.

For our own MCP-authoring workflow, see the vendored
[`mcp-builder`](../../skills/skill-creator.md#related-skills) skill (from
`anthropics/skills`).

## Entries

| Server | Domain | Auth | Transport | Page |
|---|---|---|---|---|
| Financial Datasets | Finance | API key, OAuth | stdio, http, sse | [page](financialdatasets-ai.md) |

## Why a wiki, not a registry?

Karpathy's [LLM Wiki pattern](../../reference/llm-wiki-pattern.md) — a
synthesized, curated knowledge base maintained by an LLM. MCP entries
here are knowledge memory: enough metadata to install if/when needed,
plus the trade-offs and "when *not* to use" notes that an MCP registry
won't tell you. They get updated when we re-evaluate, not on a schedule.

## Per-entry conventions

Every entry uses YAML frontmatter:

```yaml
---
name: <Display name>
slug: <kebab-case>
upstream_url: <docs URL>
upstream_repo: <github URL>  # optional
transport: [stdio, http, sse]
auth: [api_key, oauth, none]
hosting: hosted | local | both
domain: [<domain slug>]
status: documented | installed | considering
license: <SPDX>
last_verified: "<YYYY-MM-DD>"
---
```

See the [author template](#author-template) below for the body skeleton.
```

### `docs/catalog/mcp/financialdatasets-ai.md`

```markdown
---
name: Financial Datasets MCP
slug: financialdatasets-ai
upstream_url: https://docs.financialdatasets.ai/mcp-server
upstream_repo: https://github.com/financial-datasets/mcp-server
transport: [stdio, http, sse]
auth: [api_key, oauth]
hosting: hosted
domain: [finance]
status: documented
license: MIT
last_verified: "2026-05-13"
---

# Financial Datasets MCP

A Model Context Protocol server providing financial market data —
prices, fundamentals, SEC filings — via API key or OAuth. Used by
[`anthropics/financial-services`](https://github.com/anthropics/financial-services).

## TL;DR

Call market data, financial statements, and SEC filings as MCP tools.
Hosted by financialdatasets.ai. Free tier covers basic equities; paid
tiers add coverage and rate.

## Tools / capabilities

(Confirm against upstream docs at next sync.)

- `get_prices(ticker, start, end, interval)` — historical OHLCV
- `get_company_facts(ticker)` — fundamentals, statements
- `get_filings(ticker, form_type, start, end)` — SEC filings
- ... (TODO: enumerate from upstream when verifying)

## Auth & install

Two auth paths:

- **API key** — set `FINANCIAL_DATASETS_API_KEY`, configure stdio transport.
- **OAuth** — for hosted Claude / multi-user use cases.

`.mcp.json` snippet (stdio + API key):

```json
{
  "mcpServers": {
    "financialdatasets": {
      "command": "npx",
      "args": ["-y", "@financialdatasets/mcp-server"],
      "env": { "FINANCIAL_DATASETS_API_KEY": "${FINANCIAL_DATASETS_API_KEY}" }
    }
  }
}
```

(Verify command name against upstream docs before relying on it.)

## When to use it

- You need US equities OHLCV / fundamentals inside a Claude Code session
  without writing your own data-loader.
- You're using `anthropics/financial-services` skills and want their data
  layer to "just work".
- You want OAuth-gated data access for a hosted agent (multi-user).

## When NOT to use it

- Non-US markets — coverage is US-equities-first; check upstream for
  international coverage before assuming.
- Crypto / forex / futures — out of scope.
- Tick / order-book data — Tardis SDK or a dedicated provider (see
  [Finance hub](../domains/finance.md) backlog).
- Anything where you want raw control over the rate/cost surface
  (running `yfinance` locally is free and immediate).

## Related skills in this repo

- [`quantatitive-factor-researcher`](../../skills/quantatitive-factor-researcher.md)
  — pairs with this MCP as the "data layer" of a factor pipeline.
- See [Finance hub](../domains/finance.md) for the rest.

## Upstream sources

- Docs: https://docs.financialdatasets.ai/mcp-server
- Used by: https://github.com/anthropics/financial-services
```

---

## Optional new scripts / Make targets

Recommend NOT shipping in PR1, but planned for PR2:

### `scripts/build-mcp-index.sh` (PR2 candidate)

Reads YAML frontmatter from `docs/catalog/mcp/*.md` (excluding `index.md`),
emits a markdown table, and patches `docs/catalog/mcp/index.md` between
`<!-- BEGIN_MCP_TABLE -->` / `<!-- END_MCP_TABLE -->` markers.

Why deferred: with one entry, the manual table is fine. Build the script
when we have 5+ entries.

### `scripts/validate-catalog-frontmatter.sh` (PR2 candidate)

Checks every `docs/catalog/mcp/*.md` has the required frontmatter keys
(name, slug, upstream_url, transport, auth, status, last_verified) and
that `domain:` values reference existing `docs/catalog/domains/*.md`
files.

Wired into `make catalog` and into pre-commit (alongside `make marketplace`,
`make kanban`).

### Make target additions (PR1, optional)

Could add a thin `make catalog` that runs `make docs-build` with a grep
for catalog-specific link errors. Defer to PR2 once we have a
linter that does something more than `mkdocs build --strict`.

---

## Order of operations (PR1)

1. **Write EN content first** — all 7 EN pages (5 catalog + 2 indexes for
   domains/mcp). Run `make docs-serve` and walk the new tree by hand.
2. **Run `make docs-build`** — strict mode validates internal links.
   Fix broken links (the existing `not_found: info` only covers
   build-time links, not source-file ones).
3. **Edit `mkdocs.yml`** nav + llmstxt sections. Re-run `make docs-build`.
4. **Edit `Collections.md`, `README.md`, `docs/index.md`, `CLAUDE.md`** —
   the "discoverability surface" updates so readers find the new pages.
5. **Translate to zh-TW** — 6 zh-TW pages. Verify each renders by
   switching language in the served site.
6. **Run pre-existing repo gates**: `make marketplace`, `make kanban`,
   `make docs-build` one more time. None should fail since we haven't
   touched skills or marketplace.json.
7. **promote-todo** any TODO P? items the finance hub now references
   *if* they've been fully addressed by the hub. (None should be — the
   hub is awareness, not implementation.)
8. **Commit** as a single squash-merged PR with a 1–2 sentence message
   focused on "why" (consolidate Collections + introduce domain/MCP
   awareness layer).

---

## What to NOT do (anti-scope)

- **Do not move existing `docs/reference/*.md` pages.** The 5 landscape
  pages there cross-link from Catalog but stay put. Moving would churn
  permalinks for no reader benefit.
- **Do not vendor new skills.** PR1 is pure docs.
- **Do not edit `vendor.yaml` or `marketplace.json`.** Same reason.
- **Do not pre-create empty hub pages** for research / ml-ops / web-dev.
  Empty hubs degrade trust. Add them when there's content to fill them.
- **Do not pre-create per-category MCP pages** (`mcp/finance.md`,
  `mcp/dev-tools.md`). Per-MCP pages are sufficient until the count
  forces a re-grouping; premature category pages lock us into the wrong
  taxonomy.
- **Do not delete `Collections.md` outright.** Stub + redirect protects
  any external readers who linked it.
- **Do not bake "external install" guidance into per-skill detail pages**
  (`docs/skills/*.md`). External install is a *catalog* concern; per-skill
  pages stay focused on the skill's content. The exception is when a
  skill page genuinely needs an alternate-install note (none currently do).
- **Do not write a generic `docs/catalog/personal-knowledge.md` page.**
  The MCP wiki *is* the personal-knowledge area; don't dilute it with a
  meta-page.

---

## Critical files for implementation

- /Volumes/Data/Program/Personal/agent-skills/mkdocs.yml
- /Volumes/Data/Program/Personal/agent-skills/Collections.md
- /Volumes/Data/Program/Personal/agent-skills/README.md
- /Volumes/Data/Program/Personal/agent-skills/docs/index.md
- /Volumes/Data/Program/Personal/agent-skills/docs/skills/index.md
