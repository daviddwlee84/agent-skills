# Docs refactor: add `Catalog` (Domains + External skills + MCP wiki)

## Context

The repo's docs currently organize content along two axes:

- **"Skills we ship"** — `docs/skills/*.md` (10 local + 13 vendored, with the `fullstack-nextjs` series nested in nav).
- **"Concepts/landscapes we know about"** — `docs/reference/*.md` (15 pages: format specs, recipes, awareness landscapes for browser automation / SDD / Warp Oz / deep research / LLM Wiki).

As the skill count grows and the user wants to expand into **professional domains** (finance first, then AI/ML research, quant, knowledge work, etc.), neither axis fits well:

1. **No domain-driven entry point.** A finance practitioner has no single page that says: "here's the local skill (`quantatitive-factor-researcher`), the relevant Anthropic plugin (`anthropics/financial-services`), the MCP server (`financialdatasets.ai`), and the backlog items in this domain (TODO P? `financial-data-sources`, `VectorBT`, `Nautilus Trader`, `Tardis SDK`)."
2. **`Collections.md` (repo root) is abandoned** — 2 entries, never grew, while the README "Resources" section quietly became the real curated list (`anthropics/skills`, `knowledge-work-plugins`, `marimo-team/skills`, `RKiding/Awesome-finance-skills`, `Orchestra-Research/AI-research-SKILLs`, etc.).
3. **MCP servers have no record area.** The user wants a personal-wiki-style record of useful MCPs (concrete first entry: `https://docs.financialdatasets.ai/mcp-server`).
4. **No vendoring decision log.** Every external skill the user evaluates today lives in their head; there's no place to record "looked at it, skipped because X" or "wishlist, will revisit when Y."

This refactor adds a single new top-level docs section — **`Catalog`** — that absorbs all four needs into one structure, without disrupting the current `Skills` or `Reference` sections.

## Approach

1. Add `docs/catalog/` with three subareas: `domains/`, `mcp/`, and a flat `skill-collections.md`.
2. Define a **hub template** (`docs/catalog/domains/_template.md`) so empty/sparse domains can be stubbed honestly without writing fake content. Future domains copy the template.
3. Define a **status enum** for every external entry (`vendored / deferred / skipped / evaluated / wishlist`), centralized in a reusable snippet (`docs/_snippets/external-install.md`). The catalog becomes a vendoring decision log; each status change cross-links to `vendor.yaml` / `TODO.md` (existing sources of truth, not duplicated).
4. Migrate `Collections.md` (root) → `docs/catalog/skill-collections.md` (greatly expanded). Leave a 5-line stub at the old path pointing to the new location.
5. Add `Catalog` as a new top-level nav parent between `Skills` and `Reference`. Update `mkdocs.yml` nav + `llmstxt.sections` + `not_in_nav`.
6. Pair every new EN page with a `*.zh-TW.md` counterpart in the same PR (follows existing bilingual invariant).
7. Update `README.md` Resources section to a short highlight + pointer to the catalog.
8. Update `docs/index.md` "Where to go next" table to surface the catalog.
9. Update `CLAUDE.md` with one new "Catalog Workflow" subsection.
10. Add `docs/workflows/adding-catalog-entries.md` (the new workflow doc, paired with zh-TW).

## File-level plan (single PR)

### New files

```
docs/_snippets/
└── external-install.md            # reusable include: status enum + manual-install patterns
                                   # (snippets are includes, not pages — no zh-TW counterpart)

docs/catalog/
├── index.md                       # router page: what's in here + cross-links
├── domains/
│   ├── index.md                   # domain registry table + "how to add a domain"
│   ├── _template.md               # hub template (NOT in nav, no zh-TW)
│   ├── finance.md                 # POPULATED: anthropics/financial-services, financialdatasets MCP, RKiding/Awesome-finance-skills
│   ├── quant-research.md          # POPULATED: quantatitive-factor-researcher local + 4 P? (VectorBT, VectorBT Pro, Nautilus, Tardis)
│   ├── ai-ml-research.md          # POPULATED: mlflow-tracking + dvc-ml-workflow + marimo-batch-mlflow + Orchestra-Research/AI-research-SKILLs + LangChain/fine-tuning P?
│   ├── web-fullstack.md           # POPULATED: fullstack-nextjs series + browser automation cross-link
│   ├── knowledge-work.md          # MOSTLY TEMPLATE: anthropics/knowledge-work-plugins (status: wishlist)
│   └── agent-harness.md           # TEMPLATE: cross-links docs/reference/sdd-and-harnesses.md ("we don't ship these, we consume them")
├── skill-collections.md           # expanded migration of Collections.md + README Resources
└── mcp/
    ├── index.md                   # MCP wiki overview + entries table + "Per-entry frontmatter schema"
    └── financialdatasets-ai.md    # first populated MCP entry (status: wishlist)

docs/workflows/
└── adding-catalog-entries.md      # how to add an external skill / MCP / domain hub
```

