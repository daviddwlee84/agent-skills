# shellcheck shell=bash
# Forge abstraction library — sourced by other scripts, not executed directly.
# Provides a unified interface over GitHub (gh) and GitLab (glab) CLIs.
# Compatibility: macOS system Bash 3.2+.
#
# Usage:
#   source "$(dirname "$0")/forge.sh"
#   forge_detect          # sets FORGE_TYPE and FORGE_CLI
#   forge_issue_create --title "Bug" --body "Details" --label "type/bug"

# Guard against double-sourcing.
[ -n "${_FORGE_LIB_LOADED:-}" ] && return 0
_FORGE_LIB_LOADED=1

# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

_forge_log()  { printf '%s\n' "$*" >&2; }
_forge_warn() { printf 'forge: warn: %s\n' "$*" >&2; }
_forge_die()  { printf 'forge: error: %s\n' "$1" >&2; exit "${2:-1}"; }

_forge_require_detected() {
  if [ -z "${FORGE_TYPE:-}" ]; then
    _forge_die "forge not detected yet — call forge_detect first" 1
  fi
}

# ---------------------------------------------------------------------------
# Detection
# ---------------------------------------------------------------------------

# FORGE_TYPE: "github" | "gitlab" | "unknown"
# FORGE_CLI:  "gh" | "glab" | ""
# FORGE_REMOTE_URL: the origin URL
FORGE_TYPE=""
FORGE_CLI=""
FORGE_REMOTE_URL=""

forge_detect() {
  git rev-parse --is-inside-work-tree >/dev/null 2>&1 \
    || _forge_die "not inside a git repository" 2

  FORGE_REMOTE_URL="$(git remote get-url origin 2>/dev/null || true)"
  if [ -z "$FORGE_REMOTE_URL" ]; then
    _forge_warn "no 'origin' remote found"
    FORGE_TYPE="unknown"
    FORGE_CLI=""
    return 0
  fi

  case "$FORGE_REMOTE_URL" in
    *github.com*|*github.com:*)
      FORGE_TYPE="github"
      if command -v gh >/dev/null 2>&1; then
        FORGE_CLI="gh"
      else
        _forge_warn "GitHub remote detected but 'gh' CLI not found — install: brew install gh"
        FORGE_CLI=""
      fi
      ;;
    *gitlab.com*|*gitlab.com:*|*gitlab.*)
      FORGE_TYPE="gitlab"
      if command -v glab >/dev/null 2>&1; then
        FORGE_CLI="glab"
      else
        _forge_warn "GitLab remote detected but 'glab' CLI not found — install: brew install glab"
        FORGE_CLI=""
      fi
      ;;
    *)
      FORGE_TYPE="unknown"
      FORGE_CLI=""
      _forge_warn "remote URL does not match GitHub or GitLab: $FORGE_REMOTE_URL"
      ;;
  esac

  if [ -n "$FORGE_CLI" ]; then
    _forge_log "forge: detected $FORGE_TYPE (CLI: $FORGE_CLI)"
  fi
  return 0
}

# Require the CLI to be available (call after forge_detect).
_forge_require_cli() {
  _forge_require_detected
  if [ -z "$FORGE_CLI" ]; then
    _forge_die "$FORGE_TYPE remote detected but no CLI available (need ${FORGE_TYPE} CLI)" 1
  fi
}

# ---------------------------------------------------------------------------
# Labels
# ---------------------------------------------------------------------------

forge_label_ensure() {
  _forge_require_cli
  local name="$1"
  local color="${2:-}"
  local description="${3:-}"

  case "$FORGE_TYPE" in
    github)
      if gh label list --json name -q ".[].name" 2>/dev/null | grep -qxF "$name"; then
        return 0
      fi
      local cmd="gh label create $(printf '%q' "$name")"
      [ -n "$color" ] && cmd="$cmd --color $(printf '%q' "$color")"
      [ -n "$description" ] && cmd="$cmd --description $(printf '%q' "$description")"
      eval "$cmd" 2>/dev/null || _forge_warn "failed to create label: $name"
      ;;
    gitlab)
      if glab label list 2>/dev/null | grep -qF "$name"; then
        return 0
      fi
      local cmd="glab label create $(printf '%q' "$name")"
      [ -n "$color" ] && cmd="$cmd --color $(printf '%q' "#${color#\#}")"
      [ -n "$description" ] && cmd="$cmd --description $(printf '%q' "$description")"
      eval "$cmd" 2>/dev/null || _forge_warn "failed to create label: $name"
      ;;
  esac
}

