# Common outer-repo patterns

Most multi-repo workspaces fall into one of these shapes. Each lists what
tends to work, what tends to drift, and which part of this skill addresses it.

## Umbrella: parallel repos that all follow main

Several equally owned repos (for example one per platform or per service)
under an outer repo whose purpose is consistency across them. Nothing is built
in the outer repo itself.

What works:
- **Inside-out commits**: a child commit reaches `origin/main` before its
  gitlink is staged. This is what `bump` and `preflight` enforce.
- **Fast-forward-only updates** that refuse diverged branches and detached
  commits not on main: `pull`'s refusal list.
- **One cross-repo change, one outer commit**, reviewed with
  `git diff --cached --submodule=log`.

What drifts:
- Without a scheduled bump, children run many commits ahead of the recorded
  pointer between maintenance sessions. Fix: `x-bump = pr`.
- Child paths hard-coded into many recipes (often twice, for two shells).
  Adding a child means editing all of them, and stale paths linger. Fix:
  policy-driven recipes (`adopt`) and one cross-platform CLI.

## Workspace hub: tiered children, pins, and root knowledge

Many children across forges and owners, grouped into tiers such as `core` and
`reference`. The outer repo holds context that spans them: a context graph,
runbooks, agent history.

What works:
- **Tiers with on-demand init**: reference material is fetched only when a
  task needs it, never recursively (`lazy` + `update = none`, `init --tier`).
- **"Latest" is not "reset to main"**: diagnosing production reads the
  deployed revision, not upstream tip (`pin`).
- **Root context that cites the revision it observed.**

What drifts:
- No rule for when a pin moves, and no lag report. Checkouts end up on
  feature branches, dirty, with gitlinks on no origin branch. Fix: `status`,
  `audit`, explicit `pin`/`track`.
- Worktrees scattered outside the entry point, or opened from a worktree of
  the outer repo (orphaned when it is removed). Fix: worktree root, `task`,
  the guard, `repair`.
- A bespoke init script for tiers and selection. Fix: policy keys + `init --tier`.

## Home repo over existing clones

Context and instructions in one repo; the code repos already exist elsewhere
on disk, or there are too many to pin. Fix: pointer children (`add --pointer`),
clone on demand, and a repo map with `map-file` when the list is long. See
`home-repo.md`.

## Older, less agentic superprojects

These typically have `.gitmodules` and nothing else: no policy, no AGENTS.md,
and READMEs telling humans to run `git submodule update --remote`. Run
`audit`, then `adopt --dry-run --policy-default pin`, agree the policies with
the owner, then `adopt` and commit.
