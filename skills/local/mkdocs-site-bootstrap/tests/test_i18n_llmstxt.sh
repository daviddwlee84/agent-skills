#!/usr/bin/env bash
# End-to-end regression tests for the managed i18n + llmstxt two-pass build.
# Bash 3.2 compatible (stock macOS).

set -u

TESTS_DIR="$(cd "$(dirname "$0")" && pwd)"
SKILL_DIR="$(cd "$TESTS_DIR/.." && pwd)"
REPO_ROOT="$(cd "$SKILL_DIR/../../.." && pwd)"
INIT="$SKILL_DIR/scripts/init-docs-site.sh"
ADD_LANGUAGE="$SKILL_DIR/scripts/add-language.sh"
MIGRATE="$SKILL_DIR/scripts/migrate-i18n-llmstxt.sh"
CANONICAL_HELPER="$SKILL_DIR/assets/build-docs-site.py"
BASE="$(mktemp -d /tmp/test-mkdocs-i18n-llmstxt.XXXXXX)"
BASE="$(cd "$BASE" && pwd -P)"
PASS_COUNT=0
FAIL_COUNT=0

trap 'rm -rf "$BASE"' EXIT

pass() { PASS_COUNT=$((PASS_COUNT + 1)); printf '  PASS %s\n' "$1"; }
fail() { FAIL_COUNT=$((FAIL_COUNT + 1)); printf '  FAIL %s\n' "$1"; }

assert_file() {
  if [ -f "$2" ]; then pass "$1"; else fail "$1"; fi
}

assert_no_file() {
  if [ ! -e "$2" ]; then pass "$1"; else fail "$1"; fi
}

assert_contains() {
  if grep -Fq -- "$3" "$2"; then pass "$1"; else
    fail "$1"
    printf '    expected %s to contain: %s\n' "$2" "$3" >&2
  fi
}

fingerprint_tree() {
  local root="$1"
  find "$root" -type f -print | LC_ALL=C sort | while IFS= read -r file; do
    printf '%s  %s\n' "$(git hash-object --no-filters "$file")" "${file#"$root"/}"
  done
}

run_init() {
  local target="$1"
  shift
  mkdir -p "$target"
  git -C "$target" init -q
  "$INIT" --target-dir "$target" --site-name "Fixture Docs" \
    --site-url "https://example.test/docs/" --repo-slug owner/repo "$@"
}

run_helper() {
  local target="$1"
  uv run --project "$REPO_ROOT" --extra docs python \
    "$target/scripts/build-docs-site.py" --target-dir "$target"
}

run_direct_build() {
  local target="$1" output="$2"
  uv run --project "$REPO_ROOT" --extra docs mkdocs build --strict \
    --config-file "$target/mkdocs.yml" --site-dir "$output"
}

printf 'bash-under-test: %s (%s)\n' "$BASH_VERSION" "$BASH"

if ! command -v yq >/dev/null 2>&1 || ! yq --version 2>/dev/null | grep -Fqi mikefarah; then
  printf 'error: mikefarah/yq v4 is required\n' >&2
  exit 1
fi

# A project-owned helper collision fails before the scaffold writes anything.
INIT_COLLISION="$BASE/init-collision"
mkdir -p "$INIT_COLLISION/scripts"
printf 'project owned\n' > "$INIT_COLLISION/scripts/build-docs-site.py"
if "$INIT" --target-dir "$INIT_COLLISION" --site-name Collision \
  --site-url https://example.test/collision/ --repo-slug owner/repo \
  >/dev/null 2>&1; then
  fail "init rejects a project-owned helper collision"
else
  pass "init rejects a project-owned helper collision"
fi
assert_no_file "helper collision creates no mkdocs config" "$INIT_COLLISION/mkdocs.yml"
assert_no_file "helper collision creates no pyproject" "$INIT_COLLISION/pyproject.toml"
assert_contains "helper collision preserves project file" \
  "$INIT_COLLISION/scripts/build-docs-site.py" "project owned"

