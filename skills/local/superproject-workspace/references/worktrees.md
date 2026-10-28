# Worktrees in a superproject

## Rule

Feature work in a child happens in a **worktree of the child**, placed inside
the superproject at `.worktrees/<child-path>/<branch-slug>` (gitignored):

```bash
uv run --script scripts/superproject.py worktree add <child> <branch> [--base REV]
uv run --script scripts/superproject.py worktree list
uv run --script scripts/superproject.py worktree remove <child> <branch> --delete-branch
```

The submodule checkout itself stays on its tracked branch, or at its pin.

## Why not the alternatives

| Approach | Problem |
|---|---|
| Switch branches in the submodule checkout | Only one branch at a time. The gitlink shows dirty while you work. `pull` and `bump` then operate on your feature branch. Parallel agents collide. |
| `git worktree add` of the **superproject** | Submodules in a new superproject worktree start **uninitialized**: each worktree needs a full `submodule update --init`, which is slow and multiplies clones. Git's support for submodules inside multiple superproject worktrees is still marked experimental. |
| Worktree outside the superproject (`~/worktrees/...`) | Works, but leaves the agent's entry point. Context such as AGENTS.md, `context/`, and sibling repos is not under the session root, and the agent needs add-dir. Use it only when a task must be isolated from the superproject. |

## Base revision

- `track` children branch from `origin/<branch>`.
- `pin` and `lazy` children branch from the **recorded gitlink**: a fix to a
  pinned production baseline should start from that baseline, not from
  upstream main.
- An existing local or remote branch of the same name is checked out instead
  of a new one being created.
- Override with `--base`.

## Coexistence with superproject issue worktrees

`forge-native-dev` places superproject issue worktrees at `.worktrees/issue-<n>`.
Child worktrees are nested under the child's path (`.worktrees/app/...`), so
the two never collide. Superproject issue worktrees remain fine for changes
that touch **only** outer content (docs, context, CI).
