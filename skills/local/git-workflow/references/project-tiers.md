# Project tiers — main vs dev vs PR

Read this when deciding whether to commit straight to `main`, introduce a
`dev` branch, or move to a PR-based flow — or when a project outgrows its
current tier. The goal is to match ceremony to real collaboration needs, not
to a project's ambitions.

## Table of contents

1. [The promotion signal](#the-promotion-signal)
2. [Tier 1 — solo / early](#tier-1--solo--early)
3. [Tier 2 — prod/dev split](#tier-2--proddev-split)
4. [Tier 3 — team / grown vibe-coding](#tier-3--team--grown-vibe-coding)
5. [GitHub Flow in one screen](#github-flow-in-one-screen)
6. [Choosing a merge strategy](#choosing-a-merge-strategy)

---

## The promotion signal

Don't adopt a heavier tier until the signal actually appears. Over-branching a
solo repo just adds friction; under-branching a shared repo causes collisions
and un-reviewable history.

| Move to | When |
|---|---|
| Tier 2 | someone (a deploy, a teammate, "prod") depends on a stable line while you keep working |
| Tier 3 | a second contributor appears, **or** you want a per-feature review/CI gate even solo |

You can also **skip** tiers: a solo vibe-coding project with heavy CI may go
straight to Tier 3, using PRs purely as a "ship a feature" boundary.

## Tier 1 — solo / early

One `main`. Commit directly; keep history linear.

```bash
git config pull.rebase true
git config merge.ff only

# work, commit in logical/phase-sized chunks
git add -p && git commit            # uses your commit.template

# stay current without merge commits
git pull --rebase

# optional short-lived branch, landed with no merge commit
git switch -c fix/typo
# ...commit...
git switch main && git merge --ff-only fix/typo && git branch -d fix/typo
```

Tag releases when a state is worth returning to (see
[`versioning-and-releases.md`](versioning-and-releases.md)).

## Tier 2 — prod/dev split

`main` = last released/deployed state; `dev` = integration line. Feature
branches cut from `dev`, land on `dev`, and `dev` fast-forwards to `main` at a
release boundary.

```bash
git switch dev && git pull --rebase
git switch -c feat/import-csv        # branch off dev
# ...commits...
git switch dev && git merge --ff-only feat/import-csv

# release: promote dev to main
git switch main && git merge --ff-only dev
git tag -a v0.4.0 -m "release: v0.4.0" && git push --follow-tags
```

Keep hotfixes on `main` and merge them back into `dev` so the lines don't
diverge. If `--ff-only` refuses (lines diverged), rebase `dev` onto `main`
first.

## Tier 3 — team / grown vibe-coding

`main` is always deployable. All work happens on short-lived branches that
merge via **pull request** after review + CI. This is
[GitHub Flow](https://docs.github.com/en/get-started/using-github/github-flow).

```bash
git switch main && git pull --rebase
git switch -c feat/oauth             # or agent/oauth for agent work
# ...commits...
git push -u origin feat/oauth
gh pr create --fill                  # glab mr create --fill
gh pr checks                         # wait for CI
gh pr merge --squash --delete-branch # collapse WIP into one clean commit
git switch main && git pull --rebase && git fetch --prune
```

The PR is the unit of "a feature shipped": it isolates finished work from
in-progress work, gives CI a place to run, and (even solo) creates a reviewable
diff and a revert point.

## GitHub Flow in one screen

1. `main` is always deployable.
2. Branch off `main` with a descriptive name.
3. Commit and push; open a PR early for visibility.
4. Discuss/review; let CI run.
5. Merge to `main` (squash or rebase).
6. Deploy from `main`; delete the branch.

## Choosing a merge strategy

| Strategy | History effect | Best for |
|---|---|---|
| `--ff-only` | linear, no merge commit | solo/local landing of a clean branch |
| **squash-merge** | one commit per PR on `main` | vibe-coding branches with noisy WIP |
| **rebase-merge** | each commit preserved, linear | branches where every commit is already meaningful |
| `--no-ff` merge | explicit merge commit | when you want the branch topology recorded |

Default here: `--ff-only` locally, **squash** for vibe-coding PRs, **rebase**
for curated PRs. Avoid default `--no-ff` merges unless the merge topology is
information you want to keep.
