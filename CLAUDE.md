# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

A personal agent skills collection installable via `npx skills@latest add daviddwlee84/agent-skills/skills`. Contains custom-authored skills (`skills/local/`) and cherry-picked 3rd-party skills (`skills/vendor/`) synced from upstream repos.

The skills CLI discovers skills by checking `skills/` one level deep for `SKILL.md`, then falls back to recursive search (up to 5 levels). The nested `local/`/`vendor/` structure works because of this fallback behavior — including vendor `series` subdirs (e.g. `skills/vendor/fullstack-nextjs/<name>/SKILL.md` at depth 4).

## Commands

```bash
# Sync all vendored skills from upstream
make sync

# Check for upstream updates (dry-run)
make sync-check

# Validate and render the repo backlog board
make kanban

# Validate skills/.claude-plugin/marketplace.json (the catalog manifest
# that drives the grouped install UI of `npx skills add ...`).
make marketplace

# Exercise native Claude Code + Codex marketplace add/list/install in isolated state.
make native-marketplace-smoke

# YAML-parse every skills/**/SKILL.md frontmatter. A file that fails to parse
# is silently skipped by `npx skills add` — run this before publishing.
make lint-frontmatter

# All portable publish gates at once (frontmatter + marketplace + TODO format).
# CI additionally runs `make native-marketplace-smoke` with pinned CLIs.
make validate

# Install scripts/git-hooks/pre-push so `git push` runs `make validate` first.
make install-hooks

# Add a new vendored skill (auto-syncs)
./scripts/add-vendor.sh owner/repo/path/to/skill
./scripts/add-vendor.sh https://github.com/owner/repo/tree/branch/path/to/skill
# Group under a series subdir (skills/vendor/<series>/<name>/)
./scripts/add-vendor.sh --series fullstack-nextjs vercel/vercel-plugin/skills/nextjs

# Add a structured TODO entry (preferred over editing TODO.md by hand)
./scripts/add-todo.sh --priority P3 --effort M \
  --title "Title" --description "Description"

# Triage backlog/inbox.md (loose captures) into TODO.md
./scripts/sweep-inbox.sh             # interactive
./scripts/sweep-inbox.sh --batch     # only formalize parseable key=value lines

# Move an active TODO item to ## Done with the right syntax
./scripts/promote-todo.sh --title "<substring>" --summary "<shipped summary>"

# Create a new local skill
cd skills/local && npx skills@latest init [skill-name]

# Docs site (MkDocs Material + llmstxt + copy-to-llm)
uv sync --extra docs
make docs-serve     # http://127.0.0.1:8000/
make docs-build     # produces ./site/
```

## Vendor System

- `vendor.yaml` — manifest of upstream skill sources with `last_sync` tracking (date + commit SHA). Optional per-entry `series:` field groups skills under `skills/vendor/<series>/<name>/`; optional `license_path:` copies a repo-level license into the vendored directory as `LICENSE.txt`; entries without `series` stay flat at `skills/vendor/<name>/`
- `scripts/sync-vendor.sh` — downloads skill files via GitHub API (`gh` + `yq` required); honors the `series` field for nested destinations, and skips any entry carrying a `frozen:` block (see below)
- `scripts/add-vendor.sh` — adds entries to `vendor.yaml`, verifies upstream exists, deduplicates; pass `--series <name>` to group into a series subdir

Sync uses the git trees API to recursively download skill directories (SKILL.md + references/ etc.) and updates `vendor.yaml` with the latest commit SHA. When `license_path` is present it also tracks the license blob SHA, so a license-only upstream change is visible to `make sync-check`.

`.github/workflows/vendor-sync.yml` runs `make sync` weekly (Mon 03:00 UTC,
plus `workflow_dispatch` with an optional single-skill filter) and opens/updates
a PR on the fixed branch `chore/vendor-sync` — never a direct commit to `main`,
because vendored content ships to downstream agents via `npx skills update` and
a broken frontmatter is silently skipped rather than erroring. PRs created with
`GITHUB_TOKEN` do not trigger `validate.yml`, so the sync job runs the publish
gates itself. A red sync job usually means an upstream rename/removal — handle
it with `renamed_from:` or `frozen:` as below.

Active series in this repo:
- `fullstack-nextjs` — Next.js + Supabase + shadcn/ui + Tailwind + design/testing skills (9 skills from vercel/vercel-plugin, vercel-labs/agent-skills, supabase/agent-skills, anthropics/skills)