**Bilingual pairing**: every file above except `_snippets/external-install.md` and `_template.md` gets a `*.zh-TW.md` counterpart.

**Page count**: 12 EN pages + 12 zh-TW + 1 template + 1 snippet = **26 new doc files**.

### Edited files

| File | Edit |
|---|---|
| `mkdocs.yml` | Add `Catalog` nav block + Workflows entry for `adding-catalog-entries.md`; extend `llmstxt.sections` with `Catalog`; append `_template.md` to `not_in_nav` |
| `Collections.md` (repo root) | Convert to a 5-line stub: title + 1-line description + link to `docs/catalog/skill-collections.md` + "this file is kept for backlinks" note |
| `README.md` | Replace verbose "Resources" section with a 3-link highlight + pointer to `https://daviddwlee84.github.io/agent-skills/catalog/` |
| `CLAUDE.md` | Add "Catalog Workflow" subsection under "Project Memory Workflow" — describes the tree, status enum, and links to `adding-catalog-entries.md` |
| `docs/index.md` | Add a "Browse external skills, MCPs, domain hubs" row to the "Where to go next" table |
| `docs/index.zh-TW.md` | Same delta as EN |

## Status enum (reused everywhere)

Defined once in `docs/_snippets/external-install.md`, included by every catalog page that lists external entries:

| Status | Meaning | Where it links |
|---|---|---|
| `vendored` | In `vendor.yaml`. | Link to the relevant `vendor.yaml` entry by anchor (or `skills/vendor/<name>/`). |
| `deferred` | Open TODO P? item — under consideration. | Link to the TODO.md anchor. |
| `skipped` | Looked at, chose not to vendor. | Inline reason required (1 sentence). |
| `evaluated` | Read but no decision made. Effectively "tracked." | Inline 1-line note describing what was learned. |
| `wishlist` | Surfaced but not yet evaluated. | No link required; this is the default for fresh discoveries. |

Status changes are explicit human edits (no automation in PR1). The workflow doc spells out the recipe:

- `wishlist` → `deferred`: run `./scripts/add-todo.sh --priority P? --effort <X>` then update the catalog entry with the TODO link.
- `deferred` → `vendored`: run `./scripts/add-vendor.sh`, then update catalog entry status + link to `vendor.yaml`. Optionally `./scripts/promote-todo.sh` if the deferred item had a backlog entry.
- `evaluated` → `skipped`: just edit the catalog entry, add the rejection reason inline.

## Hub template (`domains/_template.md`)

Every domain hub follows this structure. Template is documented (not blank) so copy-paste produces a coherent stub.

```markdown
# {{Domain name}}

{{One-line elevator pitch — what this domain covers and who would use it.}}

## Skills in this repo

### Local
| Skill | One-line | Notes |
|---|---|---|
| _none yet — open a TODO P? if you want one_ | | |

### Vendored
| Skill | Upstream | Series |
|---|---|---|
| _none yet_ | | |

## External skills (manual install)

--8<-- "_snippets/external-install.md"

| Skill / Plugin | Upstream | Status | Why this status | Install hint |
|---|---|---|---|---|
| _none yet_ | | | | |

## MCP servers

| Name | Upstream | Status | Auth | Records |
|---|---|---|---|---|
| _none yet_ | | | | |

## Backlog (TODO P? items)

- _link to `TODO.md` anchors as items get added; otherwise: "no items yet"_

## See also

- Reference landscape pages: …
- Adjacent domain hubs: …
```

## Domain coverage in PR1

