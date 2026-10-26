#!/usr/bin/env bash
set -euo pipefail

# Standalone PR/MR lifecycle command wrapping forge.sh.
# Provides a unified CLI for PR operations across GitHub and GitLab.
#
# Compatibility: macOS system Bash 3.2+.

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

# shellcheck source=forge.sh
source "$SCRIPT_DIR/forge.sh"

usage() {
  cat <<'EOF'
Usage: forge-pr.sh <subcommand> [args]

Subcommands:
  create    Create a new PR/MR.
  list      List PRs/MRs.
  view      View a PR/MR.
  status    Show PR/MR status for a branch.
  merge     Merge a PR/MR.
  link      Link a PR to an issue (add "Closes #N").

Options vary by subcommand. Use forge-pr.sh <subcommand> --help for details.
EOF
}

[ $# -eq 0 ] && { usage; exit 1; }

subcmd="$1"; shift

forge_detect
_forge_require_cli

case "$subcmd" in
  create)
    title="" body="" base="" draft=0 issue=""
    while [ $# -gt 0 ]; do
      case "$1" in
        --title) title="$2"; shift 2 ;;
        --body) body="$2"; shift 2 ;;
        --base) base="$2"; shift 2 ;;
        --draft) draft=1; shift ;;
        --issue) issue="$2"; shift 2 ;;
        -h|--help)
          echo "Usage: forge-pr.sh create --title TITLE [--body BODY] [--base BRANCH] [--draft] [--issue N]"
          exit 0 ;;
        *) _forge_die "create: unknown arg: $1" 1 ;;
      esac
    done
    [ -z "$title" ] && _forge_die "create: --title is required" 1

    # If issue is specified, add Closes reference
    if [ -n "$issue" ]; then
      body="${body:+$body

}Closes #${issue}"
    fi

    local_args="--title $(printf '%q' "$title")"
    [ -n "$body" ] && local_args="$local_args --body $(printf '%q' "$body")"
    [ -n "$base" ] && local_args="$local_args --base $(printf '%q' "$base")"
    [ "$draft" -eq 1 ] && local_args="$local_args --draft"
    eval "forge_pr_create $local_args"
    ;;

  list)
    state="open" head="" json_flag=""
    while [ $# -gt 0 ]; do
      case "$1" in
        --state) state="$2"; shift 2 ;;
        --head) head="$2"; shift 2 ;;
        --json) json_flag="--json"; shift ;;
        -h|--help)
          echo "Usage: forge-pr.sh list [--state open|closed|merged|all] [--head BRANCH] [--json]"
          exit 0 ;;
        *) _forge_die "list: unknown arg: $1" 1 ;;
      esac
    done
    local_args="--state $(printf '%q' "$state")"
    [ -n "$head" ] && local_args="$local_args --head $(printf '%q' "$head")"
    [ -n "$json_flag" ] && local_args="$local_args --json"
    eval "forge_pr_list $local_args"
    ;;

  view)
    [ $# -eq 0 ] && _forge_die "view: PR number or branch required" 1
    ref="$1"; shift
    json_flag=""
    while [ $# -gt 0 ]; do
      case "$1" in
        --json) json_flag="--json"; shift ;;
        -h|--help) echo "Usage: forge-pr.sh view <number|branch> [--json]"; exit 0 ;;
        *) _forge_die "view: unknown arg: $1" 1 ;;
      esac
    done
    forge_pr_view "$ref" $json_flag
    ;;

  status)
    branch="${1:-$(git branch --show-current 2>/dev/null || true)}"
    [ -z "$branch" ] && _forge_die "status: no branch specified and not on a branch" 1
    st="$(forge_pr_status "$branch")"
    num="$(forge_pr_number "$branch" 2>/dev/null || true)"
    if [ "$st" = "none" ]; then
      _forge_log "No PR found for branch: $branch"
    else
      _forge_log "Branch: $branch"
      _forge_log "PR:     #${num:-?} ($st)"
    fi
    ;;

  merge)
    [ $# -eq 0 ] && _forge_die "merge: PR number required" 1
    ref="$1"; shift
    strategy="squash" no_delete=0
    while [ $# -gt 0 ]; do
      case "$1" in
        --squash) strategy="squash"; shift ;;
        --rebase) strategy="rebase"; shift ;;
        --merge) strategy="merge"; shift ;;
        --no-delete-branch) no_delete=1; shift ;;
        -h|--help)
          echo "Usage: forge-pr.sh merge <number> [--squash|--rebase|--merge] [--no-delete-branch]"
          exit 0 ;;
        *) _forge_die "merge: unknown arg: $1" 1 ;;
      esac
    done
    local_args="--$strategy"
    [ "$no_delete" -eq 1 ] && local_args="$local_args --no-delete-branch"
    eval "forge_pr_merge $(printf '%q' "$ref") $local_args"
    ;;

  link)
    [ $# -lt 2 ] && _forge_die "link: PR ref and issue number required" 1
    pr_ref="$1"
    issue_num="$2"
    forge_pr_link_issue "$pr_ref" "$issue_num"
    ;;

  -h|--help) usage; exit 0 ;;
  *) echo "Unknown subcommand: $subcmd" >&2; usage >&2; exit 1 ;;
esac
