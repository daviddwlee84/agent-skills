#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
VENDOR_YAML="$REPO_ROOT/vendor.yaml"
SYNC_SCRIPT="$REPO_ROOT/scripts/sync-vendor.sh"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

usage() {
  cat <<EOF
Usage: $(basename "$0") [OPTIONS] <owner/repo[/path/to/skill]>

Add a vendored skill to vendor.yaml and optionally sync it.

Examples:
  $(basename "$0") marimo-team/skills/skills/marimo-notebook
  $(basename "$0") vercel-labs/agent-skills/skills/next-js
  $(basename "$0") --name my-skill --branch dev owner/repo/skills/my-skill
  $(basename "$0") --no-sync owner/repo/skills/some-skill
  $(basename "$0") --series fullstack-nextjs vercel/vercel-plugin/skills/nextjs

Options:
  --name NAME      Override the skill name (default: last path component)
  --series SERIES  Group under skills/vendor/<series>/<name>/ (default: flat)
  --branch BRANCH  Upstream branch (default: main)
  --no-sync        Only add to vendor.yaml, don't sync immediately
  -h, --help       Show this help message

Dependencies: gh (GitHub CLI), yq (YAML processor)
EOF
}

check_deps() {
  local missing=()
  command -v gh &>/dev/null || missing+=(gh)
  command -v yq &>/dev/null || missing+=(yq)
  if [[ ${#missing[@]} -gt 0 ]]; then
    echo -e "${RED}Error: Missing dependencies: ${missing[*]}${NC}" >&2
    if [[ "$(uname -s)" == "Darwin" ]]; then
      echo "  macOS:  brew install ${missing[*]}" >&2
    else
      echo "  Debian/Ubuntu: sudo apt install ${missing[*]}" >&2
      echo "  Fedora/RHEL:   sudo dnf install ${missing[*]}" >&2
      echo "  Arch:          sudo pacman -S ${missing[*]}" >&2
      echo "  Or via: snap install ${missing[*]}" >&2
    fi
    exit 1
  fi
  if ! gh auth status &>/dev/null 2>&1; then
    echo -e "${RED}Error: gh is not authenticated. Run 'gh auth login' first.${NC}" >&2
    exit 1
  fi
}

# Parse owner/repo/path from a single argument
# Accepts formats:
#   owner/repo/path/to/skill
#   https://github.com/owner/repo/tree/branch/path/to/skill
parse_source() {
  local input="$1"

  # Strip GitHub URL prefix if present
  input="${input#https://github.com/}"
  input="${input#http://github.com/}"

  # Strip /tree/<branch>/ from URL-style paths
  if [[ "$input" =~ ^([^/]+/[^/]+)/tree/([^/]+)/(.+)$ ]]; then
    local url_branch="${BASH_REMATCH[2]}"
    input="${BASH_REMATCH[1]}/${BASH_REMATCH[3]}"
    # Use URL branch as default if --branch not explicitly set
    if [[ -z "$OPT_BRANCH_SET" ]]; then
      OPT_BRANCH="$url_branch"
    fi
  fi

  # Remove trailing slash
  input="${input%/}"

  # Need at least owner/repo/one-path-component
  local slash_count
  slash_count=$(echo "$input" | tr -cd '/' | wc -c | tr -d ' ')
  if [[ "$slash_count" -lt 2 ]]; then
    echo -e "${RED}Error: Expected format: owner/repo/path/to/skill${NC}" >&2
    echo "  Got: $input" >&2
    exit 1
  fi

  # Extract owner and repo (first two components)
  PARSED_OWNER="$(echo "$input" | cut -d'/' -f1)"
  PARSED_REPO="$(echo "$input" | cut -d'/' -f2)"
  PARSED_PATH="$(echo "$input" | cut -d'/' -f3-)"
}

main() {
  local opt_name=""
  local opt_series=""
  OPT_BRANCH="main"
  OPT_BRANCH_SET=""
  local opt_sync=true
  local positional=""

  while [[ $# -gt 0 ]]; do
    case "$1" in
      --name) opt_name="$2"; shift 2 ;;
      --series) opt_series="$2"; shift 2 ;;
      --branch) OPT_BRANCH="$2"; OPT_BRANCH_SET=1; shift 2 ;;
      --no-sync) opt_sync=false; shift ;;
      -h|--help) usage; exit 0 ;;
      -*) echo "Unknown option: $1" >&2; usage; exit 1 ;;
      *) positional="$1"; shift ;;
    esac
  done

  if [[ -z "$positional" ]]; then
    echo -e "${RED}Error: Missing required argument${NC}" >&2
    usage
    exit 1
  fi

  check_deps

  parse_source "$positional"

  local name="${opt_name:-$(basename "$PARSED_PATH")}"
  local owner="$PARSED_OWNER"
  local repo="$PARSED_REPO"
  local path="$PARSED_PATH"
  local branch="$OPT_BRANCH"

  # Verify the upstream path exists
  echo -n "Verifying upstream $owner/$repo/$path@$branch... "
  if ! gh api "repos/$owner/$repo/contents/$path?ref=$branch" &>/dev/null 2>&1; then
    echo -e "${RED}not found${NC}"
    echo -e "${RED}Error: Path '$path' not found in $owner/$repo (branch: $branch)${NC}" >&2
    exit 1
  fi
  echo -e "${GREEN}found${NC}"

  # Check for duplicates
  if [[ -f "$VENDOR_YAML" ]]; then
    local existing
    existing=$(yq ".skills[] | select(.name == \"$name\") | .name" "$VENDOR_YAML" 2>/dev/null || true)
    if [[ -n "$existing" ]]; then
      echo -e "${YELLOW}Skill '$name' already exists in vendor.yaml${NC}"
      echo "Use --name to specify a different name, or edit vendor.yaml manually."
      exit 1
    fi
  fi

  # Append to vendor.yaml
  echo -n "Adding '$name' to vendor.yaml... "
  yq -i ".skills += [{
    \"name\": \"$name\",
    \"upstream\": {
      \"owner\": \"$owner\",
      \"repo\": \"$repo\",
      \"path\": \"$path\",
      \"branch\": \"$branch\"
    },
    \"last_sync\": {
      \"date\": \"\",
      \"commit\": \"\"
    }
  }]" "$VENDOR_YAML"
  if [[ -n "$opt_series" ]]; then
    yq -i ".skills[-1].series = \"$opt_series\"" "$VENDOR_YAML"
  fi
  echo -e "${GREEN}done${NC}"

  if [[ "$opt_sync" == "true" ]]; then
    echo ""
    "$SYNC_SCRIPT" "$name"
  else
    echo -e "\nRun ${YELLOW}make sync${NC} or ${YELLOW}./scripts/sync-vendor.sh $name${NC} to download the skill."
  fi
}

main "$@"
