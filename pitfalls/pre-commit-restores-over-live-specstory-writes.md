# Pre-commit reports "Rolling back fixes" and restores over live SpecStory writes

**Symptoms** (grep this section): `- files were modified by this hook` ·
`Stashed changes conflicted with hook auto-fixes... Rolling back fixes...` ·
`Restored changes from` · a `.specstory/history/*.md` append disappears or
returns after a failed commit
**First seen**: 2026-09
**Affects**: pre-commit commits with unstaged changes, a mutating hook, and an
active SpecStory transcript writer
**Status**: prevention invariant documented; do not retry while the writer is
live

## Symptom

A commit involving the current SpecStory transcript emits representative
pre-commit output like this:

```text
trim trailing whitespace.................................................Failed
- hook id: trailing-whitespace
- exit code: 1
- files were modified by this hook

[WARNING] Stashed changes conflicted with hook auto-fixes... Rolling back fixes...
[INFO] Restored changes from /home/user/.cache/pre-commit/patch0000000000-000000.
```

The patch path varies by machine. The significant upstream strings are
verbatim:

```text
- files were modified by this hook
Stashed changes conflicted with hook auto-fixes... Rolling back fixes...
Restored changes from {patch_filename}.
```

Afterward, `.specstory/history/<current-session>.md` may be modified again,
contain an older rendering, or be missing content that appeared while the hook
ran. Retrying `git add` and `git commit` can repeat the sequence.

No secret-shaped sample belongs in this pitfall. If secret scanning also fails,
do not print, grep, or paste the matching transcript line; rotate the real
credential through the provider-first runbook.

## Root cause

Pre-commit isolates staged content by capturing unstaged changes in a patch and
checking those bytes out of the working tree before hooks run. A mutating hook
then rewrites a staged file. On context exit, pre-commit tries to apply the
captured unstaged patch.

If the patch overlaps the hook's edits, pre-commit reports that stashed changes
conflicted with hook auto-fixes. Its recovery path checks out the hook-modified
files to roll back fixes, then applies the old captured patch.

That algorithm assumes no third writer changes the working tree during the hook.
A live SpecStory recorder violates the assumption:

1. pre-commit captures a patch at time A;
2. the hook or checkout replaces the transcript;
3. SpecStory appends new session content at time B;
4. patch restoration conflicts;
5. rollback checkout discards working-tree changes, including the time-B append;
6. the time-A patch is restored, so the rendered transcript can move backward.

A one-shot ordinary commit does not avoid this path. Git may snapshot the index
once, but the hook framework still performs checkout/restore operations around
that snapshot. Blind retries create more chances to overwrite live writes and
make the prior commit outcome harder to establish.

## Workaround

1. **Stop retrying the commit.** Do not click Commit in LazyGit and do not run a
   second raw `git commit` while the recorder remains active.
2. Preserve any emitted pre-commit patch path for forensic recovery, but do not
   apply it repeatedly over a live writer.
3. Exit the agent through `run-specstory-session.sh` so the foreground recorder
   reaches a normal, provable end. A signal or nonzero exit is not equivalent.
4. Let the runner perform an exact sync for the named session after exit. That
   rebuilds the rendered transcript from the authoritative session rather than
   trusting bytes that pre-commit may have restored.
5. Use the parent-authorized post-session finalizer. It verifies the writer is
   gone, sanitizes and stages the exact artifacts atomically, validates the
   prepared snapshot, and makes one ordinary commit attempt.
6. Proceed only when the finalizer proves `committed` or `already_committed`.
   An uncertain prior attempt is reconciliation-only; do not retry it.

If a hook fails with HEAD proven unchanged and the finalizer explicitly reports
that its exact prepared snapshot was retained, fix the validation failure and
re-enter through the finalizer with fresh authorization. Do not treat the
LazyGit or `COMMIT_EDITMSG` draft as independent commit authority.

## Prevention

Hard invariant: **pre-commit is validation-only for agent artifacts.** Secret
checks may inspect staged transcript and plan bytes and fail closed, but no
pre-commit hook may redact, format, trim, fix line endings, or otherwise rewrite
those files.

The sole sanctioned post-recording mutator is the quiescent post-session
finalizer. Generic mutators must exclude every archival and skill-install root:

```text
.agents  .claude  .codex  .cursor  .opencode  .specify  .specstory
```

Keep detection enabled for the same roots. Excluding mutation is not an
allowlist for secrets.

The required operation order is:

```text
stage feature → queue → exit recorder → exact sync → finalize and prove commit
→ rebase/pull/switch/remove
```

## Related

- [Formatter rewrites committed chat transcripts](formatter-rewrites-committed-agent-transcripts.md)
- [Rebase continue refuses on a clean index with a live transcript](rebase-continue-refuses-on-clean-index-live-transcript.md)
- [pre-commit staged-file isolation source](https://github.com/pre-commit/pre-commit/blob/main/pre_commit/staged_files_only.py)
- [pre-commit hook result source](https://github.com/pre-commit/pre-commit/blob/main/pre_commit/commands/run.py)
