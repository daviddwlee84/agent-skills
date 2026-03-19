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
