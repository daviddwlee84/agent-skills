# agent-history-hygiene

Keep coding-agent chat transcripts and plan files in the same commit as the
feature diff they produced, without leaking `.env` contents or API keys into
Git history.

| Surface | Question it answers |
|---|---|
| `run-specstory-session.sh` | "How do I give the recorder a provable end-of-session boundary?" |
| `queue-agent-commit.sh` | "How does the live agent request one later commit without touching its transcript?" |
| `finalize-agent-commit.sh` | "How is that exact request sanitized, attributed, and committed after the writer exits?" |
| `find-session.sh` | "Which transcript / plan file is *my* current session?" |
| `stage-agent-artifacts.sh` | "Which exact agent files belong in the prepared commit?" |
| `agent-commit-metadata.sh` | "Which harness/model and artifact trailers belong in it?" |
| `bootstrap-project.sh` | "How do I install validation-only artifact hooks and secret scanners?" |
| `scan-staged.sh` | "Is there a leaked secret in what I am about to commit?" |
| `probe-specstory-redaction.py` | "What does SpecStory already redact, so we do not redo it?" |
| `references/remediation.md` | "I already pushed a secret — now what?" |

The skill prevents four common failure modes:

1. Agents silently **drop** `.specstory/history/*.md` and plan files because
   they look generated.
2. A transcript captures a credential and sends it into Git history.
3. Pre-commit or a formatter rewrites a transcript while SpecStory is still
   writing it, then restores or checks out stale bytes over newer history.
4. A failed commit is retried through LazyGit or the CLI even though the first
   attempt may already have succeeded.

## Lifecycle invariant

A live transcript is not a normal source file. The safe boundary is:

1. **Record:** start one foreground SpecStory/Claude session in the target
   worktree. Stage only the intended feature snapshot while that session runs.
2. **Queue:** the agent records an inert request naming the exact session,
   rendered transcript, optional plan, staged tree, and base commit message.
   Queueing never reads, stages, sanitizes, or commits the live transcript.
3. **Exit:** after the request is accepted, the agent performs no more
   repository or index operations and exits. A signal or nonzero child exit
   retains the request but grants no finalization authority.
4. **Synchronize:** only after a normal child exit does the outer runner render
   the exact session and prove that synchronization completed.
5. **Finalize:** a parent-authorized finalizer revalidates the worktree, branch,
   HEAD, staged tree, selectors, absence of a writer, and absence of an active
   Git operation. It then stages and sanitizes the exact artifacts atomically,
   derives provenance from the prepared index, validates the message, and
   invokes one ordinary commit.
6. **Continue:** rebase, pull, switch, worktree removal, or a manual handoff may
   begin only after the finalizer proves `committed` or `already_committed`.

This preserves feature-plus-transcript same-commit semantics without asking a
hook to mutate files at the least stable point in their lifecycle.

## Structure

```text
skills/local/agent-history-hygiene/
├── SKILL.md
├── scripts/
│   ├── run-specstory-session.sh              # foreground lifecycle owner
│   ├── queue-agent-commit.sh                 # inert exact commit request
│   ├── finalize-agent-commit.sh              # quiescent one-shot finalizer
│   ├── find-session.sh                       # exact session discovery
│   ├── stage-agent-artifacts.sh              # atomic exact artifact preparation
│   ├── agent-commit-metadata.sh              # staged provenance trailers
│   ├── bootstrap-project.sh                  # validation/scanner bootstrap
│   ├── probe-specstory-redaction.py          # native coverage measurement
│   └── scan-staged.sh                        # staged gitleaks wrapper
├── references/
│   ├── transcript-session-discovery.md
│   ├── pre-commit-redaction-stack.md
│   ├── specstory-native-redaction.md
│   └── remediation.md
└── assets/
    ├── artifact-dirs.txt
    ├── pre-commit-config.yaml.template
    ├── gitleaks.toml.template
    └── redact_secrets.py                     # finalizer-only mutator
```

## Default workflow: finalize after the session

Launch the session from the target worktree. Parent authorization can permit
one automatic finalizer call after a successful exit; without it, the runner
still performs the exact post-exit sync and retains the request for explicit
recovery.

