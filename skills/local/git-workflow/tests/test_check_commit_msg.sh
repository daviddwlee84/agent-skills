#!/usr/bin/env bash
# Regression tests for scripts/check-commit-msg.sh.

set -u

TESTS_DIR="$(cd "$(dirname "$0")" && pwd)"
SKILL_DIR="$(cd "$TESTS_DIR/.." && pwd)"
SCRIPT="$SKILL_DIR/scripts/check-commit-msg.sh"
PASS_COUNT=0
FAIL_COUNT=0

pass() { PASS_COUNT=$((PASS_COUNT + 1)); printf '  PASS %s\n' "$1"; }
fail() { FAIL_COUNT=$((FAIL_COUNT + 1)); printf '  FAIL %s\n' "$1"; }

expect_rc() {
  local expected="$1" label="$2" message="$3"
  shift 3
  printf '%s\n' "$message" | bash "$SCRIPT" "$@" >/dev/null 2>&1
  rc=$?
  if [ "$rc" = "$expected" ]; then pass "$label"
  else fail "$label (expected $expected, got $rc)"; fi
}

make_repo() {
  local repo
  repo=$(mktemp -d /tmp/test-commit-msg.XXXXXX)
  git -C "$repo" init -q -b main
  git -C "$repo" -c user.name=test -c user.email=test@example.com commit -q --allow-empty -m init
  printf '%s' "$repo"
}

printf '== check commit message ==\n'

expect_rc 0 "legacy header-only mode stays compatible" 'feat(auth): add refresh token'
expect_rc 1 "agentic message requires body" $'feat: add x\n\nAI-Assisted-By: Codex CLI (gpt-5.6-sol)' --agentic
expect_rc 0 "trivial escape hatch permits no body" $'docs: fix typo\n\nAI-Assisted-By: Codex CLI (gpt-5.6-sol)' --agentic --allow-no-body
expect_rc 1 "agentic body must be English" $'feat: add x\n\n加入新的行為。\n\nAI-Assisted-By: Codex CLI (gpt-5.6-sol)' --agentic
expect_rc 1 "canonical metadata must be in final trailer block" $'feat: add x\n\nExplain why.\n\nAI-Assisted-By: Codex CLI (gpt-5.6-sol)\n\nGenerated with Claude Code' --agentic
expect_rc 0 "native co-author may coexist" $'feat: add x\n\nExplain why.\n\nCo-Authored-By: Claude Fable 5 <noreply@anthropic.com>\nAI-Assisted-By: Claude Code (Claude Fable 5)' --agentic
expect_rc 0 "Generated-with prose may precede final trailers" $'feat: add x\n\nExplain why.\n\nGenerated with Claude Code\n\nCo-Authored-By: Claude Fable 5 <noreply@anthropic.com>\nAI-Assisted-By: Claude Code (Claude Fable 5)' --agentic
expect_rc 1 "duplicate assistant trailer fails" $'feat: add x\n\nExplain why.\n\nAI-Assisted-By: Codex CLI (gpt-5.6-sol)\nAI-Assisted-By: Codex CLI (gpt-5.6-sol)' --agentic

repo=$(make_repo)
mkdir -p "$repo/.specstory/history" "$repo/.claude/plans"
printf '# chat\n' > "$repo/.specstory/history/session.md"
printf '# plan\n' > "$repo/.claude/plans/plan.md"
git -C "$repo" add .specstory/history/session.md .claude/plans/plan.md
valid=$'feat: add x\n\nExplain why this behavior is needed.\n\nAI-Assisted-By: Codex CLI (gpt-5.6-sol)\nAgent-Transcript: .specstory/history/session.md\nAgent-Plan: .claude/plans/plan.md'
printf '%s\n' "$valid" | (cd "$repo" && bash "$SCRIPT" --agentic --staged) >/dev/null 2>&1
rc=$?
if [ "$rc" = "0" ]; then pass "staged artifact paths match trailers"
else fail "staged artifact paths match trailers (got $rc)"; fi

missing_plan=$'feat: add x\n\nExplain why this behavior is needed.\n\nAI-Assisted-By: Codex CLI (gpt-5.6-sol)\nAgent-Transcript: .specstory/history/session.md'
printf '%s\n' "$missing_plan" | (cd "$repo" && bash "$SCRIPT" --agentic --staged) >/dev/null 2>&1
rc=$?
if [ "$rc" = "1" ]; then pass "missing staged plan trailer fails"
else fail "missing staged plan trailer fails (got $rc)"; fi
rm -rf "$repo"

printf 'pass: %d\nfail: %d\n' "$PASS_COUNT" "$FAIL_COUNT"
[ "$FAIL_COUNT" = "0" ]
