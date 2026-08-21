#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
VENDOR_YAML="$REPO_ROOT/vendor.yaml"
VENDOR_DIR="$REPO_ROOT/skills/vendor"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

usage() {
  cat <<EOF
Usage: $(basename "$0") [OPTIONS] [SKILL_NAME]

Sync vendored skills from upstream repositories.

Options:
  --check    Dry-run: check for upstream updates without syncing
  -h, --help Show this help message

Arguments:
  SKILL_NAME  Optional: sync only the named skill (default: sync all)

Entries with a top-level `frozen:` block in vendor.yaml are skipped (the
vendored copy is kept as-is). Use this when an upstream skill is deleted or
renamed away but you want to keep shipping the last-synced version.

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
  # Check gh auth
  if ! gh auth status &>/dev/null 2>&1; then
    echo -e "${RED}Error: gh is not authenticated. Run 'gh auth login' first.${NC}" >&2
    exit 1
  fi
}

# Get the number of skills in vendor.yaml
skill_count() {
  yq '.skills | length' "$VENDOR_YAML"
}

# Get a field from a skill entry by index
skill_field() {
  local idx="$1" field="$2"
  yq ".skills[$idx].$field" "$VENDOR_YAML"
}

# Get latest commit SHA for a path in a repo (path="." means repo root)
get_latest_commit() {
  local owner="$1" repo="$2" branch="$3" path="$4"
  if [[ "$path" == "." ]]; then
    gh api "repos/$owner/$repo/commits?sha=$branch&per_page=1" \
      --jq '.[0].sha' 2>/dev/null || echo ""
  else
    gh api "repos/$owner/$repo/commits?sha=$branch&path=$path&per_page=1" \
      --jq '.[0].sha' 2>/dev/null || echo ""
  fi
}

# Get the blob SHA for one file, used to detect license-only updates without
# treating every unrelated commit in a large upstream repo as a skill update.
get_file_sha() {
  local owner="$1" repo="$2" branch="$3" path="$4"
  gh api "repos/$owner/$repo/contents/$path?ref=$branch" \
    --jq '.sha' 2>/dev/null || echo ""
}

download_file() {
  local owner="$1" repo="$2" branch="$3" src_path="$4" dest_path="$5"
  mkdir -p "$(dirname "$dest_path")"
  gh api "repos/$owner/$repo/contents/$src_path?ref=$branch" \
    --jq '.content' | base64 -d > "$dest_path"
}

# Download a directory tree from GitHub. src_path="." means whole repo root.
download_tree() {
  local owner="$1" repo="$2" branch="$3" src_path="$4" dest_dir="$5"

  mkdir -p "$dest_dir"

  # Get directory contents recursively using git trees API
  local tree_sha
  if [[ "$src_path" == "." ]]; then
    tree_sha=$(gh api "repos/$owner/$repo/git/trees/$branch?recursive=1" \
      --jq '.tree[] | .path + "\t" + .type + "\t" + (.url // "")')
  else
    tree_sha=$(gh api "repos/$owner/$repo/git/trees/$branch?recursive=1" \
      --jq '.tree[] | select(.path | startswith("'"$src_path"'/")) | .path + "\t" + .type + "\t" + (.url // "")')
  fi

  if [[ -z "$tree_sha" ]]; then
    echo -e "${RED}Error: No files found at $owner/$repo/$src_path${NC}" >&2
    return 1
  fi

  # Process each file
  while IFS=$'\t' read -r file_path file_type file_url; do
    local rel_path
    if [[ "$src_path" == "." ]]; then
      rel_path="$file_path"
    else
      rel_path="${file_path#"$src_path"/}"
    fi
    local dest_path="$dest_dir/$rel_path"

    if [[ "$file_type" == "tree" ]]; then
      mkdir -p "$dest_path"
    elif [[ "$file_type" == "blob" ]]; then
      mkdir -p "$(dirname "$dest_path")"
      # Download file content via the blob API
      gh api "$file_url" --jq '.content' | base64 -d > "$dest_path"
    fi
  done <<< "$tree_sha"
}