| Hub | PR1 status | Why |
|---|---|---|
| **Finance** | Populated | Has external (`anthropics/financial-services`, `RKiding/Awesome-finance-skills`), MCP (`financialdatasets.ai`), and partial local fit (cross-link to `quantatitive-factor-researcher`). |
| **Quant Research** | Populated | Strong existing local skill (`quantatitive-factor-researcher`) + 4 deferred P? items in TODO.md (VectorBT, VectorBT Pro, Nautilus, Tardis). |
| **AI/ML Research** | Populated | 3 existing local skills + `Orchestra-Research/AI-research-SKILLs` (98 skills, 23 categories) as external + LangChain/fine-tuning P? items. |
| **Web/Fullstack** | Populated | Already has `fullstack-nextjs` series — hub becomes the conceptual home. Cross-links `browser-automation-skills.md`. |
| **Knowledge Work** | Mostly template + 1 external | `anthropics/knowledge-work-plugins` listed as `wishlist`. Honest about emptiness. |
| **Agent Harness** | Template only | Cross-links `reference/sdd-and-harnesses.md`. Hub explicitly says "we don't ship these, we consume them." |

## MCP entry schema (frontmatter)

Every MCP page has YAML frontmatter for future automation (PR2+):

```yaml
---
name: Financial Datasets MCP
slug: financialdatasets-ai
upstream_url: https://docs.financialdatasets.ai/mcp-server
transport: HTTP
auth: OAuth 2.1 + API key
hosting: Hosted (mcp.financialdatasets.ai)
domain: finance
status: wishlist
license: Proprietary
last_verified: 2026-05-13
---
```

Body sections (consistent across all MCP pages):
1. **TL;DR** (2 sentences)
2. **Tools / capabilities** (table, ~6-12 rows)
3. **Auth & install** (one snippet per host: Claude Code, Claude Desktop, Cursor, Managed Agents)
4. **When to use it / When NOT to use it** (paired bullets)
5. **Related skills in this repo** (cross-links)
6. **Upstream sources** (1-3 links)

## Proposed `mkdocs.yml` nav (delta only)

```yaml
nav:
  - Home: index.md
  - Getting Started: getting-started.md
  - Conventions: conventions.md
  - Workflows:
      - Adding vendor skills: workflows/adding-vendor-skills.md
      - Creating local skills: workflows/creating-local-skills.md
      - Adding catalog entries: workflows/adding-catalog-entries.md   # NEW
      - Project memory: workflows/project-memory.md
  - Skills: …                              # unchanged
  - Catalog:                               # NEW top-level section
      - Overview: catalog/index.md
      - Domains:
          - Overview: catalog/domains/index.md
          - Finance: catalog/domains/finance.md
          - Quant Research: catalog/domains/quant-research.md
          - AI/ML Research: catalog/domains/ai-ml-research.md
          - Web & Fullstack: catalog/domains/web-fullstack.md
          - Knowledge Work: catalog/domains/knowledge-work.md
          - Agent Harness: catalog/domains/agent-harness.md
      - External skills: catalog/skill-collections.md
      - MCP wiki:
          - Overview: catalog/mcp/index.md
          - Financial Datasets: catalog/mcp/financialdatasets-ai.md
  - Reference: …                           # unchanged (15 pages stay put)
  - Changelog: changelog.md
```

`llmstxt.sections` add:

```yaml
Catalog:
  - catalog/*.md
  - catalog/domains/*.md
  - catalog/mcp/*.md
```

