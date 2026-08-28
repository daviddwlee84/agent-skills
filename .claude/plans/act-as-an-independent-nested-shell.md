# Read-only QA review of exact agent-history selectors

## Context

The current worktree implements exact session selection, atomic artifact staging, generated pre-commit hook behavior, and corresponding documentation/tests. The review must independently verify those guarantees against `main`, including tracked and untracked files, without editing source, staging changes, committing, pushing, or otherwise mutating the repository or its index. The intended outcome is a ranked list of only reproducible defects (or an explicit no-findings result), plus the exact tests run.

## Review procedure

1. **Freeze the review surface and baseline**
   - Inventory tracked and untracked changes against `main`, including the new shell tests, plan, and SpecStory transcripts that plain `git diff` omits.
   - Record the worktree root/common git dir/worktree git dir, current index tree, and `/bin/bash` version. Re-check source/index status after testing.

2. **Audit shell contracts statically**
   - Read the changed scripts and tests with their `main` versions side by side.
   - Run `/bin/bash -n` and available non-mutating shell lint checks on the changed shell files.
   - Trace argument parsing, quoting, exit-code mapping, temp-file cleanup, path canonicalization, output escaping, and every path to `git add` under Bash 3.2 semantics.

3. **Exercise `find-session.sh` adversarially**
   - Use trap-cleaned temporary fixture repositories and synthetic SpecStory/Claude JSONL data; isolate `HOME`, `TMPDIR`, `GIT_CONFIG_GLOBAL`, and `GIT_CONFIG_NOSYSTEM=1`, and do not write fixtures into this worktree.
   - Cover valid exact UUID and path selectors, relative paths from the worktree root, malformed/mismatched UUIDs, filename-versus-record identity mismatch, wrong `cwd`, missing/unreadable/outside/symlink-escape paths, duplicate candidates, same-checkout branch leakage, and two-worktree isolation.
   - Validate success/error exit codes and machine-parse TSV/JSON outputs, including control characters, spaces, quotes, backslashes, null/empty fields, candidate arrays, and diagnostics remaining off stdout.

4. **Exercise `stage-agent-artifacts.sh` and hook generation**
   - In isolated temporary git repositories, cover all session-only plan/no-plan/no-specstory combinations, invalid selectors and artifact paths, redaction/validation failures, and successful staging.
   - Snapshot `git write-tree`/index state before and after every failing case to prove fail-closed atomicity; instrument or shim git in fixtures to prove all validation precedes exactly one successful `git add` invocation.
   - Generate hooks in temporary repositories and verify selector environment quoting with whitespace/metacharacters/newlines where accepted, no-op behavior when identity is absent, propagation of real failures, executable output, and refusal under both local and global `core.hooksPath` configurations.

5. **Verify tests, docs, and leakage claims**
   - Inspect test fixtures/assertions to ensure they create genuinely distinct same-checkout branches and linked worktrees rather than merely asserting labels or paths.
   - Compare EN/zh-TW docs, `SKILL.md`, and the discovery reference with observed SpecStory 2.10 behavior and script CLI/output semantics.
   - Scan all changed and untracked artifacts for credentials, tokens, private keys, sensitive transcript content, usernames/home paths, temp paths, and other machine-specific absolute paths; distinguish expected redacted examples from publishable leaks.

6. **Run repository verification and report**
   - Run the targeted shell tests first, then the existing skill test target and applicable validation/docs targets whose outputs are already expected by the repository.
   - Re-check `git status`, unstaged diff, cached diff, and index tree to confirm the review itself changed no source or index state (excluding any explicitly expected generated build outputs, which must be reported).
   - Record every mandatory review row as PASS, FAIL, or UNVERIFIED; an unexecuted row is never inferred to pass and prevents an unconditional clean verdict.
   - Report findings by severity with clickable `file:line`, violated invariant, concrete input/state, exact reproduction command, observed result, and expected result. If no issue survives reproduction, state “No findings.” List every command/test and its pass/fail/skip result separately.

## Critical files

- `skills/local/agent-history-hygiene/scripts/find-session.sh`
- `skills/local/agent-history-hygiene/scripts/stage-agent-artifacts.sh`
- `skills/local/agent-history-hygiene/scripts/bootstrap-project.sh`
- `skills/local/agent-history-hygiene/tests/test_find_session.sh`
- `skills/local/agent-history-hygiene/tests/test_stage_agent_artifacts.sh`
- `skills/local/agent-history-hygiene/references/transcript-session-discovery.md`
- `skills/local/agent-history-hygiene/SKILL.md`
- `docs/skills/agent-history-hygiene.md`
- `docs/skills/agent-history-hygiene.zh-TW.md`
- `Makefile`
- Changed/untracked `.claude/plans/` and `.specstory/history/` artifacts