```bash
# Parent shell: foreground recorder and lifecycle owner.
bash skills/local/agent-history-hygiene/scripts/run-specstory-session.sh \
  --allow-commit claude
```

Inside that agent session:

1. Stage the feature paths that belong in the commit.
2. Obtain the canonical session UUID and exact rendered transcript path; name
   the exact plan, or explicitly state that no plan exists.
3. Write the base subject/body to a message file. Do not pre-populate the
   lifecycle-managed provenance trailers.
4. Queue the commit request with `queue-agent-commit.sh` using those exact
   selectors and message.
5. Report `finalization queued` and exit immediately. Do not run `git add`,
   `git commit`, rebase, or another diagnostic that writes the repository.

Use each command's `--help` for its full selector and recovery flags. The
important public contract is the boundary, not memorizing every low-level
option.

The finalizer verifies that the staged feature tree is still the queued tree.
It refuses stale HEAD/ref/index state, an active transcript writer, unrelated
commit-message drafts, and active merge, cherry-pick, revert, bisect, rebase,
sequencer, or index-lock state. A stale `REBASE_HEAD` file alone is not proof of
an active rebase; `rebase-merge`, `rebase-apply`, and `sequencer` are active
state.

### Commit before rebase

Finish and prove the feature-plus-history commit **before** rebasing it. Both a
normal commit and a rebase can execute checkout/restore behavior in hooks or in
Git itself, so neither is safe while a recorder can append to a tracked
transcript. The ordering is:

```text
stage feature → queue → exit recorder → exact sync → finalize and prove commit
→ rebase/pull/merge if needed → push or retire
```

Do not rebase a staged-but-unfinalized change, and do not treat a one-shot
normal commit as safe merely because it snapshots the index once. A mutating
pre-commit hook can still restore older working-tree bytes over a live write.

### LazyGit and CLI drafts are not retry authority

After preparing the exact tree and complete message, the finalizer writes
matching private drafts for LazyGit and Git's CLI message location, then makes
one ordinary commit attempt itself. It refuses to overwrite an unrelated or
user-edited draft and avoids partial handoff.

Those drafts provide visibility and recovery context; they do **not** authorize
a second commit path. Follow the bounded finalizer status:

- `committed` / `already_committed`: the exact parent, tree, and lifecycle
  trailer were proven; later Git operations may proceed.
- `commit_failed` with the exact prepared snapshot retained: fix the hook or
  dependency, then invoke the finalizer again with fresh explicit
  authorization. Do not click Commit in LazyGit or run a separate `git commit`.
- uncertain outcome, changed snapshot, or `commit_recovery_required`: reconcile
  HEAD and the private journal only. Never retry through LazyGit, raw Git, or
  the finalizer until the prior outcome is proven.
- `rotation_required`: rotate the exposed credential first, then use the
  explicit confirmed recovery path; prepared recovery does not restage.

## Validation-only hooks and mutator scope

`bootstrap-project.sh` installs a pinned validation-only agent-artifact check,
gitleaks, and standard repository hygiene. The artifact check and scanners may
inspect the staged snapshot but must never rewrite the index or working tree.
Redaction is owned by the quiescent post-session finalizer.

Generic mutators—formatters, linter autofixes, codemods,
`end-of-file-fixer`, and `trailing-whitespace`—must exclude every archival and
skill-install root:

```text
.agents  .claude  .codex  .cursor  .opencode  .specify  .specstory
```

Detection remains enabled for those roots. `.claude` must be excluded even
when `.agents` is excluded because `.claude/skills/<name>` can symlink into the
same installed tree. After the recorder itself, the finalizer is the sole
sanctioned component that materializes sanitized transcript bytes, and it does
so only after lifecycle quiescence.

The optional `prepare-commit-msg` integration is also validation-only. It
checks explicit session identity against the commit's actual index, including
temporary indexes used by normal Git modes, but never stages or repairs files.
If `core.hooksPath` is configured—even to an empty, relative, or external
value—bootstrap refuses automatic installation; integrate the check into the
configured hook directory deliberately.

