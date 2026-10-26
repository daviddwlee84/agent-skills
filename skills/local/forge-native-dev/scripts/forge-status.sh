#!/usr/bin/env bash
set -euo pipefail

# Alignment dashboard: shows issue/branch/worktree/PR state at a glance.
#
# Compatibility: macOS system Bash 3.2+.

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

# shellcheck source=forge.sh
source "$SCRIPT_DIR/forge.sh"

FORGE_WORKTREE_ROOT="${FORGE_WORKTREE_ROOT:-.worktrees}"

usage() {
  cat <<'EOF'
Usage: forge-status.sh [OPTIONS]

Show the alignment of issues, branches, worktrees, and PRs.

Options:
  --json       Output as JSON array.
  --assigned   Only show issues assigned to you (default).
  --all        Show all open issues.
  -h, --help   Show this help and exit.
EOF
}

json_out=0
scope="assigned"

while [ $# -gt 0 ]; do
  case "$1" in
    -h|--help) usage; exit 0 ;;
    --json) json_out=1; shift ;;
    --assigned) scope="assigned"; shift ;;
    --all) scope="all"; shift ;;
    *) echo "Unknown argument: $1" >&2; usage >&2; exit 2 ;;
  esac
done

forge_detect
_forge_require_cli

repo_root="$(git rev-parse --show-toplevel)"
worktree_root="$repo_root/$FORGE_WORKTREE_ROOT"

# ---------------------------------------------------------------------------
# Section 1: Open issues and their branch/PR state
# ---------------------------------------------------------------------------

_forge_log "=== Forge Status Dashboard ==="
_forge_log "Forge: $FORGE_TYPE | CLI: $FORGE_CLI"
_forge_log ""

# Get open issues
_forge_log "--- Open Issues ---"
_forge_log ""

issue_args=""
if [ "$scope" = "assigned" ]; then
  issue_args="--assignee @me"
fi

case "$FORGE_TYPE" in
  github)
    if [ "$scope" = "assigned" ]; then
      issues_json="$(gh issue list --state open --assignee @me --json number,title,labels --limit 50 2>/dev/null || echo '[]')"
    else
      issues_json="$(gh issue list --state open --json number,title,labels --limit 50 2>/dev/null || echo '[]')"
    fi
    ;;
  gitlab)
    if [ "$scope" = "assigned" ]; then
      issues_json="$(glab issue list --opened --assignee @me --output json --per-page 50 2>/dev/null || echo '[]')"
    else
      issues_json="$(glab issue list --opened --output json --per-page 50 2>/dev/null || echo '[]')"
    fi
    ;;
esac

# Parse issue numbers and titles (simple extraction, no jq dependency)
issue_nums=""
if command -v jq >/dev/null 2>&1; then
  issue_nums="$(printf '%s' "$issues_json" | jq -r '.[].number // .[].iid' 2>/dev/null || true)"
else
  issue_nums="$(printf '%s' "$issues_json" | sed -n 's/.*"number":\([0-9]*\).*/\1/p' || true)"
  if [ -z "$issue_nums" ]; then
    issue_nums="$(printf '%s' "$issues_json" | sed -n 's/.*"iid":\([0-9]*\).*/\1/p' || true)"
  fi
fi

# Collect all issue branches
all_issue_branches="$(git branch --list "issue/*" "agent/issue/*" 2>/dev/null | sed 's/^[* ]*//' || true)"

