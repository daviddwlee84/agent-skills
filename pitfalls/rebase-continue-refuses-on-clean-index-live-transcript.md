# `git rebase --continue` refuses with "edit all merge conflicts" on a clean index while a transcript is live

## Symptom

Mid-rebase, after resolving and staging the only conflict,
`git rebase --continue` repeatedly prints:

```text
You must edit all merge conflicts and then
mark them as resolved using git add
```

Yet the index has no unmerged entries:

```text
$ git diff --name-only --diff-filter=U

$ git ls-files -u

$ git diff --cached --check
```

Re-staging and retrying changes nothing. `git status` may show the current
transcript as staged and modified again, for example:

```text
AM .specstory/history/2026-07-09_..-..Z-current-session.md
```

Related failures include checkout/switch refusing to overwrite local changes,
or pre-commit reporting that it changed files and then rolled those fixes back.

## Root cause

A tracked transcript in the operation is still being written by an external
recorder. Rebase is a multi-step checkout/apply/continue transaction. Between
`git add` and `git rebase --continue`, the recorder appends again, so Git sees a
moving working tree even though the conflict stages themselves are clean. The
"edit all merge conflicts" text describes the rebase stop, not the true moving
file.

A one-shot normal commit is **not** a safe escape while the writer is live.
Although Git snapshots an index once, pre-commit commonly hides unstaged bytes,
runs hooks, and restores them. A mutating hook can also rewrite a transcript.
Either path can restore older bytes over a newer SpecStory append. Commit and
rebase therefore share the same prerequisite: lifecycle quiescence.

Git's real in-progress state lives in operation directories and sequencer
state. A stale `.git/REBASE_HEAD` by itself can survive a completed operation
and must not be treated as an active rebase. Active rebase/cherry-pick sequence
state includes:

```text
rebase-merge
rebase-apply
sequencer
```

Other operations have their own authoritative markers, such as `MERGE_HEAD`,
`CHERRY_PICK_HEAD`, and `REVERT_HEAD`.

## Workaround

1. Stop retrying `git rebase --continue` or substituting a normal commit.
2. If a real rebase is active, preserve the working state and use the
   appropriate Git recovery action (usually abort back to the known pre-rebase
   tip if continuing cannot be made safe). Inspect the reflog before any
   destructive cleanup.
3. End the agent through its foreground recorder. Do not kill or bypass the
   lifecycle wrapper merely to make Git proceed.
4. After a normal recorder exit, let the runner perform the exact session sync.
5. Let the parent-authorized post-session finalizer stage/sanitize the exact
   transcript and plan and create the **feature-plus-history commit**.
6. Only after that commit is proven complete, start a fresh rebase or pull.

The intended order is:

```text
stage feature → queue finalization → exit recorder → exact sync
→ finalize and prove commit → rebase/pull/merge
```

Do not remove the live transcript from the feature commit or move it to a
separate archival commit merely to get rebase past the race; that breaks the
review-trail invariant. The lifecycle boundary makes the same commit safe.

If Git reports an operation in progress but only `REBASE_HEAD` remains, verify
that `rebase-merge`, `rebase-apply`, and `sequencer` are absent and that status
and reflog agree before removing stale residue. Never delete active operation
state to silence a guard.

## Prevention

Invariant: **both commit and rebase wait for transcript lifecycle quiescence.**
A live agent may stage feature paths and queue an inert request, but it does not
commit, rebase, switch, pull, or remove the worktree. The outer runner proves a
normal child exit and exact sync; the finalizer then performs the sole
sanctioned transcript mutation and one guarded commit.

After finalization, accept only a proven `committed` or `already_committed`
result before rebasing. If the commit outcome is uncertain, reconcile HEAD and
the private lifecycle journal; do not retry in LazyGit or with raw Git.

Keep pre-commit checks for agent artifacts validation-only, and exclude all
archival/install roots from generic mutators. This prevents checkout/restore
behavior inside the commit from recreating the same live-writer race.

Related:

- [Pre-commit restores over live SpecStory writes](pre-commit-restores-over-live-specstory-writes.md)
- [Formatter rewrites committed chat transcripts](formatter-rewrites-committed-agent-transcripts.md)
