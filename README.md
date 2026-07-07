# Agent Skills

A personal collection of [agent skills](https://agentskills.io/home) — both custom-authored and cherry-picked from upstream repos — installable as a single package.

📚 **[Read the docs](https://daviddwlee84.github.io/agent-skills/)** for the full guide, conventions, and skill index.

## Install

<!-- snippet:install (keep in sync with docs/_snippets/install.md) -->
```bash
npx skills@latest add daviddwlee84/agent-skills/skills
```

> **Note**
> The trailing `/skills` matters. Without it, `npx skills` will look in
> `.agents/skills/` of the upstream repo, which contains a different
> layout. The `skills/` suffix points the installer at the
> `skills/local/` and `skills/vendor/` trees.
<!-- /snippet:install -->

## What's in here

- **`skills/local/`** — custom-authored skills.
  - [`project-knowledge-harness`](skills/local/project-knowledge-harness/) — TODO + backlog + pitfalls structure with init / kanban / promote / add-todo / sweep-inbox toolkit. ([docs](https://daviddwlee84.github.io/agent-skills/skills/project-knowledge-harness/))
  - [`quantatitive-factor-researcher`](skills/local/quantatitive-factor-researcher/) — Python quant-research persona. ([docs](https://daviddwlee84.github.io/agent-skills/skills/quantatitive-factor-researcher/))
  - [`skill-author`](skills/local/skill-author/) — Author new skills following [agentskills.io](https://agentskills.io/skill-creation/best-practices) best practices; ships `new-skill.sh` scaffolder and `lint-skill.sh` linter. ([docs](https://daviddwlee84.github.io/agent-skills/skills/skill-author/))
  - [`verifiable-surfaces`](skills/local/verifiable-surfaces/) — Design CLIs/tools/services with `--help`/`--dry-run`/`--print-config`/isolated-state smoke, and verify config/CLI/dotfile/IaC changes via app-native loaders before claiming done. ([docs](https://daviddwlee84.github.io/agent-skills/skills/verifiable-surfaces/))
  - [`demo-evidence`](skills/local/demo-evidence/) — Capture acceptance evidence (screenshots, terminal/screen recordings, HTTP logs) for a just-built feature into a gitignored `.evidence/` bundle keyed to git branch/commit + coding-agent session, for async "Demos over diffs" review. Lifecycle: `new-bundle.sh` → `capture.sh <web|term|http|screen>` → `finalize.sh`. ([docs](https://daviddwlee84.github.io/agent-skills/skills/demo-evidence/))
  - [`mkdocs-site-bootstrap`](skills/local/mkdocs-site-bootstrap/) — Bootstrap a MkDocs Material site + GitHub Pages deploy; consent-gated via `.skills/preferences.yaml`; ongoing `add-docs-page.sh` helper. ([docs](https://daviddwlee84.github.io/agent-skills/skills/mkdocs-site-bootstrap/))
  - [`marimo-batch-mlflow`](skills/local/marimo-batch-mlflow/) — Opinionated fork of upstream `marimo-batch`: Tyro CLI (dataclass or Pydantic) + MLflow tracking + live `mlflow-widgets` chart, dual-mode (`mo.app_meta().mode == "script"`) UI/CLI from one notebook. ([docs](https://daviddwlee84.github.io/agent-skills/skills/marimo-batch-mlflow/))
  - [`dvc-ml-workflow`](skills/local/dvc-ml-workflow/) — DVC ([treeverse/dvc](https://github.com/treeverse/dvc)) pipelines + queued experiments with metrics auto-bound to ephemeral commits; ships `init-dvc-project.sh`, `queue-helper.sh` (with `grid` cartesian-product enqueue), `lint-dvcyaml.sh`. ([docs](https://daviddwlee84.github.io/agent-skills/skills/dvc-ml-workflow/))
  - [`mlflow-tracking`](skills/local/mlflow-tracking/) — Generic [MLflow](https://mlflow.org/docs/latest) skill: SQLite + `mlflow ui` for solo, vendored PostgreSQL + MinIO docker-compose stack for teams; covers LLM tracing, model registry (aliases), and autologging across all officially-supported frameworks. ([docs](https://daviddwlee84.github.io/agent-skills/skills/mlflow-tracking/))
  - [`agent-history-hygiene`](skills/local/agent-history-hygiene/) — Commit SpecStory chat transcripts + `.claude/plans/*.md` alongside feature diffs; bootstrap pre-commit + gitleaks + secret-redactor into new repos; enforce rotate-first, rewrite-last leak remediation (never reflexive `git push --force`). ([docs](https://daviddwlee84.github.io/agent-skills/skills/agent-history-hygiene/))
  - [`fastapi-ai-patterns`](skills/local/fastapi-ai-patterns/) — Production FastAPI patterns + gotchas for AI/ML/LLM serving: the `def`/`async def` decision table, event-loop/`lifespan`/`response_model`/BOLA traps up front, and 8 references covering all 10 chapters. Inspired by *FastAPI for AI Engineers* (original wording). ([docs](https://daviddwlee84.github.io/agent-skills/skills/fastapi-ai-patterns/))
  - [`fastapi-ai-scaffold`](skills/local/fastapi-ai-scaffold/) — Generate a runnable, production-shaped FastAPI AI service via `new-fastapi-ai-service.sh` (bash 3.2, `--dry-run`/JSON): a 44-file clean-architecture skeleton with `lifespan`-loaded model, JWT, SSE LLM gateway, guardrails, `/health`+`/ready`, tests, Docker. Verified green out of the box. ([docs](https://daviddwlee84.github.io/agent-skills/skills/fastapi-ai-scaffold/))
  - [`fastapi-ai-interview-prep`](skills/local/fastapi-ai-interview-prep/) — 100 self-written FastAPI/AI-engineering interview Q&A across 10 topics, each with a senior-signal rubric, plus a stdlib `quiz.py` mock-interview CLI (`--random`/`--topic`/`--answer`/`--json`). ([docs](https://daviddwlee84.github.io/agent-skills/skills/fastapi-ai-interview-prep/))
  - [`clash-proxy-api`](skills/local/clash-proxy-api/) — Discover and drive a running Clash/mihomo proxy via its external-controller API: `clash_api.py` (stdlib-only) for status/node/mode/TUN/reload/connections/latency with robust controller discovery (not just `9090` — handles Verge Rev `9097`), plus `clash_sysproxy.sh` to toggle the OS system proxy (macOS `networksetup` / GNOME `gsettings`) and references for enabling the API per client (mihomo CLI, Clash Verge Rev, ClashX). ([docs](https://daviddwlee84.github.io/agent-skills/skills/clash-proxy-api/))
- **`skills/vendor/`** — third-party skills synced from upstream via [`vendor.yaml`](vendor.yaml). Do not edit these locally; `make sync` will clobber changes. Skills can be flat (`skills/vendor/<name>/`) or grouped into a **series** (`skills/vendor/<series>/<name>/`).
  - Flat:
    - [`marimo-notebook`](skills/vendor/marimo-notebook/) — from [marimo-team/skills](https://github.com/marimo-team/skills); general marimo authoring conventions. ([docs](https://daviddwlee84.github.io/agent-skills/skills/marimo-notebook/))
    - [`streamlit-to-marimo`](skills/vendor/streamlit-to-marimo/) — from [marimo-team/skills](https://github.com/marimo-team/skills); convert Streamlit apps to marimo notebooks. ([docs](https://daviddwlee84.github.io/agent-skills/skills/streamlit-to-marimo/))
    - [`anywidget`](skills/vendor/anywidget/) (frontmatter name: `anywidget-generator`) — from [marimo-team/skills](https://github.com/marimo-team/skills); generate anywidget components for marimo notebooks. ([docs](https://daviddwlee84.github.io/agent-skills/skills/anywidget/))
    - [`skill-creator`](skills/vendor/skill-creator/) — from [anthropics/skills](https://github.com/anthropics/skills); evaluate, benchmark, and optimize skill trigger descriptions. Complements local [`skill-author`](skills/local/skill-author/). ([docs](https://daviddwlee84.github.io/agent-skills/skills/skill-creator/))
  - Series **`fullstack-nextjs`** — Next.js (App Router) + Supabase (Postgres) + shadcn/ui + Tailwind CSS + design/testing skills, all from official orgs. See the [series overview](https://daviddwlee84.github.io/agent-skills/skills/#fullstack-nextjs-series).
    - [`nextjs`](skills/vendor/fullstack-nextjs/nextjs/) — Next.js App Router expert from [vercel/vercel-plugin](https://github.com/vercel/vercel-plugin)
    - [`shadcn`](skills/vendor/fullstack-nextjs/shadcn/) — shadcn/ui CLI + components from [vercel/vercel-plugin](https://github.com/vercel/vercel-plugin)
    - [`react-best-practices`](skills/vendor/fullstack-nextjs/react-best-practices/) — TSX reviewer (70+ rules) from [vercel/vercel-plugin](https://github.com/vercel/vercel-plugin)
    - [`vercel-storage`](skills/vendor/fullstack-nextjs/vercel-storage/) — Blob/Edge Config + Supabase/Prisma integration from [vercel/vercel-plugin](https://github.com/vercel/vercel-plugin)
    - [`supabase`](skills/vendor/fullstack-nextjs/supabase/) — full Supabase product surface from [supabase/agent-skills](https://github.com/supabase/agent-skills)
    - [`supabase-postgres-best-practices`](skills/vendor/fullstack-nextjs/supabase-postgres-best-practices/) — Postgres perf rules from [supabase/agent-skills](https://github.com/supabase/agent-skills)
    - [`web-design-guidelines`](skills/vendor/fullstack-nextjs/web-design-guidelines/) — UI audit reviewer from [vercel-labs/agent-skills](https://github.com/vercel-labs/agent-skills)
    - [`frontend-design`](skills/vendor/fullstack-nextjs/frontend-design/) — anti-AI-slop aesthetics from [anthropics/skills](https://github.com/anthropics/skills)
    - [`webapp-testing`](skills/vendor/fullstack-nextjs/webapp-testing/) — Playwright toolkit from [anthropics/skills](https://github.com/anthropics/skills)

## Categories in the install UI

The grouped picker UI of `npx skills@latest add daviddwlee84/agent-skills/skills`
is driven by [`skills/.claude-plugin/marketplace.json`](skills/.claude-plugin/marketplace.json) —
seven plugin groupings (`skill-authoring`, `project-memory`,
`engineering-quality`, `ml-workflow`, `notebooks`, `fullstack-nextjs`,
`infra-and-docs`) covering all skills in
this repo. Anything not listed there falls under **Other** automatically.

```bash
# Validate the manifest (paths exist, no duplicates, name not reserved,
# on-disk skills covered).
make marketplace
```

The manifest lives under `skills/`, **not** at the repo root, because the
install command's `/skills` subpath makes the CLI read
`<repo>/skills/.claude-plugin/marketplace.json`. See
[npx skills metadata model](https://daviddwlee84.github.io/agent-skills/reference/npx-skills-metadata/)
for the full mechanism, the `kebabToTitle` group naming rule, reserved
marketplace names, and the `marketplace.json` vs `plugin.json` distinction.

## Repo memory

This repo dogfoods `project-knowledge-harness` on itself:

- [`TODO.md`](TODO.md) — priority/effort-tagged backlog.
- [`backlog/`](backlog/) — research notes for `P?` items (when populated).
- [`backlog/inbox.md`](backlog/) — quick-capture inbox; sweep into `TODO.md` later.
- [`pitfalls/`](pitfalls/) — symptom-grep-able knowledge base of past traps (when populated).

```bash
# Validate TODO.md and render kanban-style board
make kanban

# Quick add structured TODO entry
./scripts/add-todo.sh --priority P3 --effort M --title "..." --description "..."

# Move an active TODO to ## Done in same commit as the implementation
./scripts/promote-todo.sh --title "<substring>" --summary "<shipped summary>"

# Triage backlog/inbox.md interactively
./scripts/sweep-inbox.sh
```

Full workflow: [Project memory](https://daviddwlee84.github.io/agent-skills/workflows/project-memory/).

## Vendor system

```bash
# Add a vendored skill (auto-syncs)
./scripts/add-vendor.sh owner/repo/path/to/skill
# or via Makefile
make add-vendor SOURCE=owner/repo/path/to/skill

# Group into a series subdir (skills/vendor/<series>/<name>/)
./scripts/add-vendor.sh --series fullstack-nextjs vercel/vercel-plugin/skills/nextjs

# Sync all vendored skills from upstream
make sync

# Check for upstream updates (dry-run)
make sync-check
```

Full workflow: [Adding vendor skills](https://daviddwlee84.github.io/agent-skills/workflows/adding-vendor-skills/).

**Dependencies:** `gh` (GitHub CLI, authenticated) and `yq` (YAML processor).

## Docs site

The docs site is built with MkDocs Material + `mkdocs-llmstxt` + `mkdocs-copy-to-llm`.

```bash
uv sync --extra docs
make docs-serve         # http://127.0.0.1:8000/
make docs-build         # produces ./site/
```

Deployed automatically to GitHub Pages on push to `main` via [`.github/workflows/docs.yml`](.github/workflows/docs.yml).

If you want to apply the same docs stack to your own project, see [Downstream docs stack recipe](https://daviddwlee84.github.io/agent-skills/reference/docs-stack-recipe/).

## Adding a new local skill

Use the bundled scaffolder (recommended — seeds the agentskills.io best-practice
template **and** fans out discovery symlinks for non-universal agents):

```bash
# Auto-detects scope: LOCAL (this repo) / PROJECT (another git repo) / GLOBAL (~/).
bash skills/local/skill-author/scripts/new-skill.sh <skill-name>

# Override scope explicitly when intent isn't obvious:
bash skills/local/skill-author/scripts/new-skill.sh --project <skill-name>
bash skills/local/skill-author/scripts/new-skill.sh --global  <skill-name>

bash skills/local/skill-author/scripts/lint-skill.sh skills/local/<skill-name>
```

The scaffolder mirrors `npx skills add`'s placement contract — canonical
content goes under `.agents/skills/<name>/` (read directly by Cursor /
Codex / OpenCode / Warp / Gemini-CLI / Copilot), with relative symlinks
fanned out to `.claude/skills/` and any other already-present
non-universal agent dir. In this repo (LOCAL mode) the canonical lives
in `skills/local/<name>/` and the symlinks point back at it. See
[Creating local skills](https://daviddwlee84.github.io/agent-skills/workflows/creating-local-skills/)
for the full scope table.

Or, just the SKILL.md skeleton via the upstream init (no symlinks, no
`references/` / `scripts/` / `assets/`):

```bash
cd skills/local
npx skills@latest init [skill-name]
```

## Resources

The full curated index of upstream skill collections, MCP servers, and
domain-specific hubs lives in the docs site:

📚 **[Catalog](https://daviddwlee84.github.io/agent-skills/catalog/)** —
external skill collections, per-domain hubs (Finance, Quant Research, AI/ML
Research, Web & Fullstack, Knowledge Work, Agent Harness), and an MCP wiki.

Highlights:

- [Skill collections index](https://daviddwlee84.github.io/agent-skills/catalog/skill-collections/) — every upstream we track, with `vendored / deferred / skipped / evaluated / wishlist` status per entry.
- [Finance hub](https://daviddwlee84.github.io/agent-skills/catalog/domains/finance/) — covers `anthropics/financial-services`, `RKiding/Awesome-finance-skills`, the [Financial Datasets MCP](https://daviddwlee84.github.io/agent-skills/catalog/mcp/financialdatasets-ai/), and more.
- [Adding catalog entries workflow](https://daviddwlee84.github.io/agent-skills/workflows/adding-catalog-entries/) — how to record an external skill / MCP / domain decision.
