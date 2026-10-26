#!/usr/bin/env bash
set -euo pipefail

# Worktree-per-issue lifecycle manager.
# Subcommands: start, finish, list
#
# start <issue-number> — create branch + worktree for an issue
# finish <issue-number> — push branch, create PR linking to issue
# list — show active worktree/issue/PR alignment
#
# Compatibility: macOS system Bash 3.2+.

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

# shellcheck source=forge.sh
source "$SCRIPT_DIR/forge.sh"

# Configurable worktree root (relative to repo root).
FORGE_WORKTREE_ROOT="${FORGE_WORKTREE_ROOT:-.worktrees}"

usage() {
  cat <<'EOF'
Usage: forge-worktree.sh <subcommand> [args]

Subcommands:
  start <issue-number>    Create a branch + worktree for the issue.
                          Branch: issue/<number>-<slug>
                          Worktree: .worktrees/issue-<number>/
  finish <issue-number>   Push the branch and create a PR linking to the issue.
  list                    Show active issue worktrees with PR status.

Options:
  --agent                 Use agent/ prefix for the branch (agent/issue/<n>-<slug>).
  --base BRANCH           Base branch to create from (default: auto-detected).
  --draft                 Create PR as draft (finish only).
  -h, --help              Show this help and exit.

Environment:
  FORGE_WORKTREE_ROOT     Worktree directory (default: .worktrees).
EOF
}

subcmd=""
issue_num=""
agent_prefix=0
base_branch=""
draft=0

# Parse global options first, then subcommand
while [ $# -gt 0 ]; do
  case "$1" in
    -h|--help) usage; exit 0 ;;
    --agent) agent_prefix=1; shift ;;
    --base) base_branch="$2"; shift 2 ;;
    --draft) draft=1; shift ;;
    start|finish|list)
      subcmd="$1"; shift
      break
      ;;
    *)
      # Could be a subcommand with args mixed in
      echo "Unknown argument: $1" >&2; usage >&2; exit 2
      ;;
  esac
done

# Remaining args after subcommand
while [ $# -gt 0 ]; do
  case "$1" in
    --agent) agent_prefix=1; shift ;;
    --base) base_branch="$2"; shift 2 ;;
    --draft) draft=1; shift ;;
    [0-9]*)
      issue_num="$1"; shift
      ;;
    *)
      echo "Unknown argument: $1" >&2; usage >&2; exit 2
      ;;
  esac
done

[ -z "$subcmd" ] && { usage; exit 1; }

# Ensure we're in a git repo and detect the forge
forge_detect
_forge_require_cli

# Resolve repo root
repo_root="$(git rev-parse --show-toplevel)"
worktree_root="$repo_root/$FORGE_WORKTREE_ROOT"

# Resolve base branch
[ -z "$base_branch" ] && base_branch="$(forge_default_branch)"

# ---------------------------------------------------------------------------
# start
# ---------------------------------------------------------------------------