# For each open issue, show its branch/worktree/PR
if [ -n "$issue_nums" ]; then
  printf '  %-6s  %-35s  %-35s  %-15s\n' "ISSUE" "TITLE" "BRANCH" "PR" >&2

  while IFS= read -r inum; do
    [ -z "$inum" ] && continue

    # Extract title
    local ititle=""
    if command -v jq >/dev/null 2>&1; then
      ititle="$(printf '%s' "$issues_json" | jq -r ".[] | select(.number == $inum or .iid == $inum) | .title" 2>/dev/null | head -1 || true)"
    fi
    if [ -z "$ititle" ]; then
      ititle="$(printf '%s' "$issues_json" | sed -n "/$inum/s/.*\"title\":\"\([^\"]*\)\".*/\1/p" | head -1 || true)"
    fi
    ititle="$(printf '%.35s' "${ititle:-?}")"

    # Find matching branch
    local ibranch="-"
    local match
    match="$(printf '%s' "$all_issue_branches" | grep "issue/${inum}-" | head -1 || true)"
    [ -n "$match" ] && ibranch="$match"

    # Find worktree
    if [ -d "$worktree_root/issue-${inum}" ]; then
      ibranch="${ibranch}"
    fi

    # Find PR
    local ipr="none"
    if [ "$ibranch" != "-" ]; then
      local pr_n
      pr_n="$(forge_pr_number "$ibranch" 2>/dev/null || true)"
      if [ -n "$pr_n" ] && [ "$pr_n" != "null" ]; then
        local pr_st
        pr_st="$(forge_pr_status "$ibranch" 2>/dev/null || true)"
        ipr="#${pr_n} (${pr_st})"
      fi
    fi

    printf '  #%-5s  %-35s  %-35s  %-15s\n' "$inum" "$ititle" "$ibranch" "$ipr"
  done <<EOF
$issue_nums
EOF
else
  _forge_log "  No open issues found${scope:+ (scope: $scope)}."
fi

# ---------------------------------------------------------------------------
# Section 2: Orphaned branches (no open issue)
# ---------------------------------------------------------------------------

_forge_log ""
_forge_log "--- Orphaned Branches (no matching open issue) ---"
_forge_log ""

orphan_count=0
if [ -n "$all_issue_branches" ]; then
  while IFS= read -r branch; do
    [ -z "$branch" ] && continue

    local bnum
    bnum="$(_forge_issue_from_branch "$branch" 2>/dev/null || true)"
    [ -z "$bnum" ] && continue

    # Check if this issue number is in the open issues list
    local is_open=0
    if printf '%s' "$issue_nums" | grep -qxF "$bnum" 2>/dev/null; then
      is_open=1
    fi

    if [ "$is_open" -eq 0 ]; then
      orphan_count=$(( orphan_count + 1 ))
      local pr_info="none"
      local pr_n
      pr_n="$(forge_pr_number "$branch" 2>/dev/null || true)"
      if [ -n "$pr_n" ] && [ "$pr_n" != "null" ]; then
        local pr_st
        pr_st="$(forge_pr_status "$branch" 2>/dev/null || true)"
        pr_info="#${pr_n} (${pr_st})"
      fi
      printf '  %-40s  issue #%-6s  PR: %s\n' "$branch" "$bnum" "$pr_info"
    fi
  done <<EOF
$all_issue_branches
EOF
fi

if [ "$orphan_count" -eq 0 ]; then
  _forge_log "  No orphaned branches."
fi

# ---------------------------------------------------------------------------
# Section 3: Worktrees
# ---------------------------------------------------------------------------

_forge_log ""
_forge_log "--- Worktrees ---"
_forge_log ""

if [ -d "$worktree_root" ]; then
  local wt_count=0
  for wt_dir in "$worktree_root"/issue-*/; do
    [ -d "$wt_dir" ] || continue
    wt_count=$(( wt_count + 1 ))

    local wt_name
    wt_name="$(basename "$wt_dir")"
    local wt_issue
    wt_issue="$(printf '%s' "$wt_name" | sed 's/^issue-//')"

    # Find branch in this worktree
    local wt_branch
    wt_branch="$(git -C "$wt_dir" rev-parse --abbrev-ref HEAD 2>/dev/null || echo '?')"

    printf '  %-30s  -> %-35s  (issue #%s)\n' "$FORGE_WORKTREE_ROOT/$wt_name/" "$wt_branch" "$wt_issue"
  done

  if [ "$wt_count" -eq 0 ]; then
    _forge_log "  No active worktrees."
  fi
else
  _forge_log "  No worktree directory ($FORGE_WORKTREE_ROOT/)."
fi

_forge_log ""
_forge_log "Tip: run forge-cleanup.sh to remove merged branches + worktrees."
