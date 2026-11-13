# Worktrees in a superproject

## Rule

Feature work in a child happens in a **worktree of the child**, opened from
the superproject's **main checkout**. The submodule checkout itself stays on
its tracked branch, or at its pin.

```bash
sp worktree add <child> <branch> [--base REV]   # one child
sp task open <task> <child>... [--base CHILD=REV] # one task, several children
sp worktree list [--all]
sp worktree remove <child> <branch> --delete-branch
sp task list [<task>]
sp task close <task> [--delete-branch]
```

## Layout and the worktree root

Everything lives under one **worktree root** `R`:

| Kind | Path |
|---|---|
| Single child | `R/<child-path>/<branch-slug>` |
| Task | `R/_tasks/<task-slug>/<child-path>` |

`_tasks` is reserved; `add` refuses a child path that starts with it.

`R` defaults to `.worktrees` inside the superproject (gitignored). Override it,
first match wins:

1. `git config --local superproject.worktreeRoot <path>`: per clone, not versioned.
2. `.superproject` `[workspace] worktree-root = <path>`: shared by everyone.
3. `.worktrees`

Paths may be relative to the root, absolute, or start with `~`.

| `R` | Gain | Cost |
|---|---|---|
| Inside the root (default) | An agent started at the root sees worktrees, AGENTS.md and siblings | Must be gitignored (`worktree add`, `task open` and `adopt` do it); tools that index the whole tree see the copies |
| Outside the root | Keeps the superproject tree small; fits tools that forbid worktrees inside checkouts | The agent needs add-dir to see them; `audit` reports `worktree-outside-root` (info) |

The CLI finds the root again from inside an outside worktree, through the
child's store location (`<root>/.git/modules/...`).

## Tasks: one change across several children

`task open login app lib` creates `R/_tasks/login/app` and `R/_tasks/login/lib`
on branch `login` (override with `--branch`). The task directory mirrors the
superproject, so relative paths between members still resolve, and you can
hand the single directory to an editor or agent.

- It checks every member first (initialized, durable store, target free,
  branch not checked out elsewhere) and changes nothing if any fails. If a
  creation still fails, it removes the worktrees and branches **this call**
  created and exits 1.
- It is idempotent: rerun it with more children to extend the task; existing
  members report `exists`.
- There is no state file. Membership comes from each child's
  `git worktree list`: a worktree under `R/_tasks/<t>/` belongs to task `t`.
- `task list` shows `dirty`, `untracked`, `unpushed` (commits on no `origin/*`
  ref), `merged` (into `origin/<branch>`), `stray_dirs`, and `ready_to_close`.
- `task close` refuses the whole task when any member has modified or
  untracked files, or, with `--delete-branch`, an unmerged branch. `--force`
  overrides. It uses `git worktree remove` per member and removes only empty
  parent directories. Then `pull` and `bump <members> --commit` once.

`worktree list` has a TASK column; `--all` adds worktrees outside `R`.

## The guard: never from a superproject worktree

`worktree add`, `task open` and `add` refuse when the child's git store
belongs to a **linked worktree of the superproject** (`git worktree add` of the
outer repo, `claude --worktree` at the root, `isolation: worktree` subagents).
Submodules initialized there keep their store under
`<main>/.git/worktrees/<id>/modules/`. When that outer worktree is removed or
pruned, the store goes with it, and every child worktree registered in it is
orphaned (`fatal: not a git repository`). The refusal names the main checkout;
rerun there. There is no override. `audit` reports existing ones as
`worktree-at-risk`; see `repair.md`.

The same applies to other worktree managers: if a tool created a full
worktree of the superproject, do not open child worktrees from inside it.
Either work directly on child branches in that outer worktree, or use the
child and task worktrees from the main checkout, not both for one task.

## Why not the alternatives

| Approach | Problem |
|---|---|
| Switch branches in the submodule checkout | Only one branch at a time. The gitlink shows dirty while you work. `pull` and `bump` then operate on your feature branch. Parallel agents collide. |
| `git worktree add` of the **superproject** | Submodules start uninitialized: each worktree needs a full `submodule update --init`, which is slow and multiplies clones. Child worktrees opened from it die with it (see the guard). Git's support for submodules in multiple superproject worktrees is still marked experimental. |

## Base revision

- `track` children branch from `origin/<branch>`.
- `pin` and `lazy` children branch from the **recorded gitlink**: a fix to a
  pinned production baseline should start from that baseline, not from
  upstream main.
- An existing local or remote branch of the same name is checked out instead
  of a new one being created.
- Override with `--base` (`--base CHILD=REV` for `task open`).

## Environments

The CLI does not manage environments; these are the rules that keep them sane.

- An environment (virtualenv, `node_modules`, build directory, running dev
  server) is bound to the path it was created in.
- The environment at the root serves the checkouts at their pinned or tracked
  revisions. Do not point it at a worktree.
- Each worktree or task directory builds its own environment inside itself
  (for example `uv sync` or `npm install` in the member). Gitignore it there.
- Do not override `PYTHONPATH` (or similar) to make the root environment
  import a worktree's code: it mixes revisions silently.
- Services that several members share (a database, a local registry) belong
  to the task, not to one member; start them from the task directory.

## Coexistence with superproject issue worktrees

`forge-native-dev` places superproject issue worktrees at `.worktrees/issue-<n>`.
Child worktrees are nested under the child's path (`.worktrees/app/...`) or
under `_tasks/`, so they never collide. A superproject issue worktree is
fine for changes that touch **only** outer content (docs, context, CI); do not
open child worktrees from inside it.
