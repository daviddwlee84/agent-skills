#!/usr/bin/env bash
set -euo pipefail

# Auto-cleanup branches and worktrees whose PRs have been merged.
# Scans issue/* and agent/issue/* branches, checks PR status, and removes
# merged branches + their worktrees with confirmation.
#
# Compatibility: macOS system Bash 3.2+.

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

# shellcheck source=forge.sh
source "$SCRIPT_DIR/forge.sh"

FORGE_WORKTREE_ROOT="${FORGE_WORKTREE_ROOT:-.worktrees}"

usage() {
  cat <<'EOF'
Usage: forge-cleanup.sh [OPTIONS]

Scan issue branches for merged PRs and clean up branches + worktrees.

Options:
  --dry-run    Show what would be cleaned without doing it.
  --force      Skip confirmation prompts.
  --all        Also clean branches with closed (not merged) PRs.
  -h, --help   Show this help and exit.
EOF
}

dry_run=0
force=0
include_closed=0

while [ $# -gt 0 ]; do
  case "$1" in
    -h|--help) usage; exit 0 ;;
    --dry-run) dry_run=1; shift ;;
    --force) force=1; shift ;;
    --all) include_closed=1; shift ;;
    *) echo "Unknown argument: $1" >&2; usage >&2; exit 2 ;;
  esac
done

forge_detect
_forge_require_cli

repo_root="$(git rev-parse --show-toplevel)"
worktree_root="$repo_root/$FORGE_WORKTREE_ROOT"

# Fetch + prune to get accurate upstream state
_forge_log "Fetching and pruning remote refs..."
git fetch --prune 2>/dev/null || true

# Collect candidates
branches="$(git branch --list "issue/*" "agent/issue/*" 2>/dev/null | sed 's/^[* ]*//' || true)"

if [ -z "$branches" ]; then
  _forge_log "No issue branches found. Nothing to clean."
  exit 0
fi

# Track what we'll clean
to_clean=""
clean_count=0

_forge_log ""
_forge_log "Scanning branches for merged PRs..."
_forge_log ""

while IFS= read -r branch; do
  [ -z "$branch" ] && continue

  local_issue="$(_forge_issue_from_branch "$branch" 2>/dev/null || true)"
  pr_st="$(forge_pr_status "$branch" 2>/dev/null || true)"
  pr_n="$(forge_pr_number "$branch" 2>/dev/null || true)"

  should_clean=0
  reason=""

  case "$pr_st" in
    merged)
      should_clean=1
      reason="PR #${pr_n} merged"
      ;;
    closed)
      if [ "$include_closed" -eq 1 ]; then
        should_clean=1
        reason="PR #${pr_n} closed (not merged)"
      fi
      ;;
    none)
      # Check if upstream branch is gone (squash-merged without forge tracking)
      local upstream
      upstream="$(git for-each-ref --format='%(upstream:short)' "refs/heads/$branch" 2>/dev/null || true)"
      if [ -n "$upstream" ] && ! git show-ref --verify --quiet "refs/remotes/$upstream" 2>/dev/null; then
        should_clean=1
        reason="upstream gone (likely squash-merged)"
      fi
      ;;
  esac

  if [ "$should_clean" -eq 1 ]; then
    clean_count=$(( clean_count + 1 ))

    # Check for associated worktree
    local wt_path=""
    if [ -n "$local_issue" ] && [ -d "$worktree_root/issue-${local_issue}" ]; then
      wt_path="$FORGE_WORKTREE_ROOT/issue-${local_issue}/"
    fi

    printf '  %-40s  %s' "$branch" "$reason" >&2
    [ -n "$wt_path" ] && printf '  (worktree: %s)' "$wt_path" >&2
    printf '\n' >&2

    to_clean="${to_clean}${branch}|${local_issue}|${wt_path}
"
  fi
done <<EOF
$branches
EOF

if [ "$clean_count" -eq 0 ]; then
  _forge_log "No branches ready for cleanup."
  exit 0
fi

_forge_log ""
_forge_log "Found $clean_count branch(es) ready to clean."

if [ "$dry_run" -eq 1 ]; then
  _forge_log "(dry-run mode — no changes made)"
  exit 0
fi

# Confirm
if [ "$force" -eq 0 ]; then
  printf '\nProceed with cleanup? [y/N] ' >&2
  read -r confirm
  case "$confirm" in
    y|Y|yes|YES) ;;
    *) _forge_log "Aborted."; exit 0 ;;
  esac
fi

# Execute cleanup
_forge_log ""
_forge_log "Cleaning up..."

cleaned=0
while IFS='|' read -r branch issue_n wt_path; do
  [ -z "$branch" ] && continue

  # Remove worktree first (if exists)
  if [ -n "$wt_path" ]; then
    local full_wt="$repo_root/$wt_path"
    if [ -d "$full_wt" ]; then
      _forge_log "  Removing worktree: $wt_path"
      git worktree remove "$full_wt" --force 2>/dev/null || {
        _forge_warn "Failed to remove worktree $wt_path — remove manually"
      }
    fi
  fi

  # Delete local branch
  _forge_log "  Deleting branch: $branch"
  git branch -D "$branch" 2>/dev/null || {
    _forge_warn "Failed to delete branch $branch"
  }

  cleaned=$(( cleaned + 1 ))
done <<EOF
$to_clean
EOF

_forge_log ""
_forge_log "Cleaned $cleaned branch(es)."

# Prune worktree metadata
git worktree prune 2>/dev/null || true
