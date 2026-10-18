# `make sync-check` says "update available", then `make sync` finds no files

## Symptom

`make sync-check` looks healthy:

```
Checking nextjs (vercel/vercel-plugin)... update available (c2d6e61..ee6f762)
Checking shadcn (vercel/vercel-plugin)... update available (7a73b56..26a8fbe)
```

but the real sync then fails hard on the same entry:

```
Checking nextjs (vercel/vercel-plugin)... syncing...
Error: No files found at vercel/vercel-plugin/skills/nextjs
make: *** [sync] Error 1
```

## Root cause

`--check` only compares the latest commit that **touched** `upstream.path`
with `last_sync.commit`. The commit that deletes a directory also touches the
path, so a removal looks like an ordinary update. Only the download step, which
lists the tree at that commit, finds the path is gone. Seen on 2026-10-18:
vercel/vercel-plugin#282 (`ee6f762`, removed `nextjs`) and #291 (`01ff695`,
removed `shadcn`; `26a8fbe` touched it afterwards).

## Workaround

When `make sync` reports `No files found`:

1. Check the last commit's message:
   `gh api "repos/<owner>/<repo>/commits?path=<path>&per_page=3"`.
2. If upstream removed the skill, add a `frozen:` block (`reason:` + `since:`)
   to the `vendor.yaml` entry. If it was renamed, update `name`/`path` and add
   `renamed_from:` (see CLAUDE.md "When an upstream skill is renamed or removed").
3. Re-run `make sync`. Add a "Frozen" admonition to the skill's docs page.

## Prevention

Don't read "update available" as "the path still exists". Before you plan a
sync around `make sync-check` output, run `make sync` (or check the newest
commit message for each updated entry) to see whether anything was removed.
