---
name: superproject-workspace
description: 'Set up and keep a multi-repo workspace on track as one agent entry point: a git-submodule superproject (recommended; per-child track/pin/lazy policy in .gitmodules, lag/drift status, preflighted gitlink bumps in one outer commit, scheduled bump PRs) or a pointer-only home repo (a manifest of plain clones, cloned on demand). Covers new/add from zero, child and cross-repo task worktrees, repair of orphaned worktrees, a repo map for agents, and audit/adopt for existing setups. Use when a repo has .gitmodules or .superproject, or the user wants to create a superproject or home repo, add a repo to it, update/sync/bump submodules, branch inside a child, work across several repos in one task, fix "fatal: not a git repository" in a child worktree, or asks monorepo vs submodules; incl. "開 home repo / 跨 repo worktree / submodule 落後 / 更新 submodule / 拉到 latest main".'
---

# superproject-workspace

A superproject is a repo whose job is to hold other repos as git submodules,
so that one agent session gets every repo's context and edit access while each
repo keeps its own remote, PRs, and release cycle. (A pointer-only *home repo*
does the same without submodules; see "Two modes".) The cost: **a gitlink
records a commit, not a branch.** Children merge PRs and the superproject
silently falls behind; checkouts end up detached, dirty, or on stray branches;
pointers reference commits nobody pushed. Drift is the default, not a bug.

This skill makes drift **visible** and moves pointers **by policy**, with one
CLI (`scripts/superproject.py`, stdlib Python ≥3.10, PEP 723). Every
superproject **references** the installed skill's CLI instead of copying it,
so `npx skills update` upgrades all of them at once. Otherwise the tool itself
would drift the same way the gitlinks do.

## When to use

- The repo has `.gitmodules` and the user wants to update, sync, or "pull latest" children.
- After a child PR merges, to move the superproject pointer.
- Starting feature work inside a child repo from the superproject.
- Creating a superproject from scratch (`new`), adding a repo to it (`add`), or deciding *how* to bring repos together (see `references/decision-guide.md`).
- Auditing or upgrading an older superproject that has ad-hoc recipes.

## When NOT to use

- Ordinary single-repo git work: use `git-workflow`.
- Issue/PR lifecycle inside one child: use that child's own workflow (`forge-native-dev`, etc.).
- Ad-hoc reads across a few checkouts for one session: Project / `--add-dir` is enough (see the decision guide).
- A third-party manifest tool already manages the clones (`repo`, `mani`, `gita`): keep it, or migrate to pointer mode deliberately.

## Setup commands need an explicit ask

A project's nature rarely changes. `new`, `add` and `adopt` change what the
repo is or add this skill's metadata to it, so run them only when the user
asks for one of these:

- turn this project into a superproject or home repo, or add a repo to it;
- set up a new workspace from zero;
- bring an existing superproject onto this skill's conventions.

A repo that merely has `.gitmodules` is not a request. There, `status`,
`pull`, `bump`, `worktree`, `task`, `audit` and `repair` already work without
adoption. Do not offer `adopt` unprompted; if `audit` reports `policy-missing`
or `agents-block`, mention once that `adopt --dry-run` exists and move on.

## Two modes

| | Submodule superproject (**recommended**) | Pointer home repo (fallback) |
|---|---|---|
| Children | `.gitmodules`, pinned by gitlinks | `[repo "<name>"]` in `.superproject`, plain clones |
| Version snapshot | Yes: one outer commit = an exact set | No |
| `bump` / `preflight` / CI bumps | Yes | No (refused) |
| Clone | by policy (`lazy` on demand) | always on demand (`init <name>`) |
| Worktrees, tasks, repair, audit, repo map | Yes | Yes |

Prefer submodules whenever feasible. Choose pointers only when the outer
history cannot hold gitlinks, the clones must stay where they are, there are
dozens of rarely touched repos, collaborators cannot use submodules, or nobody
would ever bump. Both kinds can coexist in one root. Criteria:
`references/decision-guide.md`; pointer details: `references/home-repo.md`.

## Outer repo rules

1. Call it the *superproject* (submodule mode) or the *home repo* (pointer
   mode); not a monorepo, meta-repo, or agent repo.
2. The outer checkout stays on its default branch. Cross-repo features live on
   child branches; the outer repo only gets short-lived outer-only branches and
   the CI bump branch. (`audit`: `outer-branch`.)