`not_in_nav` add (so MkDocs doesn't warn about the template page):

```yaml
not_in_nav: |
  /_snippets/
  /catalog/domains/_template.md
```

## Critical files to modify

- `/Volumes/Data/Program/Personal/agent-skills/mkdocs.yml`
- `/Volumes/Data/Program/Personal/agent-skills/Collections.md`
- `/Volumes/Data/Program/Personal/agent-skills/README.md`
- `/Volumes/Data/Program/Personal/agent-skills/CLAUDE.md`
- `/Volumes/Data/Program/Personal/agent-skills/docs/index.md`
- `/Volumes/Data/Program/Personal/agent-skills/docs/index.zh-TW.md`

## Reusable patterns this builds on

- **Landscape page format** — `docs/reference/warp-oz-skills.md` and `browser-automation-skills.md` already use the table-of-options + design-axes + install-snippets shape. Domain hubs and MCP entries inherit this style; do not invent new conventions.
- **Bilingual suffix pattern** — every `*.md` has a `*.zh-TW.md`; new pages follow the same convention. `mkdocs-i18n` `fallback_to_default: true` would let us land EN-only, but the user requested full bilingual in PR1.
- **`mkdocs-llmstxt` sections** — adding `Catalog:` to the sections block lets agents fetch only the catalog portion of `llms-full.txt`.
- **Snippet includes** — `docs/_snippets/install.md` already exists and is included from `index.md` / `getting-started.md` / `README.md`. New `external-install.md` snippet uses the same `pymdownx.snippets` + `--8<-- "_snippets/external-install.md"` mechanism.
- **Project memory workflow** — `add-todo.sh` / `add-vendor.sh` / `promote-todo.sh` exist and don't change. Catalog status changes use them as-is.

## Order of operations (single PR)

1. Write `docs/_snippets/external-install.md` (defines the status enum that every other page references).
2. Write `docs/catalog/domains/_template.md` (defines the hub structure that every hub copies).
3. Write 6 EN domain hubs (finance → quant-research → ai-ml-research → web-fullstack → knowledge-work → agent-harness).
4. Write `docs/catalog/skill-collections.md` (migrate Collections.md + README Resources, attach status enum to every entry).
5. Write `docs/catalog/mcp/index.md` + `mcp/financialdatasets-ai.md`.
6. Write `docs/catalog/index.md` + `domains/index.md` (router pages last — they index the others).
7. Write `docs/workflows/adding-catalog-entries.md`.
8. Translate every page above to zh-TW (12 pages → 12 translations).
9. Edit `mkdocs.yml` (nav + `llmstxt.sections` + `not_in_nav`).
10. Convert `Collections.md` (root) to a 5-line stub.
11. Edit `README.md` Resources section.
12. Edit `docs/index.md` + `docs/index.zh-TW.md` (Where to go next).
13. Edit `CLAUDE.md` (add Catalog Workflow subsection).
14. Run `make docs-build` (strict mode catches link errors and missing snippet base paths).
15. Run `make marketplace`, `make kanban` (regression sanity on existing validators).
16. Commit as a single PR with structured commit message.

## Verification

- `make docs-build` succeeds in strict mode (validates every internal link and snippet include).
- `make docs-serve` — manually click through `Catalog → each domain hub → each MCP page` and verify cross-links to `docs/skills/*` and `docs/reference/*` resolve.
- Toggle EN ↔ zh-TW in the served site; verify each new page has a translation. Spot-check 2-3 zh-TW translations for content parity.
- `make marketplace` still passes (PR doesn't touch `vendor.yaml` or `marketplace.json`, so no regression expected — but verify).
- `make kanban` still passes (PR doesn't touch `TODO.md` format).
- `cat site/llms.txt` and `head -200 site/llms-full.txt` — verify the new `Catalog` section appears in the generated llmstxt outputs.
- Verify `Collections.md` stub at repo root renders correctly on GitHub (markdown-only redirect; no HTTP redirect).

## Anti-scope (NOT doing in this PR)

- **Don't move existing `docs/reference/*.md` landscape pages.** They stay; Catalog cross-links them. Reference is for "our own format/recipe docs"; Catalog is for "external awareness."
- **Don't vendor any new skills.** That's a follow-up PR per skill (or per series).
- **Don't edit `vendor.yaml` or `marketplace.json`.** Catalog cross-references them; doesn't replace them.
- **Don't change `docs/skills/` structure.** Per-skill flat pages are the right shape.
- **Don't build automation scripts yet.** Frontmatter validator and MCP-index regenerator wait until 5+ MCPs / 10+ external entries justify the maintenance cost. Add as P3 TODOs after PR1.
- **Don't pre-populate hubs with speculative content.** Empty template is honest; bullshit content erodes trust.
- **Don't translate `_template.md` to zh-TW.** It's not in nav and templates are EN-only by convention (template + zh-TW template would have to stay in sync forever).

## Follow-up TODOs to add after PR1

(Add via `./scripts/add-todo.sh` once PR1 ships — kept out of this plan to avoid scope creep.)

- **[S/P3]** `scripts/validate-catalog-frontmatter.sh` — lint required keys on every `catalog/mcp/*.md`; verify `domain:` field matches an existing hub page.
- **[S/P3]** MCP index auto-regenerator — read frontmatter from `mcp/*.md`, regenerate the table inside `mcp/index.md` between marker comments. Build when 5+ MCP entries.
- **[M/P3]** Cross-link audit script — every catalog entry with `status: vendored` should resolve to a real `vendor.yaml` line; every `status: deferred` should resolve to a TODO.md item.
- **[?/M]** Build a P? "AI/ML research skills" series in `vendor.yaml` (mirroring `fullstack-nextjs`) once 3+ candidates from `Orchestra-Research/AI-research-SKILLs` are vetted via the new catalog hub.
- **[?/M]** Decide whether to vendor any of the `anthropics/financial-services` plugins (or pull individual skills out of them) — currently `wishlist` in the Finance hub.
