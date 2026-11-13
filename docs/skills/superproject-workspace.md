# superproject-workspace

Set up and keep a **multi-repo workspace** usable as one agent entry point,
without letting it drift. Two modes:

- a **git-submodule superproject** (recommended): the outer commit pins every
  child, so a working combination is reproducible;
- a **pointer-only home repo** (fallback): a manifest of plain clones, cloned
  on demand, for when submodules do not fit.

A gitlink records a commit, not a branch, so drift is the default: child PRs
merge and the pointer silently falls behind, checkouts end up detached or
dirty, and pointers reference commits nobody pushed. The skill makes drift
**visible** and moves pointers **by policy**.

| Surface | Question it answers |
|---|---|
| `scripts/superproject.py new` / `add` | "How do I start a superproject or home repo, and add a repo to it?" |
| `scripts/superproject.py status` | "Which children are behind, drifted, dirty, or pointing at unpushed commits?" |
| `scripts/superproject.py pull` / `bump` | "How do I move pointers safely, all in one outer commit?" |
| `scripts/superproject.py worktree` / `task` | "Where do I put a feature branch, for one child or across several?" |
| `scripts/superproject.py repair` | "A child worktree says `fatal: not a git repository`. Now what?" |
| `scripts/superproject.py audit` / `adopt` | "How do I bring an older setup up to this standard?" |
| `assets/superproject-bump.yml` | "How do pointers keep up without me remembering?" |
| `references/decision-guide.md` | "Monorepo, submodules, pointer home repo, or Project add-dir?" |

## Policy lives in `.gitmodules`

```ini
[submodule "app"]
    path = app
    url = https://example.com/org/app.git
    branch = main
    x-policy = track     # track | pin | lazy
    x-bump = pr          # pr | direct | manual   (track only)
    x-tier = core
    x-role = Web client  # shown in the generated repo map
```

| Policy | Pointer moves | Initialized |
|---|---|---|
| `track` | ff-only `pull`, then `bump`; optionally automated by CI (`pr` or `direct`) | by default |
| `pin` | only `bump --reason` | by default |
| `lazy` (`update = none`) | only `bump --reason` | only when named |

Pointer children live in `.superproject` as `[repo "<name>"]` sections
(`path`, `url`, `branch`, `x-tier`, `x-role`). They have no policy and no
gitlink: `bump`, `preflight` and `ci-plan` refuse them.

## Core workflow

```bash
sp new my-workspace && cd my-workspace
sp add https://example.com/org/app.git --policy track --bump pr
sp status --fetch
sp task open login app lib       # .worktrees/_tasks/login/{app,lib}, one branch
# ...commit + push + PR inside each child...
sp task close login --delete-branch
sp pull
sp bump --all-track --commit     # preflighted, one outer commit
```

Child worktrees are opened from the **main checkout** only. A worktree of the
superproject (including `claude --worktree` at the root) keeps its submodule
stores inside itself, and removing it orphans every child worktree opened
from them; the CLI refuses that layout, and `repair` reattaches orphans.

To adopt an existing superproject, run `audit`, then
`adopt --dry-run --policy-default pin --set app=track:pr`. After review, run
`adopt`. It writes an AGENTS.md block and repo map, `sub-*` justfile recipes,
the worktree-root ignore entry, local git config, and, optionally, the CI
workflow and pre-commit hook.

The CLI is **referenced, not copied**: recipes resolve the installed skill
(`~/.agents/skills/superproject-workspace`) and fall back to GitHub raw at
`$SUPERPROJECT_CLI_REF`. One `npx skills update` upgrades every superproject.
Rerun `adopt` to refresh the managed blocks; `audit` flags them when stale.

(`sp` = `uv run --script ~/.agents/skills/superproject-workspace/scripts/superproject.py`, or the `just sub-*` recipes.)

## See also

- [Source](https://github.com/daviddwlee84/agent-skills/tree/main/skills/local/superproject-workspace)
- [`git-workflow`](git-workflow.md): single-repo commits, branches, and worktrees.
- [`forge-native-dev`](https://github.com/daviddwlee84/agent-skills/tree/main/skills/local/forge-native-dev): issue and PR lifecycle inside each child.
