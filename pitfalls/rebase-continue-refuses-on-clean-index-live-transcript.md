# `git rebase --continue` refuses with "edit all merge conflicts" on a clean index (a tracked file is being live-written)

## Symptom

Mid-rebase, after resolving the only conflict and `git add`-ing it,
`git rebase --continue` refuses to proceed and keeps printing:

```
You must edit all merge conflicts and then
mark them as resolved using git add
```

…even though the index is provably clean:

```
$ git diff --name-only --diff-filter=U   # unmerged paths
(empty)
$ git ls-files -u                         # unmerged index entries (stages 1/2/3)
(empty)
$ git diff --cached --check               # leftover conflict markers
(none)
```

Re-staging (`git add -A`) and retrying makes no difference. `git status`
shows one file in the `AM` state (staged-add **and** working-tree-modified),
e.g. `AM .specstory/history/2026-07-09_..-..Z-<current-session>.md`.

## Root cause

A **tracked file that an external process is continuously rewriting** is part
of the commit being rebased. In an agent session that file is the **live chat
transcript** the harness appends to on every action (Claude Code / SpecStory
writes `.specstory/history/<current-session>.md`; Cursor/others similar). It
had been committed into the branch being rebased.

A rebase is a multi-step operation (apply → stop at conflict → resolve →
continue). Between the `git add` and the `git rebase --continue`, the harness
writes the transcript again, so the tracked file changes underneath git and
its mid-rebase safety checks trip. The "resolve conflicts" message is
misleading — there is no conflict; git is reacting to the moving tracked file
in the shared working directory. The same churn also blocks `git switch`
("Your local changes to the following files would be overwritten by checkout").

## Workaround

Do not put the running session's live transcript in a commit you intend to
rebase or cherry-pick. Concretely:

- **Prefer a single `git commit` over a rebase.** A one-shot commit snapshots
  the index once, so continuous writes to a tracked file don't matter. When
  the branch has diverged from `main`, land the change by staging it on `main`
  and committing directly (or `git commit -C <branch-commit>` to reuse the
  message) instead of rebase-then-ff.
- If you must rebase, **exclude the live transcript** from the commit first
  (`git rm --cached .specstory/history/<current-session>.md`), rebase, then
  add transcripts back in a separate commit.
- `git rebase --abort` is always the safe exit — it restores the pre-rebase
  branch tip and re-applies any autostash; nothing is lost (check `git reflog`).

## Prevention

Commit chat transcripts (`.specstory/history/*.md`, `.claude/plans/*.md`) as
their **own commit, ideally at session end** when the current transcript has
stopped changing — never bundle the *active* session's transcript into a
feature commit you then rebase. This is a corollary of the
[`agent-history-hygiene`](../skills/local/agent-history-hygiene/SKILL.md) skill:
stage agent artifacts separately from the feature diff. If two agents/terminals
share one working directory, treat concurrent `git` operations as unsafe — they
mutate the same `.git` and can corrupt rebase/merge state (`git reflog` will
show `commit (amend)` / `pull --rebase` entries you didn't run).