3. Never create a worktree of the outer repo for child work: no
   `git worktree add` there, no `claude --worktree` at the root, no
   `isolation: worktree` subagents. (`audit`: `superproject-worktrees`.)
4. Commit and push children first, then **one** outer commit covers every
   affected gitlink.
5. The helper never commits or pushes on its own (except `bump --commit`, on request).
6. Inside a child, the child's own instruction files win.

## The policy model

Each child declares its policy as extra keys in `.gitmodules`. Git ignores keys
it does not know, so these keys live next to `path` and `url` and cannot fall
out of sync with them.

```ini
[submodule "app"]
    path = app
    url = https://example.com/org/app.git
    branch = main        # tracking branch (native key; unset -> child's origin/HEAD)
    x-policy = track     # track | pin | lazy
    x-bump = pr          # pr | direct | manual   (only for track)
    x-tier = core        # free-form grouping for --tier selection
    x-role = Web client  # one-line purpose, shown in the repo map
    update = none        # lazy only: plain `git submodule update --init` skips it
```

| Policy | Means | Pointer moves | Initialized |
|---|---|---|---|
| `track` | "Be at the latest `origin/<branch>`" | `pull` (ff-only), then `bump`; may be automated (`x-bump`) | by default |
| `pin` | "Be at a known baseline" (production, a release, a reproduction) | only `bump --reason "..."` | by default |
| `lazy` | "Reference material; fetch only when a task needs it" | only `bump --reason` | only when named |
| unset | treated as `pin`; `audit` warns | | |

Bump modes for `track`: `pr` means scheduled CI opens one PR on
`chore/submodule-bump`. `direct` means CI commits to the default branch after
preflight. `manual` means a human or agent runs `bump`. An umbrella where every
child follows main is simply "everything `track`". A workspace hub mixes core
`pin`s with `lazy` references. Details and example configs are in
`references/policies.md`.

## Workflow

Below, `sp` means `uv run --script <skill-dir>/scripts/superproject.py`. For a
global install, `<skill-dir>` is `~/.agents/skills/superproject-workspace`.
After `adopt`, the same commands are available as `just sub-*` recipes. They
resolve the CLI in this order, first match wins:

1. `$SUPERPROJECT_CLI`
2. a vendored `scripts/superproject.py` (opt-in)
3. the project skill install `.agents/skills/...`
4. the global install `~/.agents/skills/...`
5. GitHub raw at `$SUPERPROJECT_CLI_REF` (default `main`)

`just sub-which` prints which one won. Every command takes `--json`. Mutating
commands take `--dry-run`.

### 0. Start from zero, or add a child

```bash
sp new my-workspace          # git init (if needed), .superproject marker, scaffolding
cd my-workspace
sp add <url> --policy track --bump pr --role "Web client"
sp add <url> references/paper-code --name paper-code --policy lazy --tier reference
sp add <url> --pointer --role "Docs site"   # a pointer child: repos/<name>, gitignored

sp new my-home --mode pointer               # a pointer-only home repo; `add` defaults to --pointer
```

`new` refuses a directory inside another repository's work tree, and an
existing root (use `adopt` there). A root is any directory with `.gitmodules`
or `.superproject`; the marker uses git-config syntax and holds `[workspace]`
settings such as `worktree-root`. `add` runs `git submodule add`, writes the
policy keys (`--policy` defaults to `pin`; `lazy` also sets `update = none`),
records `branch` from the child's `origin/HEAD`, and stages the child and
`.gitmodules`. Pass `--ref REV` to record a specific revision. It refuses name
or path collisions, a non-empty target, and unstaged `.gitmodules` edits.
For a pointer, `add` writes `.superproject`, clones (unless `--no-clone`;
an existing clone with the same origin is adopted), and gitignores a path
inside the root. Both refresh the **repo map** in the agents file (with many
repos, `workspace.map-file` keeps the full map elsewhere). Neither command
commits: review `git status`, then commit.

### 1. Look first

```bash
sp status --fetch   # policy, lag, drift, dirty, worktrees
sp audit            # findings + exact fix commands
```

Without `--fetch`, lag is computed against stale remote refs. Never report
"up to date" without fetching.

### 2. Get a child you need

```bash
sp init                 # all non-lazy, uninitialized submodule children
sp init some-reference  # a lazy child or a pointer clone, by name/path/basename
sp init --kind pointer  # every pointer clone
```