INIT_SYMLINK="$BASE/init-scripts-symlink"
INIT_SYMLINK_EXTERNAL="$BASE/init-scripts-external"
mkdir -p "$INIT_SYMLINK" "$INIT_SYMLINK_EXTERNAL"
ln -s "$INIT_SYMLINK_EXTERNAL" "$INIT_SYMLINK/scripts"
if "$INIT" --target-dir "$INIT_SYMLINK" --site-name Collision \
  --site-url https://example.test/collision/ --repo-slug owner/repo \
  >/dev/null 2>&1; then
  fail "init rejects a symlinked scripts directory"
else
  pass "init rejects a symlinked scripts directory"
fi
assert_no_file "scripts symlink creates no mkdocs config" "$INIT_SYMLINK/mkdocs.yml"
assert_no_file "scripts symlink writes nothing outside target" \
  "$INIT_SYMLINK_EXTERNAL/build-docs-site.py"

# A new monolingual scaffold uses the managed helper for the complete artifact.
FRESH="$BASE/fresh"
run_init "$FRESH" --no-workflow >/dev/null
assert_file "fresh scaffold installs build helper" "$FRESH/scripts/build-docs-site.py"
if cmp -s "$CANONICAL_HELPER" "$FRESH/scripts/build-docs-site.py"; then
  pass "installed helper matches canonical asset"
else
  fail "installed helper matches canonical asset"
fi

if run_direct_build "$FRESH" "$FRESH/direct-site" >/dev/null; then
  pass "direct monolingual strict preview builds"
else
  fail "direct monolingual strict preview builds"
fi
assert_no_file "direct preview omits llms.txt" "$FRESH/direct-site/llms.txt"

if run_helper "$FRESH" > "$FRESH/helper.json" 2> "$FRESH/helper.log"; then
  pass "managed monolingual build succeeds"
else
  fail "managed monolingual build succeeds"
  sed -n '1,160p' "$FRESH/helper.log" >&2
fi
assert_file "managed build writes llms.txt" "$FRESH/site/llms.txt"
assert_file "managed build writes llms-full.txt" "$FRESH/site/llms-full.txt"
assert_file "managed build writes root Markdown sidecar" "$FRESH/site/index.md"
assert_file "managed build writes nested Markdown sidecar" \
  "$FRESH/site/getting-started/index.md"
if [ "$(grep -c '^- \[' "$FRESH/site/llms.txt")" -eq 2 ]; then
  pass "monolingual llms index contains both starter pages"
else
  fail "monolingual llms index contains both starter pages"
fi
assert_contains "full output contains home body" "$FRESH/site/llms-full.txt" \
  "Welcome to the Fixture Docs documentation."
assert_contains "helper emits structured success" "$FRESH/helper.json" \
  '"status": "ok"'

# Adding zh-TW keeps both builds strict while root llms remains default-language.
if "$ADD_LANGUAGE" --target-dir "$FRESH" --lang zh-TW \
  > "$FRESH/add-language.json" 2> "$FRESH/add-language.log"; then
  pass "add-language configures safe two-pass build"
else
  fail "add-language configures safe two-pass build"
  sed -n '1,160p' "$FRESH/add-language.log" >&2
fi
DOCS_BEFORE="$(fingerprint_tree "$FRESH/docs")"
if run_helper "$FRESH" > "$FRESH/i18n-helper.json" 2> "$FRESH/i18n-helper.log"; then
  pass "managed bilingual build succeeds"
else
  fail "managed bilingual build succeeds"
  sed -n '1,200p' "$FRESH/i18n-helper.log" >&2
fi
DOCS_AFTER="$(fingerprint_tree "$FRESH/docs")"
if [ "$DOCS_BEFORE" = "$DOCS_AFTER" ]; then
  pass "managed build leaves source docs byte-identical"
