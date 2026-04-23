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

# Or via Makefile
make add-vendor SOURCE=owner/repo/path/to/skill

# GitHub URLs also work
./scripts/add-vendor.sh https://github.com/marimo-team/skills/tree/main/skills/marimo-notebook
```

This verifies the upstream path exists, adds an entry to `vendor.yaml`, and
syncs the skill immediately. Pass `--no-sync` to only add the entry without
downloading.

**Dependencies:** `gh` (GitHub CLI, authenticated) and `yq` (YAML processor).

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
