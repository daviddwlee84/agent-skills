# Git workflow best practices

A concept-level explainer for the conventions the
[`git-workflow`](../skills/git-workflow.md) skill encodes. Read this for the
*why* — it's usable on its own as a primer, independent of the skill's scripts.
Everything here favors a **clean, linear, reviewable history** and habits that
scale from solo work to a team.

## Table of contents

1. [Commit messages: Conventional Commits](#commit-messages-conventional-commits)
2. [Semantic Versioning](#semantic-versioning)
3. [Choosing a workflow by project scale](#choosing-a-workflow-by-project-scale)
4. [Rebase, fast-forward, and squash](#rebase-fast-forward-and-squash)
5. [Branch naming](#branch-naming)
6. [Worktrees for parallel work](#worktrees-for-parallel-work)
7. [Forge CLIs: gh and glab](#forge-clis-gh-and-glab)
8. [Tag-driven versioning for packages](#tag-driven-versioning-for-packages)
9. [Sources](#sources)

---

## Commit messages: Conventional Commits

A commit message is documentation *and* an API for tooling. The
[Conventional Commits](https://www.conventionalcommits.org/en/v1.0.0/)
convention gives each commit a machine-readable prefix:

```
<type>(<optional scope>): <subject>
```

Common types: `feat`, `fix`, `docs`, `style`, `refactor`, `perf`, `test`,
`build`, `ci`, `chore`, `revert`. The subject is a short **imperative** phrase
("add retry", not "added retry"), lowercase, no trailing period, ideally ≤ 72
characters. A `!` (or a `BREAKING CHANGE:` footer) marks an incompatible change.

Why bother when working solo? Because the log becomes a changelog you can
generate, a version bump you can compute, and a history you can `git log
--grep 'feat'` months later. Write commits in **English** even when you think
and prompt in another language — the object graph is read by tools and future
collaborators.

## Semantic Versioning

[SemVer](https://semver.org/) numbers releases `MAJOR.MINOR.PATCH`:

- **MAJOR** — incompatible/breaking changes.
- **MINOR** — new, backward-compatible features.
- **PATCH** — backward-compatible bug fixes.

This maps cleanly onto Conventional Commits: `fix:` → PATCH, `feat:` → MINOR,
anything breaking → MAJOR. Below `1.0.0`, anything may change; `1.0.0` is the
promise of a stable public interface.

## Choosing a workflow by project scale

The biggest mistake is applying team ceremony to a solo repo (friction with no
benefit) or applying solo habits to a shared repo (collisions, un-reviewable
history). Match the workflow to real needs:

- **Tier 1 — solo / early.** One `main`. Commit directly, keep history linear
  with `git pull --rebase`, land the occasional short-lived branch with
  `git merge --ff-only`. No PRs. Tag when a state is worth returning to.
- **Tier 2 — prod/dev split.** `main` is the released/deployed line; `dev` is
  where features integrate. Promote `dev` → `main` at a release boundary. Adopt
  this when something (a deploy, a teammate) depends on a stable line while you
  keep working.
- **Tier 3 — team / grown vibe-coding.** `main` is always deployable; all work
  happens on short-lived branches merged via **pull request** after review and
  CI. This is [GitHub Flow](https://docs.github.com/en/get-started/using-github/github-flow).
  Even a solo project benefits: the PR is a "ship a feature" boundary, a CI
  trigger, and a revert point.

You can skip tiers — a solo project with heavy CI may start at Tier 3.

## Rebase, fast-forward, and squash

Three operations shape history:

- **`git pull --rebase`** replays your local commits *on top of* the fetched
  upstream instead of making a merge commit, keeping history linear. Set it as
  the default: `git config pull.rebase true`.
- **Fast-forward merge** (`git merge --ff-only`) moves the branch pointer
  forward with no merge commit — possible only when there's nothing to
  reconcile. `git config merge.ff only` makes git *refuse* a merge that would
  create a merge commit, which surfaces divergence instead of hiding it.
- **Squash merge** collapses a branch's commits into a single commit on the
  target. Ideal for "vibe-coding" branches full of work-in-progress noise: the
  mainline gets one clean `feat: …` commit. The trade-off is that the branch's
  individual commits don't appear on `main` — so the branch shows as `gone`
  rather than `merged` afterward (see [branch hygiene](#branch-naming)).

Rule of thumb: linear locally with fast-forward; squash noisy PRs; rebase-merge
PRs whose every commit already means something.

## Branch naming

A `<prefix>/<kebab-description>` convention makes branches sort by intent and
lets you clean them up in bulk:

- `feat/…`, `fix/…`, `chore/…`, `docs/…`, `refactor/…`, `exp/…` for
  human-authored work (optionally with an issue number: `feat/123-oauth`).
- `agent/…` as a distinct namespace for agent / vibe-coding branches, so
  machine-generated work is visually separate and separately disposable.
- `worktree-*` is what Claude Code auto-creates for worktrees.

Keeping these namespaces apart is what makes cleanup (`git branch --list
'agent/*'`) safe rather than nerve-wracking. After a PR merges, prune with
`git fetch --prune`; a branch whose upstream is `gone` (`git branch -vv`) is
usually done — but confirm it has no unpushed commits before deleting, because
work sometimes continues on a branch after its PR merged.

## Worktrees for parallel work

A [git worktree](https://git-scm.com/docs/git-worktree) is a second working
directory attached to the same repository, on its own branch. Running each
parallel agent or task in its own worktree means their file edits never
collide. Claude Code integrates this directly
([docs](https://code.claude.com/docs/en/worktrees)):

- `claude --worktree <name>` creates `.claude/worktrees/worktree-<name>/` on a
  new branch, based on `origin/HEAD` by default.
- A worktree is a *fresh* checkout, so gitignored files (like `.env`) aren't
  present. A `.worktreeinclude` file at the repo root copies them in — using
  `.gitignore` syntax, and copying **only files that are themselves
  gitignored**. Already-tracked files (a committed `.vscode/settings.json`) are
  in the checkout already and should not be listed.
- Add `.claude/worktrees/` to `.gitignore` so worktree contents don't show as
  untracked in the main checkout.

## Forge CLIs: gh and glab

Drive pull/merge requests from the terminal with the platform CLI —
[`gh`](https://cli.github.com/) for GitHub, [`glab`](https://gitlab.com/gitlab-org/cli)
for GitLab:

```bash
gh pr create --fill                     # glab mr create --fill
gh pr checks                            # watch CI
gh pr merge --squash --delete-branch    # glab mr merge --squash --remove-source-branch
```

They keep you out of the browser for the common path and make PR state
scriptable. Treat them as recommended conveniences, not hard dependencies — a
good workflow still functions with plain `git` if a CLI is missing.

## Tag-driven versioning for packages

When a repository *is* a package, don't maintain the version string in three
places (`__init__.py`, `pyproject.toml`, and a git tag) and let them drift.
Make the **git tag the single source of truth**. For Python, the
[Packaging guide](https://packaging.python.org/en/latest/discussions/single-source-version/)
recommends deriving the version from the VCS:

- **setuptools** backend → [setuptools-scm](https://setuptools-scm.readthedocs.io/).
- **Hatch / hatchling** backend → [hatch-vcs](https://pypi.org/project/hatch-vcs/).

Tag as `vX.Y.Z` (PEP 440-compatible once the `v` is stripped), push the tag,
and the build stamps the matching version. The release process becomes: land
the release commit → `git tag -a vX.Y.Z` → push the tag.

## Sources

- [Conventional Commits v1.0.0](https://www.conventionalcommits.org/en/v1.0.0/)
- [Semantic Versioning 2.0.0](https://semver.org/)
- [GitHub Flow](https://docs.github.com/en/get-started/using-github/github-flow)
- [Claude Code worktrees](https://code.claude.com/docs/en/worktrees)
- [git-worktree docs](https://git-scm.com/docs/git-worktree)
- [Python Packaging — single-sourcing the version](https://packaging.python.org/en/latest/discussions/single-source-version/)
- [setuptools-scm](https://setuptools-scm.readthedocs.io/) ·
  [hatch-vcs](https://pypi.org/project/hatch-vcs/)