### When an upstream skill is renamed or removed

Upstream repos reorganize; `make sync` fails hard if a tracked
`upstream.path` no longer exists (the download step finds no files).
Handle the two cases explicitly in `vendor.yaml`:

- **Renamed upstream** — update `name` + `upstream.path` to the new
  values, `git mv` the vendored dir, fix that skill's `skills[]` path in
  `marketplace.json`, and add a `renamed_from: <old-name>` field so the
  history stays greppable. Renaming changes the *downstream* install id:
  the `npx skills` CLI has no lockfile, so users who installed the old
  name won't auto-map on `npx skills update`.
- **Removed upstream** — freeze it with a `frozen:` block (`reason:` +
  `since:`). `sync-vendor.sh` then skips the entry in both `make sync`
  and `make sync-check` while keeping the last-synced copy and its
  `marketplace.json` entry. Don't delete a vendored copy just because
  upstream did — unless you also mean to stop shipping it.

Live examples in `vendor.yaml`: `diagnosing-bugs` (`renamed_from: diagnose`)
and `zoom-out` (`frozen:`), both from the 2026-07-05 mattpocock/skills reorg.

## Marketplace Catalog

`skills/.claude-plugin/marketplace.json` defines the user-facing plugin
groupings shown by `npx skills@latest add daviddwlee84/agent-skills/skills`.
Located under `skills/` (not repo root) because the `/skills` subpath in
the install command makes the CLI read the manifest from
`<repo>/skills/.claude-plugin/marketplace.json` — see
[`docs/reference/npx-skills-metadata.md`](docs/reference/npx-skills-metadata.md)
for the full mechanism.

When adding a new skill (local or vendored), also append its path to the
matching plugin's `skills[]` array in the manifest, or accept that it
will fall through to the **Other** group. Run `make marketplace` after
editing — the validator catches broken paths, duplicates, and reserved
marketplace names. Path format is `./local/<name>` or
`./vendor/<name>` (relative to `skills/`, not repo root).

**Picker ordering is alphabetical-only.** `npx skills` sorts groups by
`plugins[].name` (A→Z) and skills within a group by their `SKILL.md`
`name` — the `plugins[]` / `skills[]` array order is ignored. To pin a
frequently-used group to the top, prefix its `name` with two digits: this
repo pins `01-project-memory`, `02-skill-authoring`, `03-infra-and-docs`,
`04-ml-workflow`, `05-notebooks`; the rest stay alphabetical. **These
`NN-` prefixes are deliberate — don't strip them.** Full mechanism +
within-group caveat in
[`docs/reference/npx-skills-metadata.md`](docs/reference/npx-skills-metadata.md).

## SKILL.md Format

Each skill is a directory containing a `SKILL.md` with YAML frontmatter (`name`, `description`) and markdown body with instructions, conventions, and examples. Vendored skills may include `references/` subdirectories.

## Local Skill Discovery Symlinks (`.agents/skills/`, `.claude/skills/`)

The `.agents/skills/<name>` and `.claude/skills/<name>` entries are
**discovery symlinks** that make a skill active in *this* repo's own agent
context (Cursor and Claude Code load whatever resolves under those dirs).
They are unrelated to distribution — downstream users get skills via
`npx skills add ...` + `marketplace.json` regardless of these links.

`scripts/new-skill.sh --local` (run by the `skill-author` skill) creates
both links automatically. **Only keep them for skills that are genuinely
useful while working _on this repo_** — e.g. `skill-author`,
`mkdocs-site-bootstrap`. Skills authored here purely for downstream use
(e.g. `fastapi-ai-*`, `dvc-ml-workflow`, `mlflow-tracking`) should **not**
be symlinked: they would load into every in-repo agent session and just
bloat/pollute context without ever being exercised here. The canonical copy
under `skills/local/<name>/` is all that's needed for distribution.

To author a downstream-only skill without the links, either:

```bash
# Skip the symlinks at creation time
bash skills/local/skill-author/scripts/new-skill.sh --local --no-symlinks <name>

# …or remove them afterward
rm .agents/skills/<name> .claude/skills/<name>
```

## Project Memory Workflow

### Long-term backlog -> `TODO.md` + `backlog/`

When work is explicitly deferred, add it to [`TODO.md`](TODO.md) using the
fixed section order `P1`, `P2`, `P3`, `P?`, `Done`.

- Active items must use `- [ ] **[Effort] Title** — description`
- `P?` items must use `- [ ] **[?/Effort] Title** — description`
- Non-trivial research should be linked as `→ [research](backlog/<slug>.md)`