# ---------------------------------------------------------------------------
# Issues
# ---------------------------------------------------------------------------

forge_issue_create() {
  _forge_require_cli
  local title="" body="" labels="" assignee=""
  while [ $# -gt 0 ]; do
    case "$1" in
      --title) title="$2"; shift 2 ;;
      --body) body="$2"; shift 2 ;;
      --label) labels="${labels:+$labels,}$2"; shift 2 ;;
      --assignee) assignee="$2"; shift 2 ;;
      *) _forge_die "forge_issue_create: unknown arg: $1" 1 ;;
    esac
  done
  [ -z "$title" ] && _forge_die "forge_issue_create: --title is required" 1

  case "$FORGE_TYPE" in
    github)
      local cmd="gh issue create --title $(printf '%q' "$title")"
      [ -n "$body" ] && cmd="$cmd --body $(printf '%q' "$body")"
      [ -n "$labels" ] && cmd="$cmd --label $(printf '%q' "$labels")"
      [ -n "$assignee" ] && cmd="$cmd --assignee $(printf '%q' "$assignee")"
      eval "$cmd"
      ;;
    gitlab)
      local cmd="glab issue create --title $(printf '%q' "$title") --no-editor"
      [ -n "$body" ] && cmd="$cmd --description $(printf '%q' "$body")"
      [ -n "$labels" ] && cmd="$cmd --label $(printf '%q' "$labels")"
      [ -n "$assignee" ] && cmd="$cmd --assignee $(printf '%q' "$assignee")"
      eval "$cmd"
      ;;
  esac
}

forge_issue_list() {
  _forge_require_cli
  local state="open" labels="" assignee="" limit="30" json_out=0
  while [ $# -gt 0 ]; do
    case "$1" in
      --state) state="$2"; shift 2 ;;
      --label) labels="${labels:+$labels,}$2"; shift 2 ;;
      --assignee) assignee="$2"; shift 2 ;;
      --limit) limit="$2"; shift 2 ;;
      --json) json_out=1; shift ;;
      *) _forge_die "forge_issue_list: unknown arg: $1" 1 ;;
    esac
  done

  case "$FORGE_TYPE" in
    github)
      local cmd="gh issue list --state $(printf '%q' "$state") --limit $(printf '%q' "$limit")"
      [ -n "$labels" ] && cmd="$cmd --label $(printf '%q' "$labels")"
      [ -n "$assignee" ] && cmd="$cmd --assignee $(printf '%q' "$assignee")"
      if [ "$json_out" -eq 1 ]; then
        cmd="$cmd --json number,title,state,labels,assignees,url"
      fi
      eval "$cmd"
      ;;
    gitlab)
      local cmd="glab issue list --per-page $(printf '%q' "$limit")"
      [ "$state" = "open" ] && cmd="$cmd --opened"
      [ "$state" = "closed" ] && cmd="$cmd --closed"
      [ -n "$labels" ] && cmd="$cmd --label $(printf '%q' "$labels")"
      [ -n "$assignee" ] && cmd="$cmd --assignee $(printf '%q' "$assignee")"
      if [ "$json_out" -eq 1 ]; then
        cmd="$cmd --output json"
      fi
      eval "$cmd"
      ;;
  esac
}

forge_issue_view() {
  _forge_require_cli
  local number="$1"; shift
  local json_out=0
  while [ $# -gt 0 ]; do
    case "$1" in
      --json) json_out=1; shift ;;
      *) _forge_die "forge_issue_view: unknown arg: $1" 1 ;;
    esac
  done

  case "$FORGE_TYPE" in
    github)
      if [ "$json_out" -eq 1 ]; then
        gh issue view "$number" --json number,title,body,state,labels,assignees,url
      else
        gh issue view "$number"
      fi
      ;;
    gitlab)
      if [ "$json_out" -eq 1 ]; then
        glab issue view "$number" --output json
      else
        glab issue view "$number"
      fi
      ;;
  esac
}

