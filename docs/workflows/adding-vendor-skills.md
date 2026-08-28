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

## Repository-level licenses

If the skill subtree does not contain the upstream license, add `license_path`
to its manifest entry:

```yaml
- name: my-skill
  upstream:
    owner: org-name
    repo: project
    path: skills/my-skill
    branch: main
  license_path: LICENSE
  last_sync:
    date: ""
    commit: ""
    license_sha: ""
```

The sync script copies it to `skills/vendor/<name>/LICENSE.txt` and tracks its
blob SHA independently, so license-only updates are detected by `make sync-check`.

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

## Scheduled sync (GitHub Actions)

[`.github/workflows/vendor-sync.yml`](https://github.com/daviddwlee84/agent-skills/blob/main/.github/workflows/vendor-sync.yml)
runs `make sync` every Monday 03:00 UTC (plus `workflow_dispatch`, which
takes an optional single-skill filter). When there is a diff it runs the
publish gates and opens — or updates — a PR on the fixed branch
`chore/vendor-sync`.

It opens a PR instead of committing to `main` because vendored `SKILL.md`
content ships straight into downstream agents' context via
`npx skills update`, and because a SKILL.md whose frontmatter stops
parsing is [silently skipped](https://github.com/daviddwlee84/agent-skills/blob/main/pitfalls/skill-description-colon-breaks-yaml-frontmatter.md)
by `npx skills add` rather than erroring.

Two things to know:

- **`validate.yml` does not run on the sync PR.** GitHub does not trigger
  workflows for PRs created with `GITHUB_TOKEN`, so the sync job runs the
  gates itself (frontmatter lint, marketplace, kanban, native smoke) and
  reports the result in the PR body.
- **A red job usually means an upstream rename or removal.** `make sync`
  fails hard when `upstream.path` no longer resolves — that needs a human
  to choose `renamed_from:` vs `frozen:` (see
  [conventions](../conventions.md)).

Repo setup required once: **Settings → Actions → General → Workflow
permissions** must be *Read and write* with *Allow GitHub Actions to
create and approve pull requests* enabled.

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
