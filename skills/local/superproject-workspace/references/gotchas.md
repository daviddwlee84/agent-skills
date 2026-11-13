# Submodule gotchas, by symptom

### `modified: app (new commits)` after `git pull`
The outer pull moved the gitlink; the child checkout stayed where it was (or
the reverse: you moved the child). Inspect with `status`. To keep the
checkout, run `bump app`. To discard it, run `git submodule update -- app`.
Setting `git config submodule.recurse true` makes `pull`/`checkout` update
children automatically. That is convenient for consumers, but surprising
while you develop in children, so leave it off in maintainer checkouts.

### `HEAD detached at 1a2b3c4` inside a child
This is normal after `git submodule update`. Commits made in this state belong
to no branch and are easily lost. Save them first:
`git switch -c rescue/<topic>`. `pull` refuses to move a detached commit that
is not on `origin/<branch>`.

### `fatal: remote error: upload-pack: not our ref <sha>` / `Fetched in submodule path 'x', but it did not contain <sha>`
Someone recorded a gitlink to a commit that was never pushed, or was
force-pushed away. Push it if it still exists locally. Otherwise move the
pointer to a pushed commit. Prevent it with `preflight` (pre-commit) and
`push.recurseSubmodules=check`.

### `Submodule 'x' could not be updated` / `update = none` surprises
`update = none` in `.gitmodules` makes plain `git submodule update --init`
skip the child. That is intended for `lazy` children. `init <name>` passes
`--checkout` to override it for that one call.

### Clone still uses the old URL after `.gitmodules` changed
`.git/config` caches submodule URLs at init time. Run
`git submodule sync -- <path>`; `audit` reports `url-unsynced`.

### Nested submodules fail to clone (private descendants)
`--recursive` pulls in every descendant, including private or unrecoverable
ones. The CLI never recurses unless asked. `init --recursive` applies only to
the nested submodules of the children that this call initializes; it does not
touch children that were already initialized. Initialize nested children
explicitly, only when the task needs them.

### Branch named in `.gitmodules` doesn't exist (`origin/main missing`)
The child uses `master`, or a release branch. Set `branch` explicitly. If
`branch` is unset, the CLI uses the child's `origin/HEAD`.

### `git status` shows `.worktrees/` as untracked
Add `.worktrees/` (or your worktree root) to `.gitignore`. `worktree add`,
`task open` and `adopt` do this automatically when the root is inside the
superproject.

### `git status` is noisy with `modified: app (untracked content)`
Build output or editor files inside a child show up in the outer status.
Fix the child's own `.gitignore` first. If a child is legitimately dirty all
the time, opt that one child in with `git config -f .gitmodules
submodule.<name>.ignore dirty`: the outer status then ignores its working
tree but still reports new commits. Never set `ignore = all`; it also hides
gitlink changes, so a moved pointer slips into commits unnoticed.

### A removed child keeps coming back (`stale-submodule-config`, `stale-module-store`)
`git rm <path>` drops the gitlink and the `.gitmodules` section, but leaves
`submodule.<name>.*` in `.git/config` and the store in `.git/modules/<name>`.
Re-adding the same name then reuses the old store and URL. To remove a child
completely:

1. Push or save any work in it (`git -C <path> log --branches --not --remotes`).
2. `git submodule deinit -f -- <path>`
3. `git rm -f <path>` and commit.
4. `sp repair --prune` (drops the `.git/config` section).
5. After checking the store holds nothing you need:
   `rm -rf .git/modules/<name>` by hand. The CLI never deletes a store.

### `fatal: working trees containing submodules cannot be moved or removed`
`git worktree move` (and plain `remove`) refuse worktrees that contain
initialized submodules. Do not move child or task worktrees by hand either:
create a new one where you want it, move your commits there by pushing the
branch, then `worktree remove` / `task close` the old one. If a move already
happened, `sp repair` relinks it.
