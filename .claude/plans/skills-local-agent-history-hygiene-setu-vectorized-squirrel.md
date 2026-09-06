# Context

The current workflow can never reliably converge while SpecStory is recording the same transcript that an agent is trying to commit. `redact_secrets.py` detects from the staged index but rewrites the live pathname, a later `git add` can replace that fix, and pre-commit itself stashes unstaged changes by running a real-worktree checkout/restore cycle. A continuously writing transcript can therefore be overwritten, reintroduced, or repeatedly reported even when the staged blob was initially frozen. Generic whitespace/EOF fixers are also inappropriate for archival transcripts.

The selected outcome is a **post-session finalizer**. During a recorded Claude session the agent queues one inert commit request and exits; only the outer process that launched `specstory run claude` may finalize after SpecStory has exited. The finalizer gets one attempt to sanitize, stage, validate, and run a normal `git commit` with every configured hook. If it cannot do so safely, it must stop once and leave a ready commit-message handoff for LazyGit/CLI rather than making the agent retry.

## Implementation

### 1. Add a three-surface post-session lifecycle

Create these Bash-3.2-compatible public scripts, using a small stdlib Python helper only where JSON/process handling is materially safer:

- `skills/local/agent-history-hygiene/scripts/run-specstory-session.sh`
  - Support `specstory run claude` only in v1, because the existing exact session resolver is Claude-specific.
  - Require an explicit `--allow-commit` on the outer command; export only an absolute per-run request path to the child agent.
  - Keep SpecStory attached to the foreground TTY, forward/record termination signals, wait for it to exit, and invoke the finalizer exactly once only after a normal exit. A signaled/nonzero run retains any request and never commits.
  - After normal exit, perform one exact, quiet `specstory sync claude -s UUID` if a request exists, then revalidate the rendered path. A sync failure is a retained handoff, not a retry.
  - Do not use a Claude Stop hook, detached worker, watcher, or `EXIT`-trap commit; those all run before lifecycle quiescence is proven or can outlive authorization.

- `skills/local/agent-history-hygiene/scripts/queue-agent-commit.sh`
  - Require `--commit`, canonical session UUID, exact SpecStory path, explicit `--plan PATH|--no-plan`, and a base message file.
  - Validate safe selectors and staged non-artifact feature work, but never stage/read/scan/redact the live transcript and never commit.
  - Capture the canonical worktree/per-worktree Git dir, branch ref, `HEAD`, staged tree OID, exact selectors, base subject/body, schema version, and action in a strict JSON request. Store no diff, transcript bytes, process arguments, scanner output, or credential material.
  - Place each request under `git rev-parse --path-format=absolute --git-path agent-history-hygiene/runs/<id>/`, with a `0700` directory and atomic, nonsymlink `0600` files. A second differing request fails; an identical request is an idempotent no-op.
  - Make queueing the agent's final repository/index action. The skill must tell the agent to report “finalization queued” and exit, never to try `git add → pre-commit → fix → retry` in-session.

- `skills/local/agent-history-hygiene/scripts/finalize-agent-commit.sh`
  - Accept only a request created by the matching outer run plus parent-held commit authorization. Recovery requires the user to pass authorization again; a request file alone is not authority to commit.
  - Fail closed on stale `HEAD`/branch/staged-tree state, merge/rebase/cherry-pick state, unsafe request ownership/mode/path, selector ambiguity, a still-live writer, or concurrent finalizer/index ownership.
  - Journal bounded states (`pending`, `prepared`, `rotation-required`, `committing`, `done`, `failed`) atomically so a crash after commit is reconciled by exact parent/tree/request identity, never by issuing a second commit.

### 2. Sanitize one quiescent candidate snapshot, then use normal Git

Reuse the alternate-index transaction in `scripts/stage-agent-artifacts.sh` rather than introducing `commit-tree`, a permanent shadow index, `--no-verify`, `SKIP`, or manual hook replay.