forge_issue_close() {
  _forge_require_cli
  local number="$1"; shift
  local comment=""
  while [ $# -gt 0 ]; do
    case "$1" in
      --comment) comment="$2"; shift 2 ;;
      *) _forge_die "forge_issue_close: unknown arg: $1" 1 ;;
    esac
  done

  case "$FORGE_TYPE" in
    github)
      if [ -n "$comment" ]; then
        gh issue close "$number" --comment "$comment"
      else
        gh issue close "$number"
      fi
      ;;
    gitlab)
      if [ -n "$comment" ]; then
        glab issue note "$number" --message "$comment"
      fi
      glab issue close "$number"
      ;;
  esac
}

forge_issue_comment() {
  _forge_require_cli
  local number="$1"; shift
  local body=""
  while [ $# -gt 0 ]; do
    case "$1" in
      --body) body="$2"; shift 2 ;;
      *) _forge_die "forge_issue_comment: unknown arg: $1" 1 ;;
    esac
  done
  [ -z "$body" ] && _forge_die "forge_issue_comment: --body is required" 1

  case "$FORGE_TYPE" in
    github) gh issue comment "$number" --body "$body" ;;
    gitlab) glab issue note "$number" --message "$body" ;;
  esac
}

forge_issue_assign() {
  _forge_require_cli
  local number="$1"; shift
  local assignee="${1:-@me}"

  case "$FORGE_TYPE" in
    github) gh issue edit "$number" --add-assignee "$assignee" ;;
    gitlab) glab issue update "$number" --assignee "$assignee" ;;
  esac
}

forge_issue_label() {
  _forge_require_cli
  local number="$1"; shift
  local labels=""
  while [ $# -gt 0 ]; do
    case "$1" in
      --add) labels="${labels:+$labels,}$2"; shift 2 ;;
      *) _forge_die "forge_issue_label: unknown arg: $1" 1 ;;
    esac
  done
  [ -z "$labels" ] && _forge_die "forge_issue_label: --add is required" 1

  case "$FORGE_TYPE" in
    github) gh issue edit "$number" --add-label "$labels" ;;
    gitlab) glab issue update "$number" --label "$labels" ;;
  esac
}

# Extract issue number from a branch name matching issue/<num>-* or agent/issue/<num>-*
_forge_issue_from_branch() {
  local branch="$1"
  case "$branch" in
    issue/[0-9]*)
      printf '%s' "$branch" | sed 's#^issue/\([0-9]*\).*#\1#'
      ;;
    agent/issue/[0-9]*)
      printf '%s' "$branch" | sed 's#^agent/issue/\([0-9]*\).*#\1#'
      ;;
    *)
      return 1
      ;;
  esac
}

# ---------------------------------------------------------------------------
# Pull Requests / Merge Requests
# ---------------------------------------------------------------------------

forge_pr_create() {
  _forge_require_cli
  local title="" body="" base="" draft=0 issue=""
  while [ $# -gt 0 ]; do
    case "$1" in
      --title) title="$2"; shift 2 ;;
      --body) body="$2"; shift 2 ;;
      --base) base="$2"; shift 2 ;;
      --draft) draft=1; shift ;;
      --issue) issue="$2"; shift 2 ;;
      *) _forge_die "forge_pr_create: unknown arg: $1" 1 ;;
    esac
  done
  [ -z "$title" ] && _forge_die "forge_pr_create: --title is required" 1

  case "$FORGE_TYPE" in
    github)
      local cmd="gh pr create --title $(printf '%q' "$title")"
      [ -n "$body" ] && cmd="$cmd --body $(printf '%q' "$body")"
      [ -n "$base" ] && cmd="$cmd --base $(printf '%q' "$base")"
      [ "$draft" -eq 1 ] && cmd="$cmd --draft"
      eval "$cmd"
      ;;
    gitlab)
      local cmd="glab mr create --title $(printf '%q' "$title") --no-editor"
      [ -n "$body" ] && cmd="$cmd --description $(printf '%q' "$body")"
      [ -n "$base" ] && cmd="$cmd --target-branch $(printf '%q' "$base")"
      [ "$draft" -eq 1 ] && cmd="$cmd --draft"
      eval "$cmd"
      ;;
  esac
}

