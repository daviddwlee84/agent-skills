#!/usr/bin/env bash
# branch-status.sh — classify local git branches as active/merged/gone/stale.
#
# Bash 3.2 compatible (works on stock macOS).

set -euo pipefail

usage() {
  cat <<'EOF'
Usage: branch-status.sh [OPTIONS]

Classify every local branch relative to the repo's default (base) branch, to
answer "which branches are still in-dev vs already merged/gone?". Read-only:
never creates, deletes, or fetches. For the freshest `gone` detection, run
`git fetch --prune` yourself first.

States:
  base    the default branch itself
  active  has commits ahead of base, upstream still present
  merged  fully contained in base (safe to delete with `git branch -d`)
  gone    upstream branch deleted (e.g. after a squash-merged PR) — verify,
          then `git branch -D`
  stale   no commits within --stale-days (default 30)

Output (stdout): TSV `branch<TAB>state<TAB>ahead<TAB>upstream<TAB>pr`
(column header goes to stderr so stdout stays machine-parseable).
The `pr` column is `merged`/`none` when a forge CLI (`gh` for GitHub) can be
queried, else `-`. GitLab remotes fall back to git-only classification.

Options:
  --json             Emit one JSON object per branch instead of TSV.
  --stale-days N     Days without a commit before a branch is "stale" (default 30).
  --help, -h         Show this help and exit.

Examples:
  branch-status.sh
  git fetch --prune && branch-status.sh --json
  branch-status.sh --stale-days 14

Exit codes:
  0  success (branch state is data, not an error condition)
  1  invalid arguments
  2  not a git repository
EOF
}

# Logging: data → stdout, diagnostics → stderr.
log()  { printf '%s\n' "$*" >&2; }
warn() { printf 'warn: %s\n' "$*" >&2; }
die()  { printf 'error: %s\n' "$1" >&2; exit "${2:-1}"; }

JSON=0
STALE_DAYS=30

while [ $# -gt 0 ]; do
  case "$1" in
    --json) JSON=1; shift ;;
    --stale-days)
      shift
      [ $# -gt 0 ] || die "--stale-days needs a number (try --help)" 1
      case "$1" in
        ''|*[!0-9]*) die "--stale-days must be a non-negative integer, got: $1" 1 ;;
      esac
      STALE_DAYS="$1"; shift ;;
    --help|-h) usage; exit 0 ;;
    -*) die "unknown flag: $1 (try --help)" 1 ;;
    *)  die "unexpected argument: $1 (try --help)" 1 ;;
  esac
done

git rev-parse --is-inside-work-tree >/dev/null 2>&1 \
  || die "not a git repository (run inside a repo)" 2

# JSON string escaper (backslash + double-quote; branch names rarely need more).
json_escape() {
  printf '%s' "$1" | sed 's/\\/\\\\/g; s/"/\\"/g'
}

# --- resolve the base (default) branch --------------------------------------
base="$(git symbolic-ref --quiet --short refs/remotes/origin/HEAD 2>/dev/null | sed 's#^origin/##' || true)"
if [ -z "$base" ]; then
  for cand in main master; do
    if git show-ref --verify --quiet "refs/heads/$cand"; then base="$cand"; break; fi
  done
fi
[ -n "$base" ] || base="$(git rev-parse --abbrev-ref HEAD 2>/dev/null || echo HEAD)"

# --- best-effort merged-PR head branches (GitHub via gh) --------------------
MERGED_PRS=""
origin_url="$(git remote get-url origin 2>/dev/null || true)"
case "$origin_url" in
  *github.com*)
    if command -v gh >/dev/null 2>&1; then
      MERGED_PRS="$(gh pr list --state merged --limit 200 --json headRefName -q '.[].headRefName' 2>/dev/null || true)"
    fi ;;
  *gitlab*)
    if command -v glab >/dev/null 2>&1; then
      warn "glab detected — PR-state enrichment not wired for GitLab; using git-only classification"
    fi ;;
esac

now="$(date +%s)"
stale_secs=$(( STALE_DAYS * 86400 ))

[ "$JSON" = "1" ] || log "branch	state	ahead	upstream	pr"

# --- classify each local branch ---------------------------------------------
# Use a non-whitespace separator (0x1f): with a whitespace IFS like tab, empty
# fields (e.g. a branch with no upstream) would collapse and shift columns.
SEP=$(printf '\037')
git for-each-ref \
  --format="%(refname:short)${SEP}%(upstream:short)${SEP}%(upstream:track)${SEP}%(committerdate:unix)" \
  refs/heads/ | while IFS="$SEP" read -r name upstream track cdate; do

  [ -n "$name" ] || continue

  ahead="$(git rev-list --count "$base..$name" 2>/dev/null || echo 0)"

  # stale?
  is_stale=0
  if [ -n "$cdate" ] && [ $(( now - cdate )) -gt "$stale_secs" ]; then
    is_stale=1
  fi

  if [ "$name" = "$base" ]; then
    state="base"
  elif printf '%s' "$track" | grep -q 'gone'; then
    state="gone"
  elif git merge-base --is-ancestor "$name" "$base" 2>/dev/null; then
    state="merged"
  elif [ "$is_stale" = "1" ]; then
    state="stale"
  else
    state="active"
  fi

  # pr enrichment
  pr="-"
  if [ -n "$MERGED_PRS" ]; then
    if printf '%s\n' "$MERGED_PRS" | grep -qxF "$name"; then pr="merged"; else pr="none"; fi
  fi

  up="${upstream:--}"

  if [ "$JSON" = "1" ]; then
    printf '{"branch":"%s","state":"%s","ahead":%s,"upstream":"%s","pr":"%s"}\n' \
      "$(json_escape "$name")" "$state" "${ahead:-0}" "$(json_escape "$up")" "$pr"
  else
    printf '%s\t%s\t%s\t%s\t%s\n' "$name" "$state" "${ahead:-0}" "$up" "$pr"
  fi
done