`init` never touches an already-initialized checkout and does not recurse
unless you pass `--recursive`. Initialization is not a way to update. For a
checkout it keeps, `init` reports `head`, `recorded` and `drift`. It refuses a
`broken` checkout (`.git` that no longer opens, for example after its store was
deleted) or a `foreign` one (files but no `.git`). It never runs `submodule
update` over them; `audit` reports them as `checkout-broken`, and
`references/repair.md` has the recovery steps.

### 3. Develop inside a child: use a child worktree

```bash
sp worktree add app feat/login
# -> .worktrees/app/feat-login  (gitignored; branch from origin/main for track,
#    from the recorded gitlink for pin, so fixes start from the baseline)
```

Work, commit, push, and open the PR **in the child's own repo and workflow**.
The submodule checkout itself stays on its branch or pin. Clean up with
`worktree list` (shows merged ones and their task; `--all` adds worktrees
outside the worktree root) and `worktree remove app feat/login --delete-branch`.
The worktree root is configurable (`.superproject` `worktree-root`, or
per clone `git config superproject.worktreeRoot`); see `references/worktrees.md`.

Open child worktrees **from the main checkout only**. `worktree add`, `task
open` and `add` refuse when the child's store belongs to a linked worktree of
the superproject, because removing that outer worktree would orphan them.

### 3b. One task across several children

```bash
sp task open login app lib      # .worktrees/_tasks/login/{app,lib}, branch login in both
sp task list login              # dirty / untracked / unpushed / merged per member
sp task close login --delete-branch
```

The task directory mirrors the superproject, so hand that one directory to
an editor or agent. `task open` checks every member before creating any, rolls
back its own worktrees if a creation fails, and can be rerun to add members.
`task close` refuses the whole task while any member has uncommitted or
untracked files (or, with `--delete-branch`, an unmerged branch) unless
`--force`. It removes worktrees with `git worktree remove` and only rmdirs
empty parents. Then `pull` and `bump <members> --commit` once.

### 4. Move pointers: inside-out, one outer commit

```bash
sp pull                 # ff track children (checkout only)
sp bump --all-track --commit
sp bump lib --reason "prod baseline v2.3" --commit   # pin/lazy
```

`bump` refuses the whole set if any child is dirty or its commit is not
pushed. For a `track` child, "pushed" means on `origin/<branch>`; for a pin, it
means on any origin branch. One cross-repo change gets one outer commit. The
commit body contains each range and the `--submodule=log` summary. Pass
`--partial` only when the user explicitly accepts splitting.

### 5. Guard every outer commit

```bash
sp preflight   # also installed as a pre-commit hook by adopt --with-hook
```

### 6. Adopt an existing superproject

```bash
uv run --script <skill>/scripts/superproject.py audit --root ../old-super
uv run --script <skill>/scripts/superproject.py adopt --root ../old-super --dry-run \
    --policy-default pin --set app=track:pr --set docs-ref=lazy
```

`adopt` writes policy keys, but only where they are missing or named by
`--set` (pointer children have no policy). It also upserts a marker-delimited
AGENTS.md guidance block and repo map, `sub-*` justfile recipes, adds the
worktree root to `.gitignore`, and, when submodule children exist, sets local
git config:
- `diff.submodule=log`
- `status.submoduleSummary=true`
- `push.recurseSubmodules=check`

Opt in to `--with-ci` and `--with-hook`. It does **not** copy the CLI. Pass
`--vendor-cli` only for offline or air-gapped superprojects, and accept that
the copy stops receiving fixes. It is idempotent: rerun it (`just sub-adopt`)
after a skill update to refresh the managed blocks. `audit` reports
`managed-block-stale`, `repo-map-stale` and `vendored-cli-stale` when the
tool itself has drifted. Review `git diff`
before committing, and pick policies with the user. The default
`--policy-default pin` is deliberately conservative.

### 7. Repair severed worktrees

```bash
sp audit                 # worktree-orphan, worktree-at-risk, stale config/stores, ...
sp repair --dry-run      # classify; each finding names the flag that handles it
sp repair                # lossless: relink worktrees whose store moved
sp repair --prune        # prune gone worktrees and stale submodule config
sp repair --reattach     # orphan -> branch rescue/<dir> in the child's store; files kept
sp repair --delete-orphans .worktrees/app/old   # explicit paths only
```

The typical cause is `fatal: not a git repository` inside `.worktrees/...` after
a superproject linked worktree was deleted. Unpushed commits made in an orphan
are gone with its store; its files are not. `repair` never deletes a
`.git/modules` store, force-removes dirty worktrees, or moves worktrees. Read
`references/repair.md` before deleting anything.

