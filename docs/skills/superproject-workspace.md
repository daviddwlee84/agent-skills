# superproject-workspace

Keep a **git-submodule superproject** usable as one agent entry point across
many repos, without letting it drift. Use it for an umbrella of parallel repos,
or for a workspace hub that mixes core, personal, and reference repos.

A gitlink records a commit, not a branch, so drift is the default: child PRs
merge and the pointer silently falls behind, checkouts end up detached or
dirty, and pointers reference commits nobody pushed. The skill makes drift
**visible** and moves pointers **by policy**.

| Surface | Question it answers |
|---|---|
| `scripts/superproject.py status` | "Which children are behind, drifted, dirty, or pointing at unpushed commits?" |
| `scripts/superproject.py pull` / `bump` | "How do I move pointers safely, all in one outer commit?" |
| `scripts/superproject.py worktree` | "Where do I put a feature branch for a child?" |
| `scripts/superproject.py audit` / `adopt` | "How do I bring an older superproject up to this standard?" |
| `assets/superproject-bump.yml` | "How do pointers keep up without me remembering?" |
| `references/decision-guide.md` | "Monorepo, submodules, manifest of clones, or Project add-dir?" |

## Policy lives in `.gitmodules`

```ini
[submodule "app"]
    path = app
    url = git@github.com:me/app.git
    branch = main
    x-policy = track     # track | pin | lazy
    x-bump = pr          # pr | direct | manual   (track only)
    x-tier = core
```

| Policy | Pointer moves | Initialized |
|---|---|---|
| `track` | ff-only `pull`, then `bump`; optionally automated by CI (`pr` or `direct`) | by default |
| `pin` | only `bump --reason` | by default |
| `lazy` (`update = none`) | only `bump --reason` | only when named |

## Core workflow

```bash
uv run --script scripts/superproject.py status --fetch
uv run --script scripts/superproject.py worktree add app feat/login   # .worktrees/app/feat-login
# ...commit + push + PR inside the child...
uv run --script scripts/superproject.py pull
uv run --script scripts/superproject.py bump --all-track --commit     # preflighted, one outer commit
```

To adopt an existing superproject, run
`audit`, then `adopt --dry-run --policy-default pin --set app=track:pr`. After
review, run `adopt`. It vendors the CLI and writes an AGENTS.md block, `sub-*`
justfile recipes, the `.worktrees/` ignore entry, local git config, and,
optionally, the CI workflow and pre-commit hook.

## See also

- [Source](https://github.com/daviddwlee84/agent-skills/tree/main/skills/local/superproject-workspace)
- [`git-workflow`](git-workflow.md): single-repo commits, branches, and worktrees.
- [`forge-native-dev`](https://github.com/daviddwlee84/agent-skills/tree/main/skills/local/forge-native-dev): issue and PR lifecycle inside each child.
