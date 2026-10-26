#!/usr/bin/env bash
set -euo pipefail

# Standalone issue lifecycle command wrapping forge.sh.
# Provides a unified CLI for issue operations across GitHub and GitLab.
#
# Compatibility: macOS system Bash 3.2+.

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

# shellcheck source=forge.sh
source "$SCRIPT_DIR/forge.sh"

usage() {
  cat <<'EOF'
Usage: forge-issue.sh <subcommand> [args]

Subcommands:
  create    Create a new issue.
  list      List open issues.
  view      View an issue.
  close     Close an issue.
  comment   Add a comment to an issue.
  assign    Assign an issue.
  label     Add labels to an issue.
  backlog   Create a backlog issue (labeled priority/P? + backlog).

Options vary by subcommand. Use forge-issue.sh <subcommand> --help for details.
EOF
}

[ $# -eq 0 ] && { usage; exit 1; }

subcmd="$1"; shift

forge_detect
_forge_require_cli

case "$subcmd" in
  create)
    title="" body="" labels="" assignee=""
    while [ $# -gt 0 ]; do
      case "$1" in
        --title) title="$2"; shift 2 ;;
        --body) body="$2"; shift 2 ;;
        --label) labels="${labels:+$labels }--label $2"; shift 2 ;;
        --assignee) assignee="$2"; shift 2 ;;
        -h|--help)
          echo "Usage: forge-issue.sh create --title TITLE [--body BODY] [--label LABEL]... [--assignee USER]"
          exit 0 ;;
        *) _forge_die "create: unknown arg: $1" 1 ;;
      esac
    done
    [ -z "$title" ] && _forge_die "create: --title is required" 1
    local_args="--title $(printf '%q' "$title")"
    [ -n "$body" ] && local_args="$local_args --body $(printf '%q' "$body")"
    [ -n "$assignee" ] && local_args="$local_args --assignee $(printf '%q' "$assignee")"
    # Re-parse labels
    eval "forge_issue_create $local_args $labels"
    ;;

  list)
    state="open" labels="" assignee="" limit="30" json_flag=""
    while [ $# -gt 0 ]; do
      case "$1" in
        --state) state="$2"; shift 2 ;;
        --label) labels="${labels:+$labels }--label $2"; shift 2 ;;
        --assignee) assignee="$2"; shift 2 ;;
        --limit) limit="$2"; shift 2 ;;
        --json) json_flag="--json"; shift ;;
        -h|--help)
          echo "Usage: forge-issue.sh list [--state open|closed] [--label LABEL] [--assignee USER] [--limit N] [--json]"
          exit 0 ;;
        *) _forge_die "list: unknown arg: $1" 1 ;;
      esac
    done
    local_args="--state $(printf '%q' "$state") --limit $(printf '%q' "$limit")"
    [ -n "$assignee" ] && local_args="$local_args --assignee $(printf '%q' "$assignee")"
    [ -n "$json_flag" ] && local_args="$local_args --json"
    eval "forge_issue_list $local_args $labels"
    ;;

  view)
    [ $# -eq 0 ] && _forge_die "view: issue number required" 1
    number="$1"; shift
    json_flag=""
    while [ $# -gt 0 ]; do
      case "$1" in
        --json) json_flag="--json"; shift ;;
        -h|--help) echo "Usage: forge-issue.sh view <number> [--json]"; exit 0 ;;
        *) _forge_die "view: unknown arg: $1" 1 ;;
      esac
    done
    forge_issue_view "$number" $json_flag
    ;;

  close)
    [ $# -eq 0 ] && _forge_die "close: issue number required" 1
    number="$1"; shift
    comment=""
    while [ $# -gt 0 ]; do
      case "$1" in
        --comment) comment="$2"; shift 2 ;;
        -h|--help) echo "Usage: forge-issue.sh close <number> [--comment TEXT]"; exit 0 ;;
        *) _forge_die "close: unknown arg: $1" 1 ;;
      esac
    done
    if [ -n "$comment" ]; then
      forge_issue_close "$number" --comment "$comment"
    else
      forge_issue_close "$number"
    fi
    ;;

  comment)
    [ $# -eq 0 ] && _forge_die "comment: issue number required" 1
    number="$1"; shift
    body=""
    while [ $# -gt 0 ]; do
      case "$1" in
        --body) body="$2"; shift 2 ;;
        -h|--help) echo "Usage: forge-issue.sh comment <number> --body TEXT"; exit 0 ;;
        *) _forge_die "comment: unknown arg: $1" 1 ;;
      esac
    done
    [ -z "$body" ] && _forge_die "comment: --body is required" 1
    forge_issue_comment "$number" --body "$body"
    ;;

  assign)
    [ $# -eq 0 ] && _forge_die "assign: issue number required" 1
    number="$1"; shift
    assignee="${1:-@me}"
    forge_issue_assign "$number" "$assignee"
    ;;

  label)
    [ $# -eq 0 ] && _forge_die "label: issue number required" 1
    number="$1"; shift
    labels=""
    while [ $# -gt 0 ]; do
      case "$1" in
        --add) labels="${labels:+$labels }--add $2"; shift 2 ;;
        -h|--help) echo "Usage: forge-issue.sh label <number> --add LABEL [--add LABEL]..."; exit 0 ;;
        *) _forge_die "label: unknown arg: $1" 1 ;;
      esac
    done
    [ -z "$labels" ] && _forge_die "label: --add is required" 1
    eval "forge_issue_label $number $labels"
    ;;

  backlog)
    title="" body="" priority="P?" effort=""
    while [ $# -gt 0 ]; do
      case "$1" in
        --title) title="$2"; shift 2 ;;
        --body) body="$2"; shift 2 ;;
        --priority) priority="$2"; shift 2 ;;
        --effort) effort="$2"; shift 2 ;;
        -h|--help)
          echo "Usage: forge-issue.sh backlog --title TITLE [--body BODY] [--priority P1|P2|P3|P?] [--effort S|M|L|XL]"
          exit 0 ;;
        *) _forge_die "backlog: unknown arg: $1" 1 ;;
      esac
    done
    [ -z "$title" ] && _forge_die "backlog: --title is required" 1

    # Detect role if not already done
    if [ -z "$FORGE_ROLE" ]; then
      forge_detect_role 2>/dev/null || true
    fi

    local label_arg=""

    if forge_is_maintainer; then
      # Maintainers: apply backlog + priority labels directly
      label_arg="--label backlog"
      case "$priority" in
        P1|P2|P3) label_arg="$label_arg --label priority/$priority" ;;
        "P?"|*) label_arg="$label_arg --label priority/P3" ;;
      esac
    else
      # Contributors: describe priority in body, don't apply labels
      # (the maintainer will triage and label)
      _forge_log "Contributor role: priority/effort noted in body, not as labels (maintainer will triage)."
      body="${body:+$body

}Suggested priority: $priority"
    fi

    [ -n "$effort" ] && body="${body:+$body

}Effort: $effort"

    eval "forge_issue_create --title $(printf '%q' "$title") --body $(printf '%q' "${body:-}") $label_arg"
    ;;

  -h|--help) usage; exit 0 ;;
  *) echo "Unknown subcommand: $subcmd" >&2; usage >&2; exit 1 ;;
esac
