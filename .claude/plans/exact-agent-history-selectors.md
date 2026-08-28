# Exact agent-history selectors

## Scope and invariants

- Change only `skills/local/agent-history-hygiene`, its EN/zh-TW public docs, root `Makefile` test wiring, and this plan.
- Leave vendored snapshots, `redact_secrets.py`, release tags, and the live SpecStory transcript untouched.
- Resolve relative paths from the git root, reject paths outside it, and keep Bash 3.2 compatibility.

## Implementation

1. **Exact discovery** — add `--session-id`, `--specstory-path`, and opt-in `--newest`; validate the fixed-byte real SpecStory v2.1 prologue and nonsymlink path, search exact lowercase UUID JSONLs across launch-directory stores, parse every record and canonicalize `cwd` roots, reject unsafe selector/output bytes, and emit structured status/candidates with dependency-aware fail-closed exits.
2. **Atomic staging** — require exact identity plus explicit plan policy; classify broad status from one NUL snapshot (including deletion/rename pairs); normalize configured directories; reject ignored, unaddable, or unmerged artifacts. Hold the real per-worktree index lock while staged-code validation and one add run against an alternate index, then atomically publish it so failures/races leave the real index unchanged.
3. **Hook behavior** — generate a validation-only explicit-env hook that runs `--check-staged` against the commit's current `GIT_INDEX_FILE` and never mutates it. Missing code/artifacts fail with the exact staging command; identity absence visibly no-ops. Cover normal, `-a`, and `--only` commit indexes. Automatic installation requires `core.hooksPath` genuinely unset, including in linked worktrees.
4. **Regression coverage** — add `tests/test_find_session.sh` and `tests/test_stage_agent_artifacts.sh`; extend metadata/hook assertions so trailers contain only exact staged artifacts; wire both scripts into `make test-skill`.
5. **Documentation** — update `SKILL.md`, `references/transcript-session-discovery.md`, `tests/README.md`, and public EN/zh-TW pages with exact-mode examples and verified SpecStory 2.10 checkout-scoping/worktree guidance.

## Validation

Run `bash -n` on changed shell files, `shellcheck` when installed, the skill linter, `make test-skill`, `make validate`, and `make docs-build`. Report exact commands, results, changed files, and any blockers; do not commit, push, or stage repository changes.