else
  fail "managed build leaves source docs byte-identical"
fi
assert_file "bilingual build keeps translated HTML" "$FRESH/site/zh-TW/index.html"
if grep -Fq '/zh-TW/' "$FRESH/site/llms.txt"; then
  fail "root llms excludes translated URLs"
else
  pass "root llms excludes translated URLs"
fi
if [ "$(grep -c '^- \[' "$FRESH/site/llms.txt")" -eq 2 ]; then
  pass "bilingual root llms keeps both default pages"
else
  fail "bilingual root llms keeps both default pages"
fi
assert_contains "English page exposes source edit link" "$FRESH/site/index.html" \
  "https://github.com/owner/repo/edit/main/docs/index.md"
assert_contains "translated page exposes translated edit link" \
  "$FRESH/site/zh-TW/index.html" \
  "https://github.com/owner/repo/edit/main/docs/index.zh-TW.md"

if run_direct_build "$FRESH" "$FRESH/direct-i18n-site" >/dev/null; then
  pass "direct bilingual strict preview builds"
else
  fail "direct bilingual strict preview builds"
fi
assert_no_file "direct bilingual preview cannot publish stale llms" \
  "$FRESH/direct-i18n-site/llms.txt"

# A failed LLM pass must not replace an already-good generated site.
printf 'preserve me\n' > "$FRESH/site/prior-site-marker.txt"
yq '(.plugins[] | select(has("llmstxt")) | .llmstxt.sections.Guides) += ["missing.md"]' \
  "$FRESH/mkdocs.yml" > "$FRESH/mkdocs.broken"
mv "$FRESH/mkdocs.broken" "$FRESH/mkdocs.yml"
if run_helper "$FRESH" > "$FRESH/failed-helper.json" 2> "$FRESH/failed-helper.log"; then
  fail "missing llmstxt page fails the managed build"
else
  pass "missing llmstxt page fails the managed build"
fi
assert_file "failed build preserves previous site" "$FRESH/site/prior-site-marker.txt"

# Audit and migrate the exact legacy scaffold shape conservatively.
LEGACY="$BASE/legacy"
run_init "$LEGACY" >/dev/null
"$ADD_LANGUAGE" --target-dir "$LEGACY" --lang zh-TW >/dev/null 2>&1
yq '
  del(.docs_dir)
  | del(.plugins[] | select(has("i18n")) | .i18n.enabled)
  | del(.plugins[] | select(has("llmstxt")) | .llmstxt.enabled)
  | del(.plugins[] | select(has("copy-to-llm")) | ."copy-to-llm".enabled)
  | .theme.features = (.theme.features - ["content.action.edit"])
  | (.markdown_extensions[] | select(has("pymdownx.snippets")) |
      ."pymdownx.snippets".base_path) = [".", "docs", "docs/_snippets"]
' "$LEGACY/mkdocs.yml" > "$LEGACY/mkdocs.legacy"
mv "$LEGACY/mkdocs.legacy" "$LEGACY/mkdocs.yml"
perl -pi -e 's/uv run python scripts\/build-docs-site\.py/uv run mkdocs build/' \
  "$LEGACY/.github/workflows/docs.yml"

if run_helper "$LEGACY" > "$LEGACY/legacy-helper.json" \
  2> "$LEGACY/legacy-helper.log"; then
  fail "managed helper rejects an unguarded legacy config"
else
  pass "managed helper rejects an unguarded legacy config"
fi
assert_contains "legacy helper points to the migration command" \
  "$LEGACY/legacy-helper.log" "migrate-i18n-llmstxt.sh"

set +e
"$MIGRATE" --target-dir "$LEGACY" --json > "$LEGACY/audit.json"
AUDIT_RC=$?
set -e
if [ "$AUDIT_RC" -eq 10 ]; then pass "migration audit reports affected legacy site"; else fail "migration audit reports affected legacy site"; fi
assert_contains "audit JSON identifies affected state" "$LEGACY/audit.json" \
  '"status":"affected"'

