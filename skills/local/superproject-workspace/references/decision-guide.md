# Decision guide: how to bring repos together for an agent

**Prefer a submodule superproject when it is feasible.** The outer commit pins
every child, so "this set worked together" is reproducible, outer notes can
cite exact child versions, and `bump`/`preflight` keep pointers honest. Use a
pointer-only home repo only when submodules do not fit.

Goal: one agent entry point with context (and usually edit access) across
several repos, without coupling their histories, CI, or release cycles more
than necessary.

## Submodule superproject or pointer home repo

| Choose a **submodule superproject** when | Choose a **pointer home repo** when |
|---|---|
| You need to reproduce a combination of versions later ("what did prod run", "the state that passed parity checks") | The outer history cannot or should not contain gitlinks (policy, tooling, or audience) |
| Outer content refers to child versions (runbooks, context notes, deployment docs) | The children already live elsewhere on disk and must stay there |
| CI spans children (parity checks, integration tests, scheduled bumps) | There are dozens of rarely touched repositories |
| | Collaborators or tools cannot handle submodules |
| | Nobody will bump: an unmaintained pin is worse than no pin |

What pointer mode gives up:

- **No snapshot.** The outer commit says nothing about child versions; notes
  must carry their own commit or date.
- **No `bump`, `preflight`, or `ci-plan`.** There is no gitlink to move,
  verify, or automate. `status` measures lag against `origin/<branch>` only.
- **Less shared layout.** Clones outside the root (`../x`, `~/x`) depend on
  each collaborator's disk layout.

It keeps: status, clone on demand, `pull`, child and task worktrees, `repair`,
`audit`, the agent block and repo map. Both kinds can coexist in one root, so
a superproject can point at a few reference repos without pinning them. See
`home-repo.md`.

## All options

| Option | What it is | Version snapshot of the set? | Drift problem | Best when |
|---|---|---|---|---|
| **Real monorepo** | One repo, one history | Yes (every commit) | None | Repos ship together, share CI and owners, and change atomically |
| **Submodule superproject** (this skill, preferred) | Outer repo pins each child by gitlink | Yes (outer commit = exact set) | Yes, so manage it by policy | Repos are independent but you need reproducible combinations, or the outer repo carries shared knowledge |
| **Pointer home repo** (this skill, fallback) | `.superproject` lists repos; plain clones, cloned on demand | No | None: each clone is whatever is checked out | Context breadth matters, version sets do not (see the table above) |
| **Other manifest + clone tools** (`mani`, `gita`, `repo`, `meta`, a script) | A manifest plus a clone/update script | No (unless you record SHAs yourself) | None | You already use one; this skill's pointer mode is the same idea with worktrees and audit |
| **Project / add-dir** (Claude Code `--add-dir`, Codex or Claude Projects) | Agent session spans several existing checkouts | No | None | Ad-hoc, personal, short-lived cross-repo tasks |

## Questions that decide it

1. **Do you need to reproduce a combination later?** If yes, choose
   submodules, or a monorepo if the repos are tightly coupled.
2. **Does the outer repo have content of its own?** Examples: AGENTS.md, a
   cross-repo context graph, `pitfalls/`, session history, runbooks. Both
   kinds give it a versioned home; only submodules date each note against
   concrete child versions.
3. **Do children have different owners, visibility, or forges?** Then rule
   out a monorepo; submodules or pointers both work.
4. **Will you remember to bump?** If not, automate it (`x-bump = pr` or
   `direct`) or choose pointers. A superproject with no bumping pins by
   accident.

## Hybrid that works well

Use submodules for the **core** set (`track` or `pin`) and mark reference
material `lazy`, so a fresh clone stays small. Reference repos that should
never be pinned can be pointers in the same root. Truly throwaway reads don't
need either: use add-dir.