## Available scripts

- **`scripts/superproject.py`**: `new | add | status | init | pull | bump | preflight | worktree add|list|remove | task open|list|close | repair | audit | adopt | ci-plan`.
  - Common flags: `--root` (or `$SUPERPROJECT_ROOT`), `--json`, `--dry-run` (mutating commands).
  - Selection: positional names (name, path, or basename), `--tier`, `--policy`, `--kind`, `--mode`.
  - Exit codes: 0 ok, 1 refused or check failed, 2 usage error. Diagnostics go to stderr.

## Bundled assets

- `assets/justfile.snippet`: thin `sub-*` recipes (marker block; `adopt` upserts it).
- `assets/agents-block.md.template`: the cross-repo contract for agents in a superproject (marker block).
- `assets/agents-block-pointer.md.template`: the same for a home repo without submodules.
- `assets/superproject-bump.yml`: scheduled, `workflow_dispatch`, and `repository_dispatch` bump workflow (`pr` and `direct`).
- `assets/child-dispatch.yml`: optional; goes in a child repo to request an immediate bump on push to main.
- `assets/pre-commit-hook.sh`: runs `preflight`.

The recipes, hook, and workflow all use the same CLI resolution. CI pins
the version with the `SUPERPROJECT_CLI_REF` repository variable (a tag or
SHA).

## Reference files

- `references/decision-guide.md`: read when choosing between a monorepo, a submodule superproject, a pointer home repo, or Project add-dir.
- `references/home-repo.md`: read when working with pointer children (manifest, paths, clone on demand, repo map, `map-file`).
- `references/policies.md`: read when assigning policies, or for umbrella vs hub examples.
- `references/worktrees.md`: read before any branch work inside a child (worktree root, tasks, the guard, environments).
- `references/repair.md`: read when a child worktree says `fatal: not a git repository`, or `audit` reports orphans, at-risk worktrees, or stale stores.
- `references/ci-bump.md`: read when enabling `pr`/`direct` automation, private or GitLab children, or dispatch.
- `references/agent-entry.md`: read when setting up the superproject as an agent entry point (AGENTS.md layering, Claude/Codex Projects, root context).
- `references/gotchas.md`: read when git prints something surprising about a submodule.
- `references/case-patterns.md`: read when adopting; common umbrella, hub, and home-repo shapes and how they drift.

## Gotchas

- **Don't copy the CLI into each superproject.** Copies freeze at adoption
  time and silently diverge across repos. Reference the installed skill; vendor
  only for offline use, and let `audit` flag stale copies.
- **`git pull` in the superproject does not update children.** It moves gitlinks and leaves checkouts behind, which then shows as `modified: app (new commits)`. Run `status`, then decide whether to `bump` (keep the checkout) or `git submodule update -- app` (discard and go back to the gitlink).
- **`git submodule update` detaches HEAD** and can strand local commits that are not on a branch. `pull` refuses "detached commit not on origin/<branch>" for this reason; save the commit to a branch first.
- **"Latest" never means resetting pins.** A pinned child may legitimately be behind or sit on a release branch. `audit` reports this as info, not an error.
- **Never bump to an unpushed child commit.** A fresh clone would then fail with `fatal: remote error: upload-pack: not our ref`. `bump` and `preflight` block this, and `push.recurseSubmodules=check` blocks the outer push.
- **A submodule name is not its path.** One example is `[submodule "core"] path = libs/core-engine`. Policy keys use the *name*. The CLI accepts either.
- **CI PRs opened with `GITHUB_TOKEN` do not trigger other workflows.** Run the gates inside the bump job, or use a PAT or GitHub App token (`references/ci-bump.md`).
- **After a child's URL changes in `.gitmodules`**, existing clones keep the old URL until `git submodule sync`. `init` syncs, and `audit` flags `url-unsynced`.
- **A linked worktree of the superproject severs child worktrees.** Submodules initialized in it keep their stores under `.git/worktrees/<id>/modules/`; removing or pruning it deletes those stores and orphans every child worktree opened from them. Open child worktrees from the main checkout (the CLI refuses otherwise); `repair` handles the aftermath.
- **Don't run `claude --worktree` (or `isolation: worktree` subagents) at the superproject root for child work.** That creates exactly such an outer worktree. Use `worktree add` / `task open` instead.
- **Don't run `git clean -ffdx` at the root.** `-x` removes ignored paths such as `.worktrees/`, and the doubled `-f` removes nested repositories: every child worktree and its uncommitted work.