forge_pr_list() {
  _forge_require_cli
  local state="open" head="" json_out=0
  while [ $# -gt 0 ]; do
    case "$1" in
      --state) state="$2"; shift 2 ;;
      --head) head="$2"; shift 2 ;;
      --json) json_out=1; shift ;;
      *) _forge_die "forge_pr_list: unknown arg: $1" 1 ;;
    esac
  done

  case "$FORGE_TYPE" in
    github)
      local cmd="gh pr list --state $(printf '%q' "$state")"
      [ -n "$head" ] && cmd="$cmd --head $(printf '%q' "$head")"
      if [ "$json_out" -eq 1 ]; then
        cmd="$cmd --json number,title,state,headRefName,url,mergedAt"
      fi
      eval "$cmd"
      ;;
    gitlab)
      local cmd="glab mr list --state $(printf '%q' "$state")"
      [ -n "$head" ] && cmd="$cmd --source-branch $(printf '%q' "$head")"
      if [ "$json_out" -eq 1 ]; then
        cmd="$cmd --output json"
      fi
      eval "$cmd"
      ;;
  esac
}

forge_pr_view() {
  _forge_require_cli
  local ref="$1"; shift
  local json_out=0
  while [ $# -gt 0 ]; do
    case "$1" in
      --json) json_out=1; shift ;;
      *) _forge_die "forge_pr_view: unknown arg: $1" 1 ;;
    esac
  done

  case "$FORGE_TYPE" in
    github)
      if [ "$json_out" -eq 1 ]; then
        gh pr view "$ref" --json number,title,state,headRefName,url,mergedAt,body
      else
        gh pr view "$ref"
      fi
      ;;
    gitlab)
      if [ "$json_out" -eq 1 ]; then
        glab mr view "$ref" --output json
      else
        glab mr view "$ref"
      fi
      ;;
  esac
}

# forge_pr_status BRANCH_NAME
#   Returns the PR/MR state for a branch: "merged" | "open" | "closed" | "draft" | "none"
forge_pr_status() {
  _forge_require_cli
  local branch="$1"

  case "$FORGE_TYPE" in
    github)
      local json
      json="$(gh pr list --head "$branch" --state all --json number,state,mergedAt --limit 1 2>/dev/null || true)"
      if [ -z "$json" ] || [ "$json" = "[]" ]; then
        printf 'none'
        return 0
      fi
      local state
      state="$(printf '%s' "$json" | sed -n 's/.*"state":"\([^"]*\)".*/\1/p' | head -1)"
      case "$state" in
        MERGED) printf 'merged' ;;
        OPEN)   printf 'open' ;;
        CLOSED) printf 'closed' ;;
        *)      printf '%s' "$state" ;;
      esac
      ;;
    gitlab)
      local json
      json="$(glab mr list --source-branch "$branch" --all --output json 2>/dev/null || true)"
      if [ -z "$json" ] || [ "$json" = "[]" ]; then
        printf 'none'
        return 0
      fi
      local state
      state="$(printf '%s' "$json" | sed -n 's/.*"state":"\([^"]*\)".*/\1/p' | head -1)"
      case "$state" in
        merged) printf 'merged' ;;
        opened) printf 'open' ;;
        closed) printf 'closed' ;;
        *)      printf '%s' "$state" ;;
      esac
      ;;
  esac
}

# forge_pr_number BRANCH_NAME — prints the PR/MR number for a branch, or ""
forge_pr_number() {
  _forge_require_cli
  local branch="$1"

  case "$FORGE_TYPE" in
    github)
      gh pr list --head "$branch" --state all --json number --limit 1 -q ".[0].number" 2>/dev/null || true
      ;;
    gitlab)
      local json
      json="$(glab mr list --source-branch "$branch" --all --output json 2>/dev/null || true)"
      printf '%s' "$json" | sed -n 's/.*"iid":\([0-9]*\).*/\1/p' | head -1
      ;;
  esac
}

