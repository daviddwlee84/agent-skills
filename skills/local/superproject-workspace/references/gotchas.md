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
ones. The CLI never recurses unless asked. Initialize nested children
explicitly, only when the task needs them.

### Branch named in `.gitmodules` doesn't exist (`origin/main missing`)
The child uses `master`, or a release branch. Set `branch` explicitly. If
`branch` is unset, the CLI uses the child's `origin/HEAD`.

### `git status` shows `.worktrees/` as untracked
Add `.worktrees/` to `.gitignore`. `worktree add` and `adopt` do this
automatically.
