#!/usr/bin/env bash
# Regression tests for MkDocs bootstrap root discovery and existing-doc handling.
# Bash 3.2 compatible (stock macOS).

set -u

TESTS_DIR="$(cd "$(dirname "$0")" && pwd)"
SKILL_DIR="$(cd "$TESTS_DIR/.." && pwd)"
REPO_ROOT="$(cd "$SKILL_DIR/../../.." && pwd)"
INIT="$SKILL_DIR/scripts/init-docs-site.sh"
PREFERENCES="$SKILL_DIR/scripts/check-preferences.sh"
BASE="$(mktemp -d /tmp/test-mkdocs-bootstrap.XXXXXX)"
BASE="$(cd "$BASE" && pwd -P)"
FAKE_BIN="$BASE/bin"
SYSTEM_PATH="/bin:/usr/bin:$PATH"
PASS_COUNT=0
FAIL_COUNT=0

trap 'rm -rf "$BASE"' EXIT

printf 'bash-under-test: %s (%s)\n' "$BASH_VERSION" "$BASH"
if [ "$(uname -s)" = "Darwin" ] && [ "${BASH_VERSINFO[0]}" != "3" ]; then
  printf 'error: Darwin compatibility suite must run with /bin/bash 3.x\n' >&2
  exit 1
fi

pass() { PASS_COUNT=$((PASS_COUNT + 1)); printf '  PASS %s\n' "$1"; }
fail() { FAIL_COUNT=$((FAIL_COUNT + 1)); printf '  FAIL %s\n' "$1"; }
contains() { printf '%s\n' "$1" | grep -Fq -- "$2"; }

assert_contains() {
  local name="$1" value="$2" expected="$3"
  if contains "$value" "$expected"; then pass "$name"; else
    fail "$name"
    printf '    expected output to contain: %s\n' "$expected" >&2
  fi
}

assert_line() {
  local name="$1" value="$2" expected="$3"
  if printf '%s\n' "$value" | grep -Fqx -- "$expected"; then pass "$name"; else
    fail "$name"
    printf '    expected exact output line: %s\n' "$expected" >&2
  fi
}

assert_file() {
  local name="$1" path="$2"
  if [ -f "$path" ]; then pass "$name"; else fail "$name"; fi
}

assert_no_file() {
  local name="$1" path="$2"
  if [ ! -e "$path" ]; then pass "$name"; else fail "$name"; fi
}

fingerprint_tree() {
  local root="$1"
  find "$root" -type f -print | LC_ALL=C sort | while IFS= read -r path; do
    printf '%s  %s\n' "$(git hash-object --no-filters "$path")" "${path#"$root"/}"
  done
}

run_init() {
  local target="$1" mode="$2"
  "$INIT" \
    --target-dir "$target" \
    --site-name "Fixture Docs" \
    --site-url "https://example.test/docs/" \
    --repo-slug "owner/repo" \
    --existing "$mode" \
    --no-workflow
}

validate_config() {
  local config="$1" mode="$2"
  shift 2
  uv run --project "$REPO_ROOT" --extra docs python - "$config" "$mode" "$@" <<'PY'
import sys
from pathlib import Path

import yaml

config = Path(sys.argv[1])
mode = sys.argv[2]
expected = sys.argv[3:]
data = yaml.safe_load(config.read_text(encoding="utf-8"))

plugins = data["plugins"]
llmstxt = next(item["llmstxt"] for item in plugins if isinstance(item, dict) and "llmstxt" in item)
guides = llmstxt.get("sections", {}).get("Guides", [])

if mode == "fresh":
    assert data["nav"] == [{"Home": "index.md"}, {"Getting Started": "getting-started.md"}]
    assert guides == ["index.md", "getting-started.md"]
elif mode == "skip":
    assert "nav" not in data
    assert guides == expected
elif mode == "wrap":
    assert data["nav"] == expected
    assert guides == expected
else:
    raise AssertionError(f"unknown mode: {mode}")
PY
}