sync_skill() {
  local idx="$1" check_only="${2:-false}"

  local name series owner repo path branch license_path last_commit last_license_sha
  name=$(skill_field "$idx" "name")
  series=$(skill_field "$idx" "series")
  owner=$(skill_field "$idx" "upstream.owner")
  repo=$(skill_field "$idx" "upstream.repo")
  path=$(skill_field "$idx" "upstream.path")
  branch=$(skill_field "$idx" "upstream.branch")
  license_path=$(skill_field "$idx" "license_path")
  last_commit=$(skill_field "$idx" "last_sync.commit")
  last_license_sha=$(skill_field "$idx" "last_sync.license_sha")

  # Normalize yq null to empty
  [[ "$last_commit" == "null" || "$last_commit" == '""' ]] && last_commit=""
  [[ "$last_license_sha" == "null" || "$last_license_sha" == '""' ]] && last_license_sha=""
  [[ "$series" == "null" || "$series" == '""' ]] && series=""
  [[ "$license_path" == "null" || "$license_path" == '""' ]] && license_path=""

  # Frozen entries: upstream renamed the skill away or deleted it, but we
  # keep shipping the last vendored copy. Skip fetching entirely so a
  # vanished upstream path can't break `make sync`. See `frozen:` in vendor.yaml.
  local frozen frozen_reason
  frozen=$(yq ".skills[$idx] | has(\"frozen\")" "$VENDOR_YAML")
  if [[ "$frozen" == "true" ]]; then
    frozen_reason=$(skill_field "$idx" "frozen.reason")
    [[ "$frozen_reason" == "null" ]] && frozen_reason="upstream removed"
    echo -e "$name ($owner/$repo)... ${YELLOW}frozen${NC} — skipping ($frozen_reason)"
    return 0
  fi

  echo -n "Checking $name ($owner/$repo)... "

  local latest_commit latest_license_sha=""
  latest_commit=$(get_latest_commit "$owner" "$repo" "$branch" "$path")

  if [[ -z "$latest_commit" ]]; then
    echo -e "${RED}failed to fetch latest commit${NC}"
    return 1
  fi

  if [[ -n "$license_path" ]]; then
    latest_license_sha=$(get_file_sha "$owner" "$repo" "$branch" "$license_path")
    if [[ -z "$latest_license_sha" ]]; then
      echo -e "${RED}failed to fetch license: $license_path${NC}"
      return 1
    fi
  fi

  if [[ "$latest_commit" == "$last_commit" && "$latest_license_sha" == "$last_license_sha" ]]; then
    echo -e "${GREEN}up to date${NC}"
    return 0
  fi

  if [[ "$check_only" == "true" ]]; then
    echo -e "${YELLOW}update available${NC} (${last_commit:0:7}${last_commit:+..}${latest_commit:0:7})"
    return 0
  fi

  echo -e "${YELLOW}syncing...${NC}"

  local dest
  if [[ -n "$series" ]]; then
    dest="$VENDOR_DIR/$series/$name"
  else
    dest="$VENDOR_DIR/$name"
  fi
  # Clean existing and re-download
  rm -rf "$dest"
  download_tree "$owner" "$repo" "$branch" "$path" "$dest"
  if [[ -n "$license_path" ]]; then
    download_file "$owner" "$repo" "$branch" "$license_path" "$dest/LICENSE.txt"
  fi

  # Update vendor.yaml with sync info
  local sync_date
  sync_date=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
  yq -i ".skills[$idx].last_sync.date = \"$sync_date\" | .skills[$idx].last_sync.commit = \"$latest_commit\"" "$VENDOR_YAML"
  if [[ -n "$license_path" ]]; then
    yq -i ".skills[$idx].last_sync.license_sha = \"$latest_license_sha\"" "$VENDOR_YAML"
  else
    yq -i "del(.skills[$idx].last_sync.license_sha)" "$VENDOR_YAML"
  fi

  echo -e "  ${GREEN}synced${NC} to ${latest_commit:0:7}"
}

main() {
  local check_only=false
  local filter_name=""

  while [[ $# -gt 0 ]]; do
    case "$1" in
      --check) check_only=true; shift ;;
      -h|--help) usage; exit 0 ;;
      -*) echo "Unknown option: $1" >&2; usage; exit 1 ;;
      *) filter_name="$1"; shift ;;
    esac
  done

  check_deps

  if [[ ! -f "$VENDOR_YAML" ]]; then
    echo -e "${RED}Error: $VENDOR_YAML not found${NC}" >&2
    exit 1
  fi

  local count
  count=$(skill_count)

  if [[ "$count" -eq 0 ]]; then
    echo "No skills configured in vendor.yaml"
    exit 0
  fi

  local found=false
  for ((i = 0; i < count; i++)); do
    local name
    name=$(skill_field "$i" "name")
    if [[ -n "$filter_name" && "$name" != "$filter_name" ]]; then
      continue
    fi
    found=true
    sync_skill "$i" "$check_only"
  done

  if [[ "$found" == "false" ]]; then
    echo -e "${RED}Error: Skill '$filter_name' not found in vendor.yaml${NC}" >&2
    exit 1
  fi
}

main "$@"