cmd_start() {
  [ -z "$issue_num" ] && _forge_die "start requires an issue number" 1

  _forge_log "Fetching issue #$issue_num..."
  local issue_json
  issue_json="$(forge_issue_view "$issue_num" --json)"

  # Extract title for slug
  local issue_title
  case "$FORGE_TYPE" in
    github)
      issue_title="$(printf '%s' "$issue_json" | sed -n 's/.*"title":"\([^"]*\)".*/\1/p' | head -1)"
      ;;
    gitlab)
      issue_title="$(printf '%s' "$issue_json" | sed -n 's/.*"title":"\([^"]*\)".*/\1/p' | head -1)"
      ;;
  esac

  if [ -z "$issue_title" ]; then
    _forge_warn "could not extract issue title; using issue number only"
    issue_title="issue-$issue_num"
  fi

  local slug
  slug="$(forge_slugify "$issue_title")"

  local branch_name
  if [ "$agent_prefix" -eq 1 ]; then
    branch_name="agent/issue/${issue_num}-${slug}"
  else
    branch_name="issue/${issue_num}-${slug}"
  fi

  local worktree_path="$worktree_root/issue-${issue_num}"

  # Check if branch already exists
  if git show-ref --verify --quiet "refs/heads/$branch_name" 2>/dev/null; then
    _forge_log "Branch $branch_name already exists."

    # Check if worktree exists
    if [ -d "$worktree_path" ]; then
      _forge_log "Worktree already exists at $worktree_path"
      _forge_log ""
      _forge_log "To resume work:"
      _forge_log "  cd $worktree_path"
      return 0
    else
      _forge_log "Creating worktree for existing branch..."
      git worktree add "$worktree_path" "$branch_name"
    fi
  else
    # Create branch from base
    _forge_log "Creating branch $branch_name from $base_branch..."
    git fetch origin "$base_branch" 2>/dev/null || true
    git branch "$branch_name" "origin/$base_branch" 2>/dev/null \
      || git branch "$branch_name" "$base_branch"

    # Create worktree
    mkdir -p "$(dirname "$worktree_path")"
    git worktree add "$worktree_path" "$branch_name"
  fi

  # Assign the issue and label it
  _forge_log "Assigning issue #$issue_num and adding 'in-progress' label..."
  forge_issue_assign "$issue_num" "@me" 2>/dev/null || true
  forge_issue_label "$issue_num" --add "in-progress" 2>/dev/null || true

  _forge_log ""
  _forge_log "=== Worktree ready ==="
  _forge_log "Issue:    #$issue_num — $issue_title"
  _forge_log "Branch:   $branch_name"
  _forge_log "Worktree: $worktree_path"
  _forge_log ""
  _forge_log "To start working:"
  _forge_log "  cd $worktree_path"
}

# ---------------------------------------------------------------------------
# finish
# ---------------------------------------------------------------------------

cmd_finish() {
  [ -z "$issue_num" ] && _forge_die "finish requires an issue number" 1

  # Find the branch for this issue
  local branch_name=""
  local branches
  branches="$(git branch --list "issue/${issue_num}-*" "agent/issue/${issue_num}-*" 2>/dev/null | sed 's/^[* ]*//')"

  local count
  count="$(printf '%s' "$branches" | grep -c . || true)"

  if [ "$count" -eq 0 ]; then
    _forge_die "no branch found for issue #$issue_num (expected issue/${issue_num}-* or agent/issue/${issue_num}-*)" 1
  elif [ "$count" -eq 1 ]; then
    branch_name="$(printf '%s' "$branches" | head -1)"
  else
    _forge_die "multiple branches found for issue #$issue_num:\n$branches\nPlease resolve manually." 1
  fi

  _forge_log "Finishing issue #$issue_num (branch: $branch_name)..."

  # Push the branch
  _forge_log "Pushing branch..."
  git push -u origin "$branch_name" 2>/dev/null || git push origin "$branch_name"

  # Check for existing PR
  local existing_pr
  existing_pr="$(forge_pr_number "$branch_name")"

  if [ -n "$existing_pr" ] && [ "$existing_pr" != "null" ]; then
    _forge_log "PR #$existing_pr already exists for this branch."
    _forge_log ""
    case "$FORGE_TYPE" in
      github) _forge_log "View: gh pr view $existing_pr --web" ;;
      gitlab) _forge_log "View: glab mr view $existing_pr --web" ;;
    esac
    return 0
  fi

  # Get issue title for PR title
  local issue_title=""
  local issue_json
  issue_json="$(forge_issue_view "$issue_num" --json 2>/dev/null || true)"
  if [ -n "$issue_json" ]; then
    issue_title="$(printf '%s' "$issue_json" | sed -n 's/.*"title":"\([^"]*\)".*/\1/p' | head -1)"
  fi

  local pr_title="${issue_title:-Issue #$issue_num}"
  local pr_body="Closes #${issue_num}"

  # Create PR
  _forge_log "Creating PR..."
  local pr_args="--title $(printf '%q' "$pr_title") --body $(printf '%q' "$pr_body") --base $(printf '%q' "$base_branch")"
  if [ "$draft" -eq 1 ]; then
    forge_pr_create --title "$pr_title" --body "$pr_body" --base "$base_branch" --draft
  else
    forge_pr_create --title "$pr_title" --body "$pr_body" --base "$base_branch"
  fi

  _forge_log ""
  _forge_log "=== PR created ==="
  _forge_log "Issue:  #$issue_num"
  _forge_log "Branch: $branch_name"
  _forge_log ""
  _forge_log "After the PR is merged, run:"
  _forge_log "  forge-cleanup.sh"
}

# ---------------------------------------------------------------------------
# list
# ---------------------------------------------------------------------------

cmd_list() {
  _forge_log "=== Active Issue Worktrees ==="
  _forge_log ""

  # Find all issue-related branches
  local branches
  branches="$(git branch --list "issue/*" "agent/issue/*" 2>/dev/null | sed 's/^[* ]*//' || true)"

  if [ -z "$branches" ]; then
    _forge_log "No issue branches found."
    return 0
  fi

  printf '%-8s  %-40s  %-30s  %-12s\n' "ISSUE" "BRANCH" "WORKTREE" "PR" >&2

  local branch
  while IFS= read -r branch; do
    [ -z "$branch" ] && continue

    local issue_n
    issue_n="$(_forge_issue_from_branch "$branch" 2>/dev/null || true)"
    [ -z "$issue_n" ] && issue_n="?"

    # Check worktree
    local wt_path="-"
    local wt_dir="$worktree_root/issue-${issue_n}"
    if [ -d "$wt_dir" ]; then
      wt_path="$FORGE_WORKTREE_ROOT/issue-${issue_n}/"
    fi

    # Check PR
    local pr_info="none"
    local pr_n
    pr_n="$(forge_pr_number "$branch" 2>/dev/null || true)"
    if [ -n "$pr_n" ] && [ "$pr_n" != "null" ]; then
      local pr_st
      pr_st="$(forge_pr_status "$branch" 2>/dev/null || true)"
      pr_info="#${pr_n} (${pr_st})"
    fi

    printf '%-8s  %-40s  %-30s  %-12s\n' "#$issue_n" "$branch" "$wt_path" "$pr_info"
  done <<EOF
$branches
EOF
}

# ---------------------------------------------------------------------------
# Dispatch
# ---------------------------------------------------------------------------

case "$subcmd" in
  start)  cmd_start ;;
  finish) cmd_finish ;;
  list)   cmd_list ;;
  *)      usage; exit 1 ;;
esac
