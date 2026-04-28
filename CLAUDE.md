# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

A personal agent skills collection installable via `npx skills@latest add daviddwlee84/agent-skills`. Contains custom-authored skills (`skills/local/`) and cherry-picked 3rd-party skills (`skills/vendor/`) synced from upstream repos.

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

- `vendor.yaml` — manifest of upstream skill sources with `last_sync` tracking (date + commit SHA). Optional per-entry `series:` field groups skills under `skills/vendor/<series>/<name>/`; entries without `series` stay flat at `skills/vendor/<name>/`
- `scripts/sync-vendor.sh` — downloads skill files via GitHub API (`gh` + `yq` required); honors the `series` field for nested destinations
- `scripts/add-vendor.sh` — adds entries to `vendor.yaml`, verifies upstream exists, deduplicates; pass `--series <name>` to group into a series subdir

Sync uses the git trees API to recursively download skill directories (SKILL.md + references/ etc.) and updates `vendor.yaml` with the latest commit SHA.

Active series in this repo:
- `fullstack-nextjs` — Next.js + Supabase + shadcn/ui + Tailwind + design/testing skills (9 skills from vercel/vercel-plugin, vercel-labs/agent-skills, supabase/agent-skills, anthropics/skills)

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

## SKILL.md Format

Each skill is a directory containing a `SKILL.md` with YAML frontmatter (`name`, `description`) and markdown body with instructions, conventions, and examples. Vendored skills may include `references/` subdirectories.

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

### Past pitfalls -> `pitfalls/`

When a debugging session uncovers a non-obvious trap that could realistically be
hit again, write `pitfalls/<slug>.md` with:

1. The verbatim symptom or error text
2. The root cause
3. The workaround
4. Prevention guidance or the hard invariant that supersedes it

Use symptom-first titles so future agents can grep the failure they see, not
the explanation they do not know yet.