## Exact discovery and staging

`find-session.sh` is exact by default. It validates the SpecStory prologue,
canonical lowercase UUID, direct non-symlink transcript path, strict Claude
JSONL, and canonical worktree root. The same UUID can render more than one
alias, so ambiguity requires an explicit transcript path; `--newest` is only a
compatibility escape hatch.

`stage-agent-artifacts.sh` requires a non-artifact feature diff for the
same-commit workflow. Preparation uses an alternate index under the real
worktree index lock and publishes it atomically only on success. Validation mode
never mutates an index. The finalizer uses the exact selector path; broad
branch-wide staging remains compatibility mode, not the lifecycle default.

## SpecStory 2.10 checkout scoping

Rendered output and raw Claude-session discovery are scoped by **checkout
path, not branch**. Switching branches in one checkout shares an artifact pool;
separate worktrees have separate `.specstory/history/` roots and Claude project
slugs.

Use **worktree first, recorder/session second**, with one SpecStory wrapper and
Claude session per change stream. `EnterWorktree` does not rebind an existing
watcher. Stop it and start the foreground runner in the target worktree.

## SpecStory native redaction (v2.4.0+)

SpecStory redacts on write by default using Betterleaks, covering local
Markdown and cloud sync. The repository layer is still required because
measured coverage is incomplete, especially for custom keys and webhook shapes
in prose.

| Caught by | Pairs (measured on 2.9.0) | Examples |
|---|---:|---|
| SpecStory | 36 / 54 | Major provider keys, PEM blocks, `.env` dumps |
| Repository layer only | 15 / 54 | Cursor, Tailscale, webhook and custom-key shapes in prose |
| Neither | 3 / 54 | Access-key IDs and a bot-token prose case |

Both layers use `[REDACTED:<rule-id>]`, and gitleaks allowlists that sentinel.
The finalizer leaves bytes already sanitized by SpecStory unchanged. It never
prints transcript, diff, scanner, or credential content to its bounded public
output.

## Post-leak discipline

When any layer finds a real credential:

1. **Rotate it at the provider.** This is the only revocation action.
2. Assess whether it was staged, committed locally, pushed to a feature branch,
   or reached a shared branch.
3. Scrub history only when the rotate-first runbook says it is appropriate.
   Never use plain force-push on a shared branch.

See `references/remediation.md` before any history rewrite.

## Gotchas

- Never ignore `.specstory/` or `.specstory/history/` wholesale. Only
  machine-local identity and generated statistics are excluded precisely.
- A normal child exit and exact completed sync are lifecycle proof; possession
  of a request file is not commit authority.
- A live writer blocks artifact staging and commit preparation. Do not work
  around the guard with an ordinary commit or a pre-commit mutator.
- Branch names do not scope SpecStory discovery; checkout paths do.
- Native Claude/Cursor attribution is additive. The portable minimum is the
  final staged `AI-Assisted-By` plus transcript/plan block; message attribution
  is not cryptographic signing.
- A bare phrase discussing private keys is not key material. Shipped fixtures
  build scanner-sensitive headers at runtime rather than weakening scanner
  coverage.
- `pre-commit install` is per clone, and global `core.hooksPath` protects only
  repositories that actually carry the expected configuration.

## See also

- [Source](https://github.com/daviddwlee84/agent-skills/tree/main/skills/local/agent-history-hygiene)
- [Formatter rewrites committed agent transcripts](https://github.com/daviddwlee84/agent-skills/blob/main/pitfalls/formatter-rewrites-committed-agent-transcripts.md)
- [Pre-commit restores over live SpecStory writes](https://github.com/daviddwlee84/agent-skills/blob/main/pitfalls/pre-commit-restores-over-live-specstory-writes.md)
- [Rebase continue refuses on a clean index with a live transcript](https://github.com/daviddwlee84/agent-skills/blob/main/pitfalls/rebase-continue-refuses-on-clean-index-live-transcript.md)
- [`project-knowledge-harness`](project-knowledge-harness.md) — complementary
  durable project memory; this skill supplies the Git lifecycle for agent
  review artifacts.
