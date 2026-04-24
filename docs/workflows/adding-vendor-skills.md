# Adding vendor skills

Vendor skills are third-party skills cherry-picked from upstream repos
into [`skills/vendor/`](https://github.com/daviddwlee84/agent-skills/tree/main/skills/vendor).
The [`vendor.yaml`](https://github.com/daviddwlee84/agent-skills/blob/main/vendor.yaml)
manifest tracks each upstream source plus the last-synced date and commit
SHA, so re-syncing is reproducible.

## Quick add

```bash
./scripts/add-vendor.sh owner/repo/path/to/skill

# Examples
./scripts/add-vendor.sh marimo-team/skills/skills/marimo-notebook
./scripts/add-vendor.sh vercel-labs/agent-skills/skills/next-js
./scripts/add-vendor.sh --name my-name --branch dev owner/repo/skills/some-skill

# Group into a series subdir
./scripts/add-vendor.sh --series fullstack-nextjs vercel/vercel-plugin/skills/nextjs

# Or via Makefile
make add-vendor SOURCE=owner/repo/path/to/skill

# GitHub URLs also work
./scripts/add-vendor.sh https://github.com/marimo-team/skills/tree/main/skills/marimo-notebook
```

This verifies the upstream path exists, adds an entry to `vendor.yaml`, and
syncs the skill immediately. Pass `--no-sync` to only add the entry without
downloading.

**Dependencies:** `gh` (GitHub CLI, authenticated) and `yq` (YAML processor).

## Series grouping

When you're vendoring a coherent set of skills around a single tech stack
(e.g. Next.js + Supabase + shadcn), pass `--series <name>` so the skills
land in `skills/vendor/<series>/<name>/` instead of being flat. The
`series` field is recorded in `vendor.yaml` and honored by `sync-vendor.sh`.

```yaml
# vendor.yaml
- name: nextjs
  series: fullstack-nextjs              # ← optional, omit for flat layout
  upstream:
    owner: vercel
    repo: vercel-plugin
    path: skills/nextjs
    branch: main
  last_sync: { date: "...", commit: "..." }
```

This results in `skills/vendor/fullstack-nextjs/nextjs/SKILL.md`. The
`npx skills@latest add` discovery does a 5-level fallback recursive
search, so series subdirs are still discovered.

Existing flat entries (no `series` field) keep working unchanged. Active
series in this repo:

- **`fullstack-nextjs`** — see [Skills overview > Fullstack Next.js series](../skills/index.md#fullstack-nextjs-series)

## Manual config

If you'd rather edit `vendor.yaml` by hand:

```yaml
- name: my-skill
  upstream:
    owner: org-name
    repo: skills-repo
    path: skills/my-skill
    branch: main
  last_sync:
    date: ""
    commit: ""
```

Then run `make sync` to download and stamp `last_sync`.

## Check for upstream updates

```bash
make sync-check
```

This dry-runs the sync against the recorded `last_sync.commit` for each
entry and prints which skills have new commits upstream. Run `make sync`
to apply.

## Why not just install upstream directly?

`npx skills add owner/repo/path/to/skill` works one skill at a time and
leaves no manifest. Vendoring into this repo gives you:

- A single install command for the whole curated set
  (`npx skills@latest add daviddwlee84/agent-skills/skills`).
- A pinned commit per skill so a reckless upstream change doesn't surprise you.
- A diff in your repo when you re-sync, which is your chance to read what
  changed before accepting it.

## Don't edit vendored skills in place

Modifications under `skills/vendor/` get overwritten by `make sync`. If you
need to customize a vendored skill, fork it into `skills/local/` and drop
the upstream entry from `vendor.yaml`. See [Conventions](../conventions.md).
