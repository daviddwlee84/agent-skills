#!/usr/bin/env bash
# new-bundle.sh — create an evidence bundle keyed to the current agent
# session + git branch/commit, and guarantee the evidence root is gitignored.
#
# Layout: <root>/<agent>-<short-session>/<UTC-ts>-<shortSHA>[-<title>]/
# Writes manifest.json (machine-readable) + MANIFEST.md (scaffold) and a
# <root>/.current pointer that capture.sh reads by default.
#
# Bash 3.2 compatible (stock macOS).

set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

usage() {
  cat <<'EOF'
Usage: new-bundle.sh [OPTIONS]

Create a fresh evidence bundle under the (gitignored) evidence root and print
its path as JSON. Records git branch/short-SHA/dirty + the detected coding
agent session inside the bundle's manifest.json.

Options:
  --title SLUG      Short title appended to the bundle dir name + manifest.
  --feature TEXT    One-line description of the feature under review.
  --agent VALUE     Force agent kind (claude|cursor|codex|...); else detected.
  --root DIR        Evidence root (default: .evidence, at the repo top level).
  --dry-run         Print what would be created; write nothing.
  --help, -h        Show this help and exit.

Output (JSON on stdout):
  {"bundle_dir","manifest","agent","session","branch","sha","dirty"}

Exit codes:
  0  success
  1  invalid arguments
  2  not inside a git repo
  3  required tool missing (jq)
EOF
}

log()  { printf '%s\n' "$*" >&2; }
warn() { printf 'warn: %s\n' "$*" >&2; }
die()  { printf 'error: %s\n' "$*" >&2; exit "${2:-1}"; }

TITLE=""
FEATURE=""
AGENT_OVERRIDE=""
ROOT=".evidence"
DRY_RUN=0

while [ $# -gt 0 ]; do
  case "$1" in
    --title=*)   TITLE="${1#--title=}"; shift ;;
    --title)     TITLE="${2:-}"; shift 2 ;;
    --feature=*) FEATURE="${1#--feature=}"; shift ;;
    --feature)   FEATURE="${2:-}"; shift 2 ;;
    --agent=*)   AGENT_OVERRIDE="${1#--agent=}"; shift ;;
    --agent)     AGENT_OVERRIDE="${2:-}"; shift 2 ;;
    --root=*)    ROOT="${1#--root=}"; shift ;;
    --root)      ROOT="${2:-}"; shift 2 ;;
    --dry-run)   DRY_RUN=1; shift ;;
    --help|-h)   usage; exit 0 ;;
    -*)          die "unknown flag: $1 (try --help)" 1 ;;
    *)           die "unexpected positional arg: $1 (try --help)" 1 ;;
  esac
done

command -v jq >/dev/null 2>&1 || die "jq not found in PATH (install: brew install jq)" 3

# --- Anchor at repo top level (idiom: stage-agent-artifacts.sh) -----------
git rev-parse --show-toplevel >/dev/null 2>&1 || die "not inside a git repo" 2
REPO_ROOT="$(git rev-parse --show-toplevel)"
cd "$REPO_ROOT"

BRANCH="$(git rev-parse --abbrev-ref HEAD 2>/dev/null || echo HEAD)"
SHA="$(git rev-parse --short HEAD 2>/dev/null || echo nocommit)"
if [ -n "$(git status --porcelain 2>/dev/null)" ]; then DIRTY=true; else DIRTY=false; fi

# --- Detect agent + session via sibling script ----------------------------
SESS_TSV="$("$HERE/detect-session.sh" --tsv ${AGENT_OVERRIDE:+--agent "$AGENT_OVERRIDE"} --quiet || true)"
val() { printf '%s\n' "$SESS_TSV" | awk -F'\t' -v k="$1" '$1==k{print $2}'; }
AGENT="$(val agent)";          [ -n "$AGENT" ] || AGENT="unknown"
SESSION_ID="$(val session_id)"; [ -n "$SESSION_ID" ] || SESSION_ID="nosession"
SESSION_SOURCE="$(val source)"; [ -n "$SESSION_SOURCE" ] || SESSION_SOURCE="none"
SPECSTORY_PATH="$(val specstory_path)"

# --- Compute slugs + paths -------------------------------------------------
slugify() {
  printf '%s' "$1" | tr '[:upper:]' '[:lower:]' \
    | sed -E 's/[^a-z0-9]+/-/g; s/^-+//; s/-+$//' | cut -c1-40
}
short_session() {
  # UUID → first 8 hex; timestamp/other → as-is.
  if printf '%s' "$1" | grep -Eq '^[0-9a-f]{8}-[0-9a-f]{4}'; then
    printf '%s' "$1" | cut -c1-8
  else
    printf '%s' "$1"
  fi
}

