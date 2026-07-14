# Branch hygiene

Read this when your local branches are confusing — a PR merged but the branch
lingers, you can't tell which branches are done vs still in-dev, or work
continued on a branch after its PR merged. Pairs with
`scripts/branch-status.sh`, which reports the same states as data.

## Table of contents

1. [The four states](#the-four-states)
2. [Prune first](#prune-first)
3. [Detecting each state](#detecting-each-state)
4. [The squash-merge trap](#the-squash-merge-trap)
5. [Safe deletion](#safe-deletion)
6. [Reconciling against remote PRs](#reconciling-against-remote-prs)
7. [Using branch-status.sh](#using-branch-statussh)

---

## The four states

| State | Meaning | Typical action |
|---|---|---|
| `active` | ahead of base, upstream still exists | keep working |
| `merged` | fully contained in the base branch | delete with `-d` |
| `gone` | upstream branch was deleted (e.g. PR squash-merged) | delete with `-D` after confirming |
| `stale` | no commits for N days | review; likely abandoned |

## Prune first

Local remote-tracking refs go out of date. Refresh before judging anything:

```bash
git fetch --prune          # drop origin/* refs whose remote branch is gone
```

Configure it permanently: `git config remote.origin.prune true` (or global
`fetch.prune true`).

## Detecting each state

```bash
# branches fully merged into the current branch (safe to delete)
git branch --merged

# branches NOT yet merged
git branch --no-merged

# upstream tracking + ahead/behind; deleted upstream shows ": gone]"
git branch -vv
#   feat/x  1a2b3c [origin/feat/x: ahead 2] ...      → active
#   agent/y 4d5e6f [origin/agent/y: gone] ...        → gone (PR merged, branch deleted)

# last-commit date per branch (spot stale ones)
git for-each-ref --sort=-committerdate refs/heads/ \
  --format='%(committerdate:short) %(refname:short)'
```

## The squash-merge trap

A **squash-merge** replays a branch's changes as one *new* commit on `main`.
The branch's original commits never appear on `main`, so `git branch --merged`
does **not** list it — it looks unmerged even though it's shipped. The reliable
signal is the deleted upstream (`: gone]`). This is why `branch-status.sh`
treats `gone` as "probably done" rather than relying only on `--merged`.

## Safe deletion

- `git branch -d <name>` — refuses unless the branch is merged into its
  upstream or the current branch. Use for `merged` state.
- `git branch -D <name>` — force delete. Needed for `gone` (squash-merged)
  branches. **Before forcing, confirm there are no unpushed commits you still
  want** — a branch can be `gone` upstream yet carry local work.

```bash
# check for commits not on main before force-deleting a gone branch
git log --oneline main..agent/y
```

## Reconciling against remote PRs

When a remote PR/MR is the source of truth, ask the forge directly (optional —
requires `gh`/`glab`, authenticated):

```bash
gh pr status                       # PRs for the current branch + yours
gh pr list --state merged --limit 50
glab mr list --state merged        # GitLab
```

Cross-reference merged PR head branches against your local branch list to find
"merged remotely, still local" leftovers.

## Using branch-status.sh

```bash
bash skills/local/git-workflow/scripts/branch-status.sh              # TSV
bash skills/local/git-workflow/scripts/branch-status.sh --json       # for tooling
bash skills/local/git-workflow/scripts/branch-status.sh --stale-days 14
```

It runs `git fetch --prune` implications in mind (run `fetch --prune` first for
freshest results), classifies each local branch, and — if `gh`/`glab` is
available on a matching remote — enriches `merged`/`gone` with PR state. It
never deletes anything; it only reports, so you decide `-d` vs `-D`.
