# Case patterns from real superprojects

Two production superprojects informed this skill. Their lessons, with private
details removed:

## Umbrella: parallel platform repos, all following main

Five equally owned repos (one per OS or platform), unified by an outer repo
whose purpose is UX parity across them. No product is built in the outer repo.

What worked:
- **Inside-out commits** with a preflight that the inner HEAD is reachable
  from `origin/main` before the gitlink is staged. This is the origin of
  `bump`/`preflight`.
- **ff-only "pull main"** that refuses diverged branches and detached commits
  not on main. This is the origin of `pull`'s refusal list.
- **"One cross-repo change gets one outer commit"**, reviewed with
  `git diff --cached --submodule=log`.
- Deploy recipes pin the tool to a specific child checkout, never to an
  implicit default.

What drifted:
- No scheduled bump, so children ran 9+ commits ahead of the recorded pointer
  between maintenance sessions. Fix: `x-bump = pr`.
- Every child path was hard-coded into a dozen recipes, written twice (POSIX
  sh and PowerShell). Adding a sixth child meant editing all of them, and one
  pathspec still named a path that no longer existed. Fix: policy-driven
  recipes and one cross-platform CLI.

## Workspace hub: tiered children, pins, and root knowledge

About 20 children across GitHub and GitLab, org and personal, grouped
`core / personal / references`. The outer repo holds a structured context
graph (entities, relations, dated observations), runbooks, and agent history.

What worked:
- **Tiers with on-demand init**: references are fetched only when a task
  needs them, and never recursively. This is the origin of `lazy` + `update = none`.
- **"Latest is not reset-to-main"**: production diagnosis reads the deployed
  revision rather than upstream tip. This is the origin of `pin`.
- **Root context** that cites the revisions it observed.

What drifted:
- No rule for when a core pin moves forward, and no lag report. Some
  checkouts sat on feature branches, dirty, while their gitlinks pointed at
  commits on no origin branch at all. Fix: `status`, `audit`, explicit
  `pin`/`track`.
- External worktrees outside the entry point. Fix: `.worktrees/<child>/<branch>`.
- A bespoke init script (tiers and selection) that the policy keys plus `init --tier` now replace.

## Older, less agentic superprojects

These typically have `.gitmodules` and nothing else: no policy, no AGENTS.md,
and READMEs telling humans to run `git submodule update --remote`. Run `audit`,
then `adopt --dry-run --policy-default pin`, agree the policies with the
owner, then `adopt` and commit.