build_fixture() {
  local target="$1"
  uv run --project "$REPO_ROOT" --extra docs mkdocs build \
    --strict \
    --config-file "$target/mkdocs.yml" \
    --site-dir "$target/site" >/dev/null
}

mkdir -p "$FAKE_BIN"
printf '#!/bin/sh\nexit 97\n' > "$FAKE_BIN/yq"
chmod +x "$FAKE_BIN/yq"

# Linked-worktree root discovery from a nested directory.
PRIMARY="$BASE/primary"
WORKTREE="$BASE/linked-worktree"
mkdir -p "$PRIMARY"
git -C "$PRIMARY" init -q -b main
printf 'base\n' > "$PRIMARY/base.txt"
git -C "$PRIMARY" add base.txt
git -C "$PRIMARY" -c core.hooksPath=/dev/null \
  -c user.name=test -c user.email=test@example.com commit -q -m init
git -C "$PRIMARY" worktree add -q -b linked "$WORKTREE"
mkdir -p "$WORKTREE/nested/deep" "$WORKTREE/.skills"
printf 'fixture: linked-worktree\n' > "$WORKTREE/.skills/preferences.yaml"

OUTPUT=$(
  cd "$WORKTREE/nested/deep" &&
  GIT_CONFIG_GLOBAL=/dev/null "$INIT" --dry-run --site-name Test \
    --site-url https://example.test/ --repo-slug owner/repo --no-workflow 2>&1
)
assert_line "init resolves linked-worktree root" "$OUTPUT" "Target: $WORKTREE"

OUTPUT=$(
  cd "$WORKTREE/nested/deep" &&
  PATH="$FAKE_BIN:$SYSTEM_PATH" GIT_CONFIG_GLOBAL=/dev/null "$PREFERENCES" --list
)
assert_contains "preferences resolve linked-worktree root" "$OUTPUT" "fixture: linked-worktree"

# Outside Git, both scripts keep the invocation directory fallback.
OUTSIDE="$BASE/outside/nested"
mkdir -p "$OUTSIDE/.skills"
printf 'fixture: outside-git\n' > "$OUTSIDE/.skills/preferences.yaml"
OUTPUT=$(
  cd "$OUTSIDE" &&
  GIT_CONFIG_GLOBAL=/dev/null "$INIT" --dry-run --site-name Test \
    --site-url https://example.test/ --repo-slug owner/repo --no-workflow 2>&1
)
assert_line "init falls back outside Git" "$OUTPUT" "Target: $OUTSIDE"
OUTPUT=$(
  cd "$OUTSIDE" &&
  PATH="$FAKE_BIN:$SYSTEM_PATH" GIT_CONFIG_GLOBAL=/dev/null "$PREFERENCES" --list
)
assert_contains "preferences fall back outside Git" "$OUTPUT" "fixture: outside-git"

# Fresh scaffold keeps the starter pages and starter configuration.
FRESH="$BASE/fresh"
mkdir -p "$FRESH"
run_init "$FRESH" skip >/dev/null
assert_file "fresh scaffold creates index" "$FRESH/docs/index.md"
assert_file "fresh scaffold creates getting started" "$FRESH/docs/getting-started.md"
if validate_config "$FRESH/mkdocs.yml" fresh; then pass "fresh config keeps starter entries"; else fail "fresh config keeps starter entries"; fi
if build_fixture "$FRESH"; then pass "fresh scaffold builds strictly"; else fail "fresh scaffold builds strictly"; fi

# --no-skeleton also removes starter references when no docs exist yet.
NO_SKELETON="$BASE/no-skeleton"
mkdir -p "$NO_SKELETON"
"$INIT" --target-dir "$NO_SKELETON" --site-name "Fixture Docs" \
  --site-url "https://example.test/docs/" --repo-slug "owner/repo" \
  --no-skeleton --no-workflow >/dev/null
