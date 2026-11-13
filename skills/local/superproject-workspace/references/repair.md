# Repair: severed child worktrees and stale submodule state

## Symptom

```text
$ cd .worktrees/app/feat && git status
fatal: not a git repository: /path/super/.git/worktrees/wt-1/modules/app/worktrees/feat
```

A child worktree's `.git` file points to an admin directory that no longer
exists. Its files are still there; git cannot see them. Start with:

```bash
sp audit
sp repair --dry-run
```

## Finding codes

| Code | Meaning | Level | Handled by |
|---|---|---|---|
| `worktree-relinkable` | The `.git` target is gone, but the child's store still has the admin dir (the superproject or store moved) | warn | `repair` (no flag) |
| `worktree-orphan` | The `.git` target is gone and no admin dir exists. `cause = superproject-worktree-removed` when the old path was under `.git/worktrees/<x>/modules/`, else `store-missing` | error | `--reattach` or `--delete-orphans PATH` |
| `worktree-prunable` | Registered, but the directory is gone | info | `--prune` |
| `worktree-at-risk` | Healthy, but registered in the store of a superproject linked worktree | warn | manual (below) |
| `superproject-worktrees` | The superproject has linked worktrees; warn when they hold initialized submodules | info/warn | manual |
| `stale-submodule-config` | `.git/config` has `submodule.<n>.*` that `.gitmodules` no longer declares | info | `--prune` |
| `stale-module-store` | `.git/modules/<n>` exists for an undeclared submodule | info | manual (below) |
| `checkout-broken` | A submodule checkout is `broken` (`.git` does not open) or `foreign` (files, no `.git`) | error | manual (below) |

## What each invocation may do

| Invocation | Does |
|---|---|
| `repair` | Lossless only: `git -C <child> worktree repair <dir>` for each relinkable worktree, verified with `rev-parse`. Lists everything else and the flag that handles it. |
| `repair --prune` | `git worktree prune` in children with prunable entries; `git config --remove-section submodule.<n>` for stale config. Never touches files or stores. |
| `repair --reattach [--base REV] [PATH...]` | Reattach each orphan to the child's durable store (below). Working files are not modified. |
| `repair --delete-orphans PATH...` | Delete the named directories, only if the scan confirms each is an orphan. `--dry-run` prints the file count and newest mtime. The only step that deletes a directory. |

`PATH` restricts the actions to those directories. Exit 1 when an action fails
or error-level findings remain.

## How reattach works

1. Refuse if the child's own store is not durable (same guard as `worktree add`).
2. `git -C <child> worktree add --no-checkout -b rescue/<dir> <tmp> <base>`,
   where `<base>` is `--base` or the recorded gitlink.
3. Point `<orphan>/.git` at the new admin dir and the admin dir's `gitdir`
   back at `<orphan>/.git`; remove the temporary directory.
4. `git -C <orphan> reset -q`: the index follows `rescue/<dir>`; files stay.

Afterwards the worktree is on `rescue/<dir>`, and your edits show as
modifications against the base. **Commits made in the orphan that were never
pushed are gone**: they lived in the deleted store. Compare against the
branch you pushed, if any, then continue or `task close`/`worktree remove` as
usual.

## Manual steps

**`worktree-at-risk`** (do this before the outer worktree is removed):

1. In the child worktree, commit and `git push -u origin <branch>`.
2. `git worktree remove <path>` from the linked worktree's child.
3. From the main checkout: `sp worktree add <child> <branch>` (or `task open`).

**`stale-module-store`**: the store may hold the only copy of unpushed
commits. `git --git-dir=.git/modules/<n> log --branches --not --remotes`
lists them. Push or save what matters, then delete the directory by hand.
The CLI never deletes a store.

**`checkout-broken`**: move the directory aside (`mv app app.broken`), run
`sp init app`, copy the files you need back, then delete `app.broken`.

## Why `rm -rf` plus `git worktree prune` is not cleanup

Deleting a superproject worktree with `rm -rf` and pruning removes its admin
directory, and with it every submodule store initialized there. Child
worktrees registered in those stores become orphans, and their unpushed
commits vanish. Use `git worktree remove` on child worktrees first, push
their branches, and keep child work in the main checkout (see the guard in
`worktrees.md`). Removing the remaining entries of `git worktree list` by
hand has the same effect on whatever they hold.