forge_pr_merge() {
  _forge_require_cli
  local ref="$1"; shift
  local strategy="squash" delete_branch=1
  while [ $# -gt 0 ]; do
    case "$1" in
      --squash) strategy="squash"; shift ;;
      --rebase) strategy="rebase"; shift ;;
      --merge) strategy="merge"; shift ;;
      --no-delete-branch) delete_branch=0; shift ;;
      *) _forge_die "forge_pr_merge: unknown arg: $1" 1 ;;
    esac
  done

  case "$FORGE_TYPE" in
    github)
      local cmd="gh pr merge $(printf '%q' "$ref") --$strategy"
      [ "$delete_branch" -eq 1 ] && cmd="$cmd --delete-branch"
      eval "$cmd"
      ;;
    gitlab)
      local cmd="glab mr merge $(printf '%q' "$ref")"
      [ "$strategy" = "squash" ] && cmd="$cmd --squash"
      [ "$delete_branch" -eq 1 ] && cmd="$cmd --remove-source-branch"
      eval "$cmd"
      ;;
  esac
}

forge_pr_link_issue() {
  _forge_require_cli
  local pr_ref="$1" issue_number="$2"

  case "$FORGE_TYPE" in
    github)
      gh pr edit "$pr_ref" --body "$(gh pr view "$pr_ref" --json body -q '.body')

Closes #${issue_number}"
      ;;
    gitlab)
      _forge_warn "GitLab: add 'Closes #${issue_number}' to MR description manually or in commit message"
      ;;
  esac
}

# ---------------------------------------------------------------------------
# Discussions (GitHub) / Issue threads (GitLab fallback)
# ---------------------------------------------------------------------------

forge_discussion_create() {
  _forge_require_cli
  local title="" body="" category=""
  while [ $# -gt 0 ]; do
    case "$1" in
      --title) title="$2"; shift 2 ;;
      --body) body="$2"; shift 2 ;;
      --category) category="$2"; shift 2 ;;
      *) _forge_die "forge_discussion_create: unknown arg: $1" 1 ;;
    esac
  done
  [ -z "$title" ] && _forge_die "forge_discussion_create: --title is required" 1

  case "$FORGE_TYPE" in
    github)
      if [ -z "$category" ]; then
        category="General"
      fi
      _forge_log "Creating GitHub Discussion (category: $category)..."
      _forge_warn "GitHub Discussions creation via CLI requires 'gh api' with GraphQL."
      _forge_warn "Use the web UI or: gh api graphql -f query='mutation { ... }'"
      _forge_warn "Falling back to creating an issue labeled 'discussion'."
      forge_issue_create --title "[Discussion] $title" --body "$body" --label "discussion"
      ;;
    gitlab)
      _forge_log "GitLab does not have Discussions like GitHub. Creating an issue thread."
      forge_issue_create --title "[Discussion] $title" --body "$body" --label "discussion"
      ;;
  esac
}

# ---------------------------------------------------------------------------
# Project / Board (read-only)
# ---------------------------------------------------------------------------

forge_project_view() {
  _forge_require_cli

  case "$FORGE_TYPE" in
    github)
      _forge_log "GitHub Projects:"
      gh project list 2>/dev/null || _forge_warn "no projects found or 'gh project' extension not available"
      ;;
    gitlab)
      _forge_log "GitLab Boards:"
      glab board list 2>/dev/null || _forge_warn "no boards found"
      ;;
  esac
}

# ---------------------------------------------------------------------------
# Utility: slugify a title for branch names
# ---------------------------------------------------------------------------

forge_slugify() {
  printf '%s' "$1" \
    | tr '[:upper:]' '[:lower:]' \
    | sed 's/[^a-z0-9]/-/g; s/--*/-/g; s/^-//; s/-$//' \
    | cut -c1-50
}

# ---------------------------------------------------------------------------
# Utility: get current user login
# ---------------------------------------------------------------------------

forge_whoami() {
  _forge_require_cli
  case "$FORGE_TYPE" in
    github) gh api user -q '.login' 2>/dev/null || printf '@me' ;;
    gitlab) glab api user -q '.username' 2>/dev/null || printf '@me' ;;
  esac
}

# ---------------------------------------------------------------------------
# Utility: get the default branch name
# ---------------------------------------------------------------------------

forge_default_branch() {
  local branch
  branch="$(git symbolic-ref --quiet --short refs/remotes/origin/HEAD 2>/dev/null | sed 's#^origin/##' || true)"
  if [ -z "$branch" ]; then
    branch="$(git remote show origin 2>/dev/null | sed -n 's/.*HEAD branch: //p' || true)"
  fi
  if [ -z "$branch" ]; then
    branch="main"
  fi
  printf '%s' "$branch"
}