- Extract/reuse its real per-worktree `index.lock`, alternate `GIT_INDEX_FILE`, preflight, and atomic publication logic. Resolve index paths absolutely before changing directories.
- After SpecStory exit/sync, verify exact transcript/plan files with `find-session.sh`, capture their inode/stat/digest, and stage them exactly once into the candidate index while preserving all pre-queued feature entries.
- Run the residual sanitizer against **stage-0 blobs in that candidate index**; read by OID, preserve regular-file mode and all nonsecret bytes, write replacement blobs with no second clean-filter pass, and update entries through `git update-index`. Never perform a later `git add` of the sanitized hot artifact.
- Re-scan the complete candidate index fail-closed. Before publication, confirm the now-quiescent working files still match the captured generation, then materialize the sanitized candidate blobs back to those exact paths using Git's checkout/filter semantics. This prevents a clean commit paired with a locally leaky transcript.
- If a real credential was found, publish only the sanitized local/index state, mark `rotation-required`, and stop before commit. Rotation/revocation remains a human action; resume requires explicit confirmation. Document that earlier raw staging may have left unreachable local objects and never auto-run GC/prune.
- Derive `AI-Assisted-By`, transcript, and plan trailers from the candidate index via `agent-commit-metadata.sh`; validate the final message against the same index with `check-commit-msg.sh`.
- Atomically publish the candidate index, recheck its tree, and invoke one ordinary `git commit -F ...` in the original worktree. All native/global pre-commit, prepare-commit-msg, commit-msg, and post-commit hooks run normally. A hook modification/failure is retained for handoff and is never auto-restaged or retried.

### 3. Make secret checks validation-only and fail closed

Refactor `assets/redact_secrets.py` while reusing its placeholder and pure replacement logic:

- Add an explicit staged/index check mode for pre-commit and an internal exact-file/index-fix mode for the quiescent finalizer; retain legacy worktree fixing only as a clearly deprecated manual mode.
- Make the effective `GIT_INDEX_FILE` the sole source in staged mode. Use component-anchored artifact paths, exact candidate arguments, stage-0 regular blobs, and NUL-safe Git interfaces; reject symlinks, gitlinks, unmerged entries, unsafe paths, and lookalike prefixes.
- Treat a missing scanner, nonzero scanner result, invalid config, malformed/non-list JSON, or failed post-redaction scan as an operational error—not an empty clean result.
- Redact complete, structurally bounded PEM/OpenVPN/PuTTY material. An incomplete or unparseable key block must block finalization rather than merely removing the detector header and leaving key bytes behind.
- Never print `Secret`, `Match`, scanner stderr, fingerprints, or partial credential bytes. Emit only bounded structured status/count/rule/path/line metadata.

Update `scripts/scan-staged.sh` to share the same safe-output/fail-closed contract: remove the `match` field, reject malformed reports, mask scanner diagnostics by default, and describe `--redact` only as output masking (not file rewriting).

### 4. Replace mutating pre-commit behavior and migrate safely

- In `.pre-commit-hooks.yaml`, publish a validation-only staged-index hook. Keep the historical `redact-agent-secrets` ID only as a deprecated validation-only alias so an update cannot continue mutating a live transcript; add/use a clearly named check hook in new templates.
- In `assets/pre-commit-config.yaml.template`, move to a new immutable major hook tag and exclude every archival/install root from generic mutators such as `trailing-whitespace` and `end-of-file-fixer`: `.agents`, `.claude`, `.codex`, `.cursor`, `.opencode`, `.specify`, and `.specstory`. Do not exclude them from gitleaks, private-key detection, or the dedicated finalizer sanitizer.
- Harden `scripts/bootstrap-project.sh --migrate`: build and validate a candidate config first; update the exact old pin; remove only the redactor hook item from local/remote blocks; preserve sibling hooks and overrides; refuse ambiguous/custom arguments; merge known formatter exclusions; atomically publish; only then remove a recognized unmodified legacy script. A second migration must be byte-stable.
- Prepare release/version documentation, but do not create or push the new hook tag without separate explicit approval.

### 5. Guarantee a useful manual handoff

Compose the full validated message before attempting `git commit` and keep a request-owned copy. On any one-shot finalizer failure after message preparation:

- Atomically seed both the worktree Git dir's `LAZYGIT_PENDING_COMMIT` (the file LazyGit's `c` panel reads) and `git rev-parse --git-path COMMIT_EDITMSG` for standard Git/editor workflows.
- Refuse to overwrite an unrelated existing draft; track the hashes of drafts owned by this request.
- Print only a concise reason code, whether staging/message/trailers are ready, and the next single action (for example, rotate then resume, fix a non-artifact hook issue, or open LazyGit and press `c`).
- On successful automatic commit, remove only the LazyGit pending draft still matching this request. On early/stale failure, preserve the base draft but state that trailers/staging are not yet verified.

### 6. Update the skill's procedure and durable knowledge

- Replace Workflow A and the racy “atomic Python + git add + commit” gotcha in `SKILL.md` with one default: launch through the outer runner, stage feature paths, queue once after explicit commit authorization, then exit. Keep `SKILL.md` below 500 lines by moving lifecycle/recovery details into a new `references/post-session-finalization.md`.
- Rewrite `references/pre-commit-redaction-stack.md` so the post-session finalizer is the only mutator and pre-commit is validation-only; update session discovery/native-redaction/remediation text where the lifecycle boundary matters.
- Correct `pitfalls/rebase-continue-refuses-on-clean-index-live-transcript.md` and `pitfalls/formatter-rewrites-committed-agent-transcripts.md`, and add a symptom-first pitfall for pre-commit rollback against a live SpecStory writer. Treat the separate chezmoi pitfall as an explicit cross-repository follow-up, not part of this change.
- Update `tests/README.md` and the published EN/zh-TW skill docs. Keep all shipped secret fixtures synthetic so downstream `detect-private-key` remains clean.

## Verification

Add deterministic tests using temporary repositories, fake `specstory`/gitleaks commands, FIFO/barrier synchronization, and real Git hooks—never timing sleeps or the live transcript:

- **Lifecycle/request:** normal exit + request finalizes once; no request is a no-op; nonzero/signal retains request; linked worktrees cannot consume each other's requests; stale head/ref/tree, unsafe request files, and active writer all fail without a commit; crash recovery recognizes an already-created commit rather than duplicating it.
- **Snapshot/sanitizer:** staged-vs-working-tree divergence, writer shutdown before any read, exact path/mode preservation, filters applied once, idempotent redaction, complete private-key block handling, fail-open scanner regressions, atomic index publication, no secret bytes in stdout/stderr, and no post-redaction `git add`.
- **Hooks/commit:** pre-commit, prepare-commit-msg, commit-msg, and post-commit each run once in the original worktree; a mutating/failing hook produces one failure and a ready handoff; successful commits contain the queued feature tree plus only the selected transcript/plan and canonical trailers.
- **Fallback:** failure seeds request-owned `LAZYGIT_PENDING_COMMIT` and `COMMIT_EDITMSG`; existing foreign drafts are preserved; successful commit removes only the owned LazyGit draft.
- **Migration/config:** old remote/local redactor layouts with sibling hooks, custom overrides, invalid candidates, idempotency, full-root formatter exclusions, and validation-only hook behavior.

Run:

```bash
make test-skill
bash skills/local/skill-author/scripts/lint-skill.sh \
  skills/local/agent-history-hygiene
pre-commit validate-manifest .pre-commit-hooks.yaml
pre-commit validate-config \
  skills/local/agent-history-hygiene/assets/pre-commit-config.yaml.template
make validate
make docs-build
```

Finally exercise a disposable end-to-end `run-specstory-session.sh --allow-commit claude` flow: queue from the child, verify no finalizer starts before the fake writer exits, confirm a normal successful auto-commit, then repeat with a hook failure and verify the staged snapshot plus LazyGit/CLI message handoff are usable without another agent attempt.

## Sources

- [LazyGit commit-message context (`LAZYGIT_PENDING_COMMIT`)](https://github.com/jesseduffield/lazygit/blob/3f6be3b3ee7b69c0dbed429669134fd04e1e9e35/pkg/gui/context/commit_message_context.go)
- [SpecStory 2.10 Claude executor lifecycle](https://github.com/specstoryai/getspecstory/blob/v2.10.0/specstory-cli/pkg/providers/claudecode/claude_code_exec.go#L101-L139)
- [SpecStory 2.10 run lifecycle](https://github.com/specstoryai/getspecstory/blob/v2.10.0/specstory-cli/main.go#L339-L507)