TS_DIR="$(date -u +%Y-%m-%dT%H-%M-%SZ)"    # colon-free, filename-safe
TS_ISO="$(date -u +%Y-%m-%dT%H:%M:%SZ)"    # ISO for the manifest
SESSION_DIR="$(slugify "$AGENT")-$(short_session "$SESSION_ID")"
BUNDLE_NAME="$TS_DIR-$SHA"
[ -n "$TITLE" ] && BUNDLE_NAME="$BUNDLE_NAME-$(slugify "$TITLE")"
BUNDLE_DIR="$ROOT/$SESSION_DIR/$BUNDLE_NAME"
MANIFEST="$BUNDLE_DIR/manifest.json"

if [ "$DRY_RUN" = "1" ]; then
  log "[dry-run] would create bundle: $BUNDLE_DIR"
  log "[dry-run] agent=$AGENT session=$SESSION_ID branch=$BRANCH sha=$SHA dirty=$DIRTY"
  printf '{"bundle_dir":"%s","manifest":"%s","agent":"%s","session":"%s","branch":"%s","sha":"%s","dirty":%s,"dry_run":true}\n' \
    "$BUNDLE_DIR" "$MANIFEST" "$AGENT" "$SESSION_ID" "$BRANCH" "$SHA" "$DIRTY"
  exit 0
fi

# --- Guarantee the evidence root is gitignored ----------------------------
# Idiomatic: a root-anchored entry in the repo's .gitignore (cf. /site, /state/).
ROOT_CLEAN="${ROOT#./}"
IGNORE_LINE="/$ROOT_CLEAN/"
if ! grep -qxF "$IGNORE_LINE" .gitignore 2>/dev/null; then
  { printf '\n# demo-evidence: local acceptance artifacts (never committed)\n%s\n' "$IGNORE_LINE"; } >> .gitignore
  log "added '$IGNORE_LINE' to .gitignore"
fi

mkdir -p "$BUNDLE_DIR"
if ! git check-ignore -q "$BUNDLE_DIR" 2>/dev/null; then
  warn "$BUNDLE_DIR is NOT gitignored — check your .gitignore before committing"
fi

# --- Write manifest.json ---------------------------------------------------
jq -n \
  --arg created "$TS_ISO" \
  --arg agent   "$AGENT" \
  --arg sid     "$SESSION_ID" \
  --arg ssrc    "$SESSION_SOURCE" \
  --arg spath   "$SPECSTORY_PATH" \
  --arg branch  "$BRANCH" \
  --arg sha     "$SHA" \
  --argjson dirty "$DIRTY" \
  --arg title   "$TITLE" \
  --arg feature "$FEATURE" \
  '{schema:1, created_utc:$created, agent:$agent,
    session:{id:$sid, source:$ssrc, specstory_path:$spath},
    git:{branch:$branch, sha:$sha, dirty:$dirty},
    title:$title, feature:$feature, verdict:"pending",
    steps:[], artifacts:[]}' > "$MANIFEST"

# --- Write a MANIFEST.md scaffold (finalize.sh renders the real one) ------
# Note: printf format strings that begin with '-' must use `printf --`.
{
  printf '# Evidence: %s\n\n' "${TITLE:-$BUNDLE_NAME}"
  printf '> **verdict: pending** — run `finalize.sh --bundle %s --verdict PASS|NEEDS_WORK` when done.\n\n' "$BUNDLE_DIR"
  printf -- '- agent/session: `%s` / `%s`\n' "$AGENT" "$SESSION_ID"
  printf -- '- git: `%s` @ `%s` (dirty: %s)\n' "$BRANCH" "$SHA" "$DIRTY"
  printf -- '- created: `%s`\n\n' "$TS_ISO"
  [ -n "$FEATURE" ] && printf '%s\n\n' "$FEATURE"
  printf '_No artifacts captured yet._\n'
} > "$BUNDLE_DIR/MANIFEST.md"

# --- Update the .current pointer (default target for capture.sh) ----------
printf '%s\n' "$BUNDLE_DIR" > "$ROOT/.current"

log "created bundle: $BUNDLE_DIR"
printf '{"bundle_dir":"%s","manifest":"%s","agent":"%s","session":"%s","branch":"%s","sha":"%s","dirty":%s}\n' \
  "$BUNDLE_DIR" "$MANIFEST" "$AGENT" "$SESSION_ID" "$BRANCH" "$SHA" "$DIRTY"
