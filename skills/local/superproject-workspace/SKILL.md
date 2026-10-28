---
name: superproject-workspace
description: Keep a git-submodule superproject (umbrella repo / multi-repo workspace used as one agent entry point) from drifting — per-submodule policy in .gitmodules (track / pin / lazy), lag and drift status, safe fast-forward, preflighted gitlink bumps in one outer commit, scheduled bump PRs, child worktrees, and audit/adopt for existing superprojects. Use when a repo has .gitmodules and the user asks to update/sync submodules, bump pointers, work on a branch inside a submodule, add a repo to the workspace, or asks "monorepo vs submodules", incl. "submodule 落後 / 更新 submodule / 拉到 latest main".
---

# superproject-workspace

A superproject is a repo whose job is to hold other repos as git submodules,
so that one agent session gets every repo's context and edit access while each
repo keeps its own remote, PRs, and release cycle. The cost: **a gitlink
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
- Adding a repo to a workspace, or deciding *how* to bring repos together (see `references/decision-guide.md`).
- Auditing or upgrading an older superproject that has ad-hoc recipes.

## When NOT to use

- Ordinary single-repo git work: use `git-workflow`.
- Issue/PR lifecycle inside one child: use that child's own workflow (`forge-native-dev`, etc.).
- The repos are not submodules (manifest + gitignored clones, or Project add-dir): only the decision guide applies.

## The policy model

Each child declares its policy as extra keys in `.gitmodules`. Git ignores keys
it does not know, so these keys live next to `path` and `url` and cannot fall
out of sync with them.

```ini
[submodule "app"]
    path = app
    url = git@github.com:me/app.git
    branch = main        # tracking branch (native key; unset -> child's origin/HEAD)
    x-policy = track     # track | pin | lazy
    x-bump = pr          # pr | direct | manual   (only for track)
    x-tier = core        # free-form grouping for --tier selection
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

### 1. Look first

```bash
sp status --fetch   # policy, lag, drift, dirty, worktrees
sp audit            # findings + exact fix commands
```

Without `--fetch`, lag is computed against stale remote refs. Never report
"up to date" without fetching.

### 2. Get a child you need

```bash
sp init                 # all non-lazy, uninitialized children
sp init some-reference  # a lazy child, by name/path/basename
```

`init` never touches an already-initialized checkout and does not recurse
unless you pass `--recursive`. Initialization is not a way to update.

### 3. Develop inside a child: use a child worktree

```bash
sp worktree add app feat/login
# -> .worktrees/app/feat-login  (gitignored; branch from origin/main for track,
#    from the recorded gitlink for pin, so fixes start from the baseline)
```

Work, commit, push, and open the PR **in the child's own repo and workflow**.
The submodule checkout itself stays on its branch or pin. Clean up with
`worktree list` (shows merged ones) and `worktree remove app feat/login --delete-branch`.
Do not create worktrees of the superproject for this; see `references/worktrees.md`.

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
`--set`. It also upserts a marker-delimited AGENTS.md block and `sub-*`
justfile recipes, adds `.worktrees/` to `.gitignore`, and sets local git
config:
- `diff.submodule=log`
- `status.submoduleSummary=true`
- `push.recurseSubmodules=check`

Opt in to `--with-ci` and `--with-hook`. It does **not** copy the CLI. Pass
`--vendor-cli` only for offline or air-gapped superprojects, and accept that
the copy stops receiving fixes. It is idempotent: rerun it (`just sub-adopt`)
after a skill update to refresh the managed blocks. `audit` reports
`managed-block-stale` and `vendored-cli-stale` when the tool itself has
drifted. Review `git diff`
before committing, and pick policies with the user. The default
`--policy-default pin` is deliberately conservative.

## Available scripts

- **`scripts/superproject.py`**: `status | init | pull | bump | preflight | worktree add|list|remove | audit | adopt | ci-plan`.
  - Common flags: `--root`, `--json`, `--dry-run` (mutating commands).
  - Selection: positional names (name, path, or basename), `--tier`, `--policy`, `--mode`.
  - Exit codes: 0 ok, 1 refused or check failed, 2 usage error. Diagnostics go to stderr.

## Bundled assets

- `assets/justfile.snippet`: thin `sub-*` recipes (marker block; `adopt` upserts it).
- `assets/agents-block.md.template`: the cross-repo contract for agents (marker block).
- `assets/superproject-bump.yml`: scheduled, `workflow_dispatch`, and `repository_dispatch` bump workflow (`pr` and `direct`).
- `assets/child-dispatch.yml`: optional; goes in a child repo to request an immediate bump on push to main.
- `assets/pre-commit-hook.sh`: runs `preflight`.

The recipes, hook, and workflow all use the same CLI resolution. CI pins
the version with the `SUPERPROJECT_CLI_REF` repository variable (a tag or
SHA).

## Reference files

- `references/decision-guide.md`: read when choosing between a real monorepo, a submodule superproject, a manifest with clones, or Project add-dir.
- `references/policies.md`: read when assigning policies, or for umbrella vs hub examples.
- `references/worktrees.md`: read before any branch work inside a child.
- `references/ci-bump.md`: read when enabling `pr`/`direct` automation, private or GitLab children, or dispatch.
- `references/agent-entry.md`: read when setting up the superproject as an agent entry point (AGENTS.md layering, Claude/Codex Projects, root context).
- `references/gotchas.md`: read when git prints something surprising about a submodule.
- `references/case-patterns.md`: read when adopting; lists lessons from real umbrella and hub superprojects.

## Gotchas

- **Don't copy the CLI into each superproject.** Copies freeze at adoption
  time and silently diverge across repos. Reference the installed skill; vendor
  only for offline use, and let `audit` flag stale copies.
- **`git pull` in the superproject does not update children.** It moves gitlinks and leaves checkouts behind, which then shows as `modified: app (new commits)`. Run `status`, then decide whether to `bump` (keep the checkout) or `git submodule update -- app` (discard and go back to the gitlink).
- **`git submodule update` detaches HEAD** and can strand local commits that are not on a branch. `pull` refuses "detached commit not on origin/<branch>" for this reason; save the commit to a branch first.
- **"Latest" never means resetting pins.** A pinned child may legitimately be behind or sit on a release branch. `audit` reports this as info, not an error.
- **Never bump to an unpushed child commit.** A fresh clone would then fail with `fatal: remote error: upload-pack: not our ref`. `bump` and `preflight` block this, and `push.recurseSubmodules=check` blocks the outer push.
- **A submodule name is not its path.** One example is `[submodule "dotfiles"] path = dotfiles-unix`. Policy keys use the *name*. The CLI accepts either.
- **CI PRs opened with `GITHUB_TOKEN` do not trigger other workflows.** Run the gates inside the bump job, or use a PAT or GitHub App token (`references/ci-bump.md`).
- **After a child's URL changes in `.gitmodules`**, existing clones keep the old URL until `git submodule sync`. `init` syncs, and `audit` flags `url-unsynced`.