`TODO.md` is parsed by [`scripts/todo-kanban.sh`](scripts/todo-kanban.sh), so
do not invent alternate headings, nested bullets, or ad hoc checkbox formats.

#### Three ways to add a TODO entry (preferred order)

1. **Structured CLI — `scripts/add-todo.sh`** (default):

   ```bash
   ./scripts/add-todo.sh --priority P3 --effort M \
     --title "Title" --description "Description"
   # add --backlog to also scaffold backlog/<slug>.md
   ```

   This inserts a canonically-formatted line into the right `## P*` lane
   and re-runs the validator. Refuses to write a malformed entry.

2. **Quick capture — `backlog/inbox.md`** (when priority/effort unclear):

   ```bash
   echo "- maybe add docs versioning with mike" >> backlog/inbox.md
   ```

   When the user asks "sweep the inbox" or "clear inbox.md", run
   [`./scripts/sweep-inbox.sh`](scripts/sweep-inbox.sh). It prompts for
   priority/effort/title/description per loose line and calls
   `add-todo.sh`. Use `--batch` for non-interactive runs that only
   formalize lines with parseable `key=value` pairs.

3. **Direct edit of `TODO.md`** — fine if the format is fresh in your
   head; run `make kanban` (or `./scripts/todo-kanban.sh --validate-only`)
   afterwards to catch drift.

#### Promote a TODO when implementing it

When implementing a TODO item, in the same commit run:

```bash
./scripts/promote-todo.sh --title "<substring>" --summary "<one-line shipped summary>"
```

That moves the matched active item into `## Done` with the dated `Done`
syntax and re-validates the file. If a `backlog/<slug>.md` exists for the
item, also mark it as shipped (don't delete — keep it as historical record).

Keep `## Done` as the recent history buffer. Prune it into `CHANGELOG.md` only
when it contains items from a previous calendar year or grows past 20 entries.

### External skill / MCP / domain catalog -> `docs/catalog/`

`docs/catalog/` is the vendoring decision log + external-awareness
registry, separate from `Skills` (what we ship) and `Reference` (our
own conventions). It has three subareas:

- `docs/catalog/domains/` — per-domain hub pages (one per professional
  domain: Finance, Quant Research, AI/ML Research, Web & Fullstack,
  Knowledge Work, Agent Harness). Each hub aggregates local + vendored
  + external skills + MCPs relevant to that domain. New hubs copy
  [`docs/_snippets/domain-hub-template.md`](docs/_snippets/domain-hub-template.md).
- `docs/catalog/skill-collections.md` — single curated index of all
  upstream skill collections (Anthropic, Vercel, Supabase, marimo,
  Warp Oz, Orchestra-Research, etc.) with status per entry. Replaces
  the historical `Collections.md` (kept as a stub).
- `docs/catalog/mcp/` — MCP wiki, modeled after Karpathy's
  [LLM Wiki pattern](docs/reference/llm-wiki-pattern.md). One markdown
  file per MCP with required YAML frontmatter
  (`name / slug / upstream_url / transport / auth / hosting / domain /
  status / license / last_verified`).

Every external entry carries a status enum (single source of truth in
`docs/_snippets/external-install.md`):

| Status | Meaning |
|---|---|
| `vendored` | In `vendor.yaml` — link to the entry. |
| `deferred` | Open `TODO P?` item — link to it. |
| `skipped` | Looked at, chose not to vendor — inline reason required. |
| `evaluated` | Read but no decision — 1-line note. |
| `wishlist` | Surfaced but not yet evaluated — default for fresh discoveries. |

Status changes trigger existing scripts:
`wishlist → deferred` runs `add-todo.sh`; `deferred → vendored` runs
`add-vendor.sh` + optionally `promote-todo.sh`. Full recipe in
[`docs/workflows/adding-catalog-entries.md`](docs/workflows/adding-catalog-entries.md).

Every published catalog page is bilingual (`*.md` + `*.zh-TW.md`).
Snippets and `_template.md` are EN-only by convention.

### Past pitfalls -> `pitfalls/`

When a debugging session uncovers a non-obvious trap that could realistically be
hit again, write `pitfalls/<slug>.md` with:

1. The verbatim symptom or error text
2. The root cause
3. The workaround
4. Prevention guidance or the hard invariant that supersedes it

Use symptom-first titles so future agents can grep the failure they see, not
the explanation they do not know yet.
