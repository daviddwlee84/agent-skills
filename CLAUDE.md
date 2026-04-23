# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

A personal agent skills collection installable via `npx skills@latest add daviddwlee84/agent-skills`. Contains custom-authored skills (`skills/local/`) and cherry-picked 3rd-party skills (`skills/vendor/`) synced from upstream repos.

The skills CLI discovers skills by checking `skills/` one level deep for `SKILL.md`, then falls back to recursive search (up to 5 levels). The nested `local/`/`vendor/` structure works because of this fallback behavior.

## Commands

```bash
# Sync all vendored skills from upstream
make sync

# Check for upstream updates (dry-run)
make sync-check

# Validate and render the repo backlog board
make kanban

# Add a new vendored skill (auto-syncs)
./scripts/add-vendor.sh owner/repo/path/to/skill
./scripts/add-vendor.sh https://github.com/owner/repo/tree/branch/path/to/skill

# Create a new local skill
cd skills/local && npx skills@latest init [skill-name]
```

## Vendor System

- `vendor.yaml` — manifest of upstream skill sources with `last_sync` tracking (date + commit SHA)
- `scripts/sync-vendor.sh` — downloads skill files via GitHub API (`gh` + `yq` required)
- `scripts/add-vendor.sh` — adds entries to `vendor.yaml`, verifies upstream exists, deduplicates

Sync uses the git trees API to recursively download skill directories (SKILL.md + references/ etc.) and updates `vendor.yaml` with the latest commit SHA.

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

When implementing a TODO item, in the same commit:

1. Move it to `## Done`
2. Rewrite it as `- ✅ [YYYY-MM-DD] [P#/Effort] Title — one-line shipped summary`
3. Mark the related `backlog/<slug>.md` as shipped if one exists

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