assert_no_file "no-skeleton creates no docs directory" "$NO_SKELETON/docs"
if validate_config "$NO_SKELETON/mkdocs.yml" skip; then
  pass "no-skeleton removes starter references"
else
  fail "no-skeleton removes starter references"
fi

# Skip preserves existing docs and omits explicit navigation.
SKIP="$BASE/skip"
mkdir -p "$SKIP/docs/nested"
printf '# Alpha\n' > "$SKIP/docs/alpha.md"
printf '# Beta Notes\n' > "$SKIP/docs/nested/Beta notes.md"
printf 'static text\n' > "$SKIP/docs/notes.txt"
BEFORE="$(fingerprint_tree "$SKIP/docs")"
run_init "$SKIP" skip >/dev/null
AFTER="$(fingerprint_tree "$SKIP/docs")"
if [ "$BEFORE" = "$AFTER" ]; then pass "skip preserves existing docs byte-for-byte"; else fail "skip preserves existing docs byte-for-byte"; fi
assert_no_file "skip creates no starter page" "$SKIP/docs/getting-started.md"
if validate_config "$SKIP/mkdocs.yml" skip alpha.md "nested/Beta notes.md"; then pass "skip omits nav and refreshes llmstxt paths"; else fail "skip omits nav and refreshes llmstxt paths"; fi
if build_fixture "$SKIP"; then pass "skip scaffold builds strictly"; else fail "skip scaffold builds strictly"; fi

# Wrap preserves docs and writes deterministic path-only navigation.
WRAP="$BASE/wrap"
mkdir -p "$WRAP/docs/nested" "$WRAP/docs/assets"
printf '# Last\n' > "$WRAP/docs/z-last.md"
printf '# Alpha\n' > "$WRAP/docs/Alpha page.md"
printf '# Beta\n' > "$WRAP/docs/nested/Beta notes.md"
printf '# Owner\n' > "$WRAP/docs/owner's guide.md"
printf 'asset\n' > "$WRAP/docs/assets/readme.txt"
BEFORE="$(fingerprint_tree "$WRAP/docs")"
run_init "$WRAP" wrap >/dev/null
AFTER="$(fingerprint_tree "$WRAP/docs")"
if [ "$BEFORE" = "$AFTER" ]; then pass "wrap preserves existing docs byte-for-byte"; else fail "wrap preserves existing docs byte-for-byte"; fi
assert_no_file "wrap creates no starter page" "$WRAP/docs/getting-started.md"
if validate_config "$WRAP/mkdocs.yml" wrap \
  "Alpha page.md" "nested/Beta notes.md" "owner's guide.md" "z-last.md"; then
  pass "wrap writes sorted path-only nav and llmstxt paths"
else
  fail "wrap writes sorted path-only nav and llmstxt paths"
fi
if build_fixture "$WRAP"; then pass "wrap scaffold builds strictly"; else fail "wrap scaffold builds strictly"; fi

# Dry-run does not create or alter files.
DRY="$BASE/dry-run"
mkdir -p "$DRY/docs"
printf '# Existing\n' > "$DRY/docs/existing.md"
BEFORE="$(fingerprint_tree "$DRY")"
"$INIT" --target-dir "$DRY" --dry-run --site-name Test \
  --site-url https://example.test/ --repo-slug owner/repo --existing wrap --no-workflow >/dev/null 2>&1
AFTER="$(fingerprint_tree "$DRY")"
if [ "$BEFORE" = "$AFTER" ]; then pass "dry-run leaves target unchanged"; else fail "dry-run leaves target unchanged"; fi
assert_no_file "dry-run creates no config" "$DRY/mkdocs.yml"

printf '\n%d passed, %d failed\n' "$PASS_COUNT" "$FAIL_COUNT"
[ "$FAIL_COUNT" -eq 0 ]