LEGACY_BEFORE="$(git hash-object --no-filters "$LEGACY/mkdocs.yml") $(git hash-object --no-filters "$LEGACY/.github/workflows/docs.yml")"
set +e
"$MIGRATE" --target-dir "$LEGACY" --apply --dry-run --json \
  > "$LEGACY/dry-run.json"
DRY_RC=$?
set -e
LEGACY_AFTER="$(git hash-object --no-filters "$LEGACY/mkdocs.yml") $(git hash-object --no-filters "$LEGACY/.github/workflows/docs.yml")"
if [ "$DRY_RC" -eq 10 ] && [ "$LEGACY_BEFORE" = "$LEGACY_AFTER" ]; then
  pass "migration dry-run is byte-preserving"
else
  fail "migration dry-run is byte-preserving"
fi

if "$MIGRATE" --target-dir "$LEGACY" --apply --verify --json \
  > "$LEGACY/apply.json"; then
  pass "migration applies recognized legacy changes"
else
  fail "migration applies recognized legacy changes"
fi
assert_contains "migration verification runs both strict passes" \
  "$LEGACY/apply.json" '"verified":true'
assert_contains "migration restores helper workflow" \
  "$LEGACY/.github/workflows/docs.yml" \
  "uv run python scripts/build-docs-site.py"
assert_contains "migration isolates snippets through staged docs" \
  "$LEGACY/mkdocs.yml" "MKDOCS_SITE_BOOTSTRAP_DOCS_DIR"

if "$MIGRATE" --target-dir "$LEGACY" --json > "$LEGACY/post-audit.json"; then
  pass "migration is idempotent on re-audit"
else
  fail "migration is idempotent on re-audit"
fi
assert_contains "post-migration audit is safe" "$LEGACY/post-audit.json" \
  '"status":"safe"'

if "$ADD_LANGUAGE" --target-dir "$LEGACY" --lang zh-TW \
  --keep-llmstxt --drop-strict > /dev/null 2> "$LEGACY/deprecated.log"; then
  pass "deprecated language flags remain compatible"
else
  fail "deprecated language flags remain compatible"
fi
assert_contains "drop-strict warns instead of weakening CI" \
  "$LEGACY/deprecated.log" "--drop-strict is now a no-op"

# A foreign same-named helper is never overwritten by conservative migration.
CUSTOM="$BASE/custom-helper"
run_init "$CUSTOM" --no-workflow >/dev/null
"$ADD_LANGUAGE" --target-dir "$CUSTOM" --lang zh-TW >/dev/null 2>&1
printf '#!/usr/bin/env python3\nprint("project owned")\n' \
  > "$CUSTOM/scripts/build-docs-site.py"
yq 'del(.plugins[] | select(has("llmstxt")) | .llmstxt.enabled)' \
  "$CUSTOM/mkdocs.yml" > "$CUSTOM/mkdocs.legacy"
mv "$CUSTOM/mkdocs.legacy" "$CUSTOM/mkdocs.yml"
set +e
"$MIGRATE" --target-dir "$CUSTOM" --apply --json > "$CUSTOM/apply.json"
CUSTOM_RC=$?
set -e
if [ "$CUSTOM_RC" -eq 11 ]; then
  pass "foreign helper collision requires manual migration"
else
  fail "foreign helper collision requires manual migration"
fi
assert_contains "foreign helper remains untouched" \
  "$CUSTOM/scripts/build-docs-site.py" 'print("project owned")'
assert_contains "collision is reported in manual actions" "$CUSTOM/apply.json" \
  "exists without the managed marker"

printf '\n%d passed, %d failed\n' "$PASS_COUNT" "$FAIL_COUNT"
[ "$FAIL_COUNT" -eq 0 ]
