#!/usr/bin/env bash
# Validate skills/.claude-plugin/marketplace.json — the catalog manifest
# read by `npx skills@latest add daviddwlee84/agent-skills/skills`.
#
# Checks:
#   1. JSON parses
#   2. `name` is not on the official reserved list
#   3. Every plugins[].skills[] path exists and contains SKILL.md
#   4. No skill path is listed under more than one plugin
#   5. (warn) Every on-disk SKILL.md under skills/ is either listed in
#      some plugin or will fall through to "Other" in the picker UI.
#
# Errors (1-4) exit non-zero; (5) is warn-only so the build doesn't break
# while a skill is mid-add.
#
# Reference: docs/reference/npx-skills-metadata.md
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
SKILLS_DIR="$REPO_ROOT/skills"
MANIFEST="$SKILLS_DIR/.claude-plugin/marketplace.json"

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

errors=0
warnings=0

err()  { printf "${RED}ERROR:${NC} %s\n"   "$*" >&2; errors=$((errors+1)); }
warn() { printf "${YELLOW}WARN:${NC}  %s\n" "$*" >&2; warnings=$((warnings+1)); }
ok()   { printf "${GREEN}OK:${NC}    %s\n"  "$*"; }

# 1. File exists + valid JSON
if [[ ! -f "$MANIFEST" ]]; then
  err "manifest not found: $MANIFEST"
  exit 1
fi
if ! jq empty "$MANIFEST" 2>/dev/null; then
  err "manifest is not valid JSON: $MANIFEST"
  exit 1
fi
ok "JSON parses"

# 2. Marketplace name is not reserved.
# Source: https://code.claude.com/docs/en/plugin-marketplaces (reserved names section).
RESERVED=(
  claude-code-marketplace
  claude-code-plugins
  claude-plugins-official
  anthropic-marketplace
  anthropic-plugins
  agent-skills
  knowledge-work-plugins
  life-sciences
)
name="$(jq -r '.name // ""' "$MANIFEST")"
if [[ -z "$name" ]]; then
  err "manifest has no top-level 'name' field"
fi
for r in "${RESERVED[@]}"; do
  if [[ "$name" == "$r" ]]; then
    err "marketplace name '$name' is on the reserved list"
  fi
done
[[ $errors -eq 0 ]] && ok "marketplace name '$name' is not reserved"

# 3. Every plugins[].skills[] path exists with a SKILL.md.
# Skills paths are relative to the manifest directory ($SKILLS_DIR).
declare -A seen_paths=()
duplicates=0
while IFS=$'\t' read -r plugin_name skill_path; do
  # Resolve relative to skills/
  resolved="$SKILLS_DIR/${skill_path#./}"
  if [[ ! -d "$resolved" ]]; then
    err "plugin '$plugin_name': directory not found: $skill_path  (resolved: $resolved)"
    continue
  fi
  if [[ ! -f "$resolved/SKILL.md" ]]; then
    err "plugin '$plugin_name': missing SKILL.md in $skill_path"
    continue
  fi
  if [[ -n "${seen_paths[$skill_path]+x}" ]]; then
    err "duplicate skill path '$skill_path' (also under plugin '${seen_paths[$skill_path]}')"
    duplicates=$((duplicates+1))
  else
    seen_paths[$skill_path]="$plugin_name"
  fi
done < <(jq -r '.plugins[] | .name as $n | .skills[]? | [$n, .] | @tsv' "$MANIFEST")

listed_count=${#seen_paths[@]}
ok "$listed_count skill paths listed; all exist with SKILL.md"
[[ $duplicates -eq 0 ]] && ok "no duplicate skill paths across plugins"

# 4. (already covered by duplicates check above)

# 5. Warn for on-disk skills not covered by any plugin (will fall under "Other").
# Discovery: depth 2 (skills/<top>/<name>/SKILL.md) + depth 3 (skills/vendor/<series>/<name>/SKILL.md).
on_disk_paths=$(
  find "$SKILLS_DIR" -maxdepth 4 -name SKILL.md -not -path '*/.claude-plugin/*' \
    | sed "s|^$SKILLS_DIR/||; s|/SKILL.md\$||" \
    | sort
)
unlisted=0
while IFS= read -r rel; do
  [[ -z "$rel" ]] && continue
  key="./$rel"
  if [[ -z "${seen_paths[$key]+x}" ]]; then
    warn "skill '$rel' not listed in any plugin — will appear under 'Other'"
    unlisted=$((unlisted+1))
  fi
done <<< "$on_disk_paths"

if [[ $unlisted -eq 0 ]]; then
  ok "all on-disk skills are covered by a plugin (no fallback to 'Other')"
fi

echo
if [[ $errors -gt 0 ]]; then
  printf "${RED}FAILED${NC}: %d error(s), %d warning(s)\n" "$errors" "$warnings" >&2
  exit 1
fi
printf "${GREEN}PASSED${NC}: 0 errors, %d warning(s)\n" "$warnings"
