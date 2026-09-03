#!/usr/bin/env bash
# Audit and migrate mkdocs-static-i18n + mkdocs-llmstxt sites to the
# mkdocs-site-bootstrap two-pass build. Bash 3.2 compatible.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
SKILL_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
CANONICAL_HELPER="$SKILL_DIR/assets/build-docs-site.py"
MANAGED_MARKER="# mkdocs-site-bootstrap-managed: two-pass-build-v1"

usage() {
  cat <<'EOF'
Usage: migrate-i18n-llmstxt.sh [OPTIONS]

Audit an MkDocs site for the mkdocs-static-i18n + mkdocs-llmstxt overwrite
bug, or conservatively migrate a recognized site to the managed two-pass
build. Audit is the default and never writes files.

Options:
  --target-dir DIR  Repository root (default: walk up to mkdocs.yml).
  --apply           Apply safe, recognized changes.
  --dry-run         Preview --apply without writing (requires --apply).
  --verify          Run the managed strict two-pass build after auditing/apply.
  --json            Emit one JSON result on stdout; diagnostics stay on stderr.
  --help, -h        Show this help and exit.

Examples:
  migrate-i18n-llmstxt.sh --target-dir . --json
  migrate-i18n-llmstxt.sh --target-dir . --apply --dry-run --json
  migrate-i18n-llmstxt.sh --target-dir . --apply --verify --json

Exit codes:
  0   Safe already, or migration and optional verification completed.
  1   Invalid arguments.
  2   Target or mkdocs.yml not found.
  4   yq/config/staging error.
  10  Audit/dry-run found an affected site.
  11  Apply completed, but manual migration actions remain.
  12  Managed strict two-pass verification failed.
EOF
}

log() { printf '%s\n' "$*" >&2; }
die() { code="$2"; printf 'error: %s\n' "$1" >&2; exit "$code"; }

TARGET=""
APPLY=0
DRY_RUN=0
VERIFY=0
JSON=0

while [ $# -gt 0 ]; do
  case "$1" in
    --target-dir)
      [ $# -ge 2 ] || die "--target-dir requires a directory" 1
      case "$2" in -*) die "--target-dir requires a directory, got flag: $2" 1 ;; esac
      TARGET="$2"
      shift 2
      ;;
    --apply) APPLY=1; shift ;;
    --dry-run) DRY_RUN=1; shift ;;
    --verify) VERIFY=1; shift ;;
    --json) JSON=1; shift ;;
    --help|-h) usage; exit 0 ;;
    -*) die "unknown flag: $1 (try --help)" 1 ;;
    *) die "unexpected positional argument: $1" 1 ;;
  esac
done

[ "$DRY_RUN" = "0" ] || [ "$APPLY" = "1" ] || \
  die "--dry-run requires --apply" 1
command -v yq >/dev/null 2>&1 || \
  die "yq v4 is required (install with: brew install yq)" 4

if [ -z "$TARGET" ]; then
  cursor="$(pwd)"
  while [ "$cursor" != "/" ]; do
    if [ -f "$cursor/mkdocs.yml" ]; then
      TARGET="$cursor"
      break
    fi
    cursor="$(dirname "$cursor")"
  done
  [ -n "$TARGET" ] || die "could not find mkdocs.yml walking up from $(pwd)" 2
fi

[ -d "$TARGET" ] || die "target directory not found: $TARGET" 2
TARGET="$(cd "$TARGET" && pwd -P)"
MKDOCS="$TARGET/mkdocs.yml"
[ -f "$MKDOCS" ] || die "mkdocs.yml not found in $TARGET" 2

STATE_DIR="$(mktemp -d "${TMPDIR:-/tmp}/mkdocs-i18n-migration.XXXXXX")"
CHANGES_FILE="$STATE_DIR/changes.jsonl"
MANUAL_FILE="$STATE_DIR/manual.jsonl"
: > "$CHANGES_FILE"
: > "$MANUAL_FILE"
trap 'rm -rf "$STATE_DIR"' EXIT HUP INT TERM

json_line() {
  JSON_VALUE="$1" yq -n -o=json 'strenv(JSON_VALUE)' | tr -d '\n'
  printf '\n'
}

add_change() {
  json_line "$1" >> "$CHANGES_FILE"
  NEEDS_CHANGE=1
}

add_manual() {
  json_line "$1" >> "$MANUAL_FILE"
  MANUAL_COUNT=$((MANUAL_COUNT + 1))
}

json_array() {
  file="$1"
  if [ ! -s "$file" ]; then
    printf '[]'
    return
  fi
  printf '['
  awk 'NR > 1 { printf "," } { printf "%s", $0 }' "$file"
  printf ']'
}

if ! yq '.' "$MKDOCS" >/dev/null 2>&1; then
  die "mkdocs.yml is not valid YAML; fix it before running this migration" 4
fi

if yq -e 'has("INHERIT") and (.INHERIT != null)' "$MKDOCS" >/dev/null 2>&1; then
  json_line "mkdocs.yml uses INHERIT, which this migration cannot safely resolve; migrate the base config or flatten the effective config first" >> "$MANUAL_FILE"
  if [ "$APPLY" = "1" ] && [ "$DRY_RUN" = "0" ]; then
    inherit_status=manual_required
    inherit_rc=11
  else
    inherit_status=affected
    inherit_rc=10
  fi
  if [ "$JSON" = "1" ]; then
    printf '{"status":"%s","affected":true,"changed":false,"dry_run":%s,"verified":null,"changes":[],"manual_actions":' \
      "$inherit_status" "$([ "$DRY_RUN" = "1" ] && printf true || printf false)"
    json_array "$MANUAL_FILE"
    printf '}\n'
  else
    printf 'Status: %s\n' "$inherit_status"
    printf 'Manual actions:\n'
    sed 's/^/  - /' "$MANUAL_FILE" | sed 's/^  - "//; s/"$//'
  fi
  exit "$inherit_rc"
fi

plugin_map_count() {
  PLUGIN_NAME="$1" yq '[.plugins[]? | select(type == "!!map" and has(strenv(PLUGIN_NAME)))] | length' "$MKDOCS"
}

plugin_scalar_count() {
  PLUGIN_NAME="$1" yq '[.plugins[]? | select(type == "!!str" and . == strenv(PLUGIN_NAME))] | length' "$MKDOCS"
}

plugin_present() {
  maps="$(plugin_map_count "$1")"
  scalars="$(plugin_scalar_count "$1")"
  [ $((maps + scalars)) -gt 0 ]
}

HAS_I18N=0
HAS_LLMSTXT=0
plugin_present i18n && HAS_I18N=1
plugin_present llmstxt && HAS_LLMSTXT=1

# This migration intentionally leaves monolingual and i18n-without-llmstxt
# sites alone. They do not hit the last-locale-overwrites-root-output bug.
if [ "$HAS_I18N" = "0" ] || [ "$HAS_LLMSTXT" = "0" ]; then
  if [ "$JSON" = "1" ]; then
    printf '{"status":"safe","affected":false,"changed":false,"dry_run":%s,"verified":null,"changes":[],"manual_actions":[]}\n' \
      "$([ "$DRY_RUN" = "1" ] && printf true || printf false)"
  else
    printf 'Safe: mkdocs.yml does not enable both i18n and llmstxt.\n'
  fi
  exit 0
fi

NEEDS_CHANGE=0
MANUAL_COUNT=0
YQ_EXPR='.'
CONFIG_CHANGE=0
WORKFLOW_CHANGE=0
MAKEFILE_CHANGE=0
HELPER_CHANGE=0
APPLIED_CHANGE=0
CONFIG_WRITABLE=1
HELPER_READY=0

if [ -L "$MKDOCS" ]; then
  CONFIG_WRITABLE=0
  add_manual "mkdocs.yml is a symlink; replace or edit it manually so migration cannot write outside the repository"
else
  if yq -e '(.docs_dir | tag) == "!ENV" and (.docs_dir | length) == 2 and .docs_dir[0] == "MKDOCS_SITE_BOOTSTRAP_DOCS_DIR" and .docs_dir[1] == "docs"' "$MKDOCS" >/dev/null 2>&1; then
    :
  elif yq -e '(has("docs_dir") == false) or (.docs_dir == null) or (.docs_dir == "docs")' "$MKDOCS" >/dev/null 2>&1; then
    YQ_EXPR="$YQ_EXPR | .docs_dir = [\"MKDOCS_SITE_BOOTSTRAP_DOCS_DIR\", \"docs\"] | .docs_dir tag = \"!ENV\" | .docs_dir style = \"flow\""
    CONFIG_CHANGE=1
    add_change "guard docs_dir with MKDOCS_SITE_BOOTSTRAP_DOCS_DIR"
  else
    add_manual "custom docs_dir is not auto-migrated; use suffix-layout docs/ or add the MKDOCS_SITE_BOOTSTRAP_DOCS_DIR !ENV guard manually"
  fi
fi

guard_plugin() {
  plugin="$1"
  guard_env="$2"
  guard_default="$3"
  maps="$(plugin_map_count "$plugin")"
  scalars="$(plugin_scalar_count "$plugin")"

  if [ "$maps" -eq 0 ] && [ "$scalars" -eq 0 ]; then
    return
  fi
  if [ "$maps" -ne 1 ] || [ "$scalars" -ne 0 ]; then
    add_manual "plugin '$plugin' is not one map-form entry; add enabled: !ENV [$guard_env, $guard_default] manually"
    return
  fi
  if ! PLUGIN_NAME="$plugin" yq -e '[.plugins[]? | select(type == "!!map" and has(strenv(PLUGIN_NAME))) | .[strenv(PLUGIN_NAME)] | select(type == "!!map")] | length == 1' "$MKDOCS" >/dev/null 2>&1; then
    add_manual "plugin '$plugin' has a custom/non-map configuration; add enabled: !ENV [$guard_env, $guard_default] manually"
    return
  fi
  if PLUGIN_NAME="$plugin" GUARD_ENV="$guard_env" GUARD_DEFAULT="$guard_default" \
    yq -e '[.plugins[]? | select(type == "!!map" and has(strenv(PLUGIN_NAME))) | .[strenv(PLUGIN_NAME)].enabled | select((tag == "!ENV") and (length == 2) and (.[0] == strenv(GUARD_ENV)) and (.[1] == env(GUARD_DEFAULT)))] | length == 1' "$MKDOCS" >/dev/null 2>&1; then
    return
  fi
  if PLUGIN_NAME="$plugin" yq -e '[.plugins[]? | select(type == "!!map" and has(strenv(PLUGIN_NAME))) | .[strenv(PLUGIN_NAME)] | has("enabled")] | any' "$MKDOCS" >/dev/null 2>&1; then
    add_manual "plugin '$plugin' already has a custom enabled value; preserve it and add the two-pass environment behavior manually"
    return
  fi
  if [ "$CONFIG_WRITABLE" = "0" ]; then
    add_manual "plugin '$plugin' needs enabled: !ENV [$guard_env, $guard_default], but mkdocs.yml is not a writable regular file"
    return
  fi

  YQ_EXPR="$YQ_EXPR | (.plugins[] | select(type == \"!!map\" and has(\"$plugin\")) | .[\"$plugin\"].enabled) = [\"$guard_env\", $guard_default] | (.plugins[] | select(type == \"!!map\" and has(\"$plugin\")) | .[\"$plugin\"].enabled) tag = \"!ENV\" | (.plugins[] | select(type == \"!!map\" and has(\"$plugin\")) | .[\"$plugin\"].enabled) style = \"flow\""
  CONFIG_CHANGE=1
  add_change "add $guard_env guard to plugin '$plugin'"
}

guard_plugin i18n MKDOCS_SITE_BOOTSTRAP_I18N_ENABLED true
guard_plugin llmstxt MKDOCS_SITE_BOOTSTRAP_LLMSTXT_ENABLED false
guard_plugin copy-to-llm MKDOCS_SITE_BOOTSTRAP_COPY_TO_LLM_ENABLED true
guard_plugin social MKDOCS_SITE_BOOTSTRAP_SOCIAL_ENABLED true

SNIPPETS_MAP_COUNT=$(yq '[.markdown_extensions[]? | select(type == "!!map" and has("pymdownx.snippets"))] | length' "$MKDOCS" 2>/dev/null || printf '0')
SNIPPETS_SCALAR_COUNT=$(yq '[.markdown_extensions[]? | select(type == "!!str" and . == "pymdownx.snippets")] | length' "$MKDOCS" 2>/dev/null || printf '0')
if [ "$SNIPPETS_MAP_COUNT" -eq 1 ] && [ "$SNIPPETS_SCALAR_COUNT" -eq 0 ]; then
  if yq -e '
    [.markdown_extensions[]? | select(type == "!!map" and has("pymdownx.snippets")) |
      .["pymdownx.snippets"].base_path |
      select((type == "!!seq") and (length == 2) and (.[0] == ".") and
        ((.[1] | tag) == "!ENV") and (.[1] | length) == 2 and
        .[1][0] == "MKDOCS_SITE_BOOTSTRAP_DOCS_DIR" and .[1][1] == "docs")
    ] | length == 1
  ' "$MKDOCS" >/dev/null 2>&1; then
    :
  elif yq -e '
    [.markdown_extensions[]? | select(type == "!!map" and has("pymdownx.snippets")) |
      .["pymdownx.snippets"].base_path |
      select((type == "!!seq") and (length == 3) and
        (.[0] == ".") and (.[1] == "docs") and (.[2] == "docs/_snippets"))
    ] | length == 1
  ' "$MKDOCS" >/dev/null 2>&1; then
    if [ "$CONFIG_WRITABLE" = "1" ]; then
      YQ_EXPR="$YQ_EXPR | (.markdown_extensions[] | select(type == \"!!map\" and has(\"pymdownx.snippets\")) | .[\"pymdownx.snippets\"].base_path) = [\".\", [\"MKDOCS_SITE_BOOTSTRAP_DOCS_DIR\", \"docs\"]] | (.markdown_extensions[] | select(type == \"!!map\" and has(\"pymdownx.snippets\")) | .[\"pymdownx.snippets\"].base_path[1]) tag = \"!ENV\" | (.markdown_extensions[] | select(type == \"!!map\" and has(\"pymdownx.snippets\")) | .[\"pymdownx.snippets\"].base_path[1]) style = \"flow\""
      CONFIG_CHANGE=1
      add_change "replace legacy pymdownx.snippets base_path with the staged docs-dir guard"
    else
      add_manual "legacy pymdownx.snippets.base_path must use MKDOCS_SITE_BOOTSTRAP_DOCS_DIR, but mkdocs.yml is not a writable regular file"
    fi
  else
    add_manual "custom pymdownx.snippets.base_path is not auto-migrated; ensure every docs path uses MKDOCS_SITE_BOOTSTRAP_DOCS_DIR"
  fi
elif [ $((SNIPPETS_MAP_COUNT + SNIPPETS_SCALAR_COUNT)) -gt 0 ]; then
  add_manual "pymdownx.snippets has a custom or duplicated shape; configure its base_path for the staged docs directory manually"
fi

I18N_STRUCTURE=$(yq -r '(.plugins[]? | select(type == "!!map" and has("i18n")) | .i18n.docs_structure) // ""' "$MKDOCS" 2>/dev/null || printf '')
if [ "$I18N_STRUCTURE" != "suffix" ]; then
  add_manual "i18n.docs_structure must be suffix for the managed two-pass build; folder layout requires a manual migration"
fi
DEFAULT_LOCALE_COUNT=$(yq '[.plugins[]? | select(type == "!!map" and has("i18n")) | .i18n.languages[]? | select(.default == true)] | length' "$MKDOCS" 2>/dev/null || printf '0')
if [ "$DEFAULT_LOCALE_COUNT" -ne 1 ]; then
  add_manual "i18n.languages must identify exactly one default locale before migration"
fi
if [ -L "$TARGET/docs" ]; then
  add_manual "docs/ is a symlink; move it inside the repository or migrate the source tree manually"
elif [ -d "$TARGET/docs" ]; then
  LOCALES_FILE="$STATE_DIR/non-default-locales"
  yq -r '.plugins[]? | select(type == "!!map" and has("i18n")) | .i18n.languages[]? | select(.default != true) | .locale' \
    "$MKDOCS" > "$LOCALES_FILE" 2>/dev/null || :
  while IFS= read -r locale; do
    [ -n "$locale" ] || continue
    LOCALIZED_FILES="$STATE_DIR/localized-files"
    find "$TARGET/docs" -type f \( -name "*.$locale.md" -o -name "*.$locale.markdown" \) \
      > "$LOCALIZED_FILES" 2>/dev/null || :
    while IFS= read -r localized_file; do
      [ -n "$localized_file" ] || continue
      LINK_TARGETS="$STATE_DIR/link-targets"
      grep -Eo '\]\([^)]*\)' "$localized_file" 2>/dev/null \
        | sed -e 's/^](//' -e 's/)$//' > "$LINK_TARGETS" || :
      while IFS= read -r link_target; do
        [ -n "$link_target" ] || continue
        case "$link_target" in
          http://*|https://*|mailto:*|/*|\#*) continue ;;
          *' '*|*'"'*) continue ;;
        esac
        clean_target="${link_target%%#*}"
        clean_target="${clean_target%%\?*}"
        clean_target="${clean_target#<}"
        clean_target="${clean_target%>}"
        bad_generated_link=0
        case "$clean_target" in
          llms.txt|llms-full.txt|*/llms.txt|*/llms-full.txt)
            bad_generated_link=1
            ;;
          */index.md)
            resolved_target="$(dirname "$localized_file")/$clean_target"
            if [ ! -f "$resolved_target" ]; then
              route_source="${resolved_target%/index.md}"
              if [ -f "$route_source.md" ] || [ -f "$route_source.markdown" ]; then
                bad_generated_link=1
              fi
            fi
            ;;
        esac
        if [ "$bad_generated_link" = "1" ]; then
          relative_file="${localized_file#"$TARGET"/}"
          add_manual "localized page $relative_file uses relative generated link '$link_target'; replace it with the root/site_url absolute llms or sidecar URL"
        fi
      done < "$LINK_TARGETS"
    done < "$LOCALIZED_FILES"
  done < "$LOCALES_FILE"
fi

if yq -e '.theme.features // [] | contains(["content.action.edit"])' "$MKDOCS" >/dev/null 2>&1; then
  :
elif yq -e '(.theme | type) == "!!map" and ((.theme.features == null) or ((.theme.features | type) == "!!seq"))' "$MKDOCS" >/dev/null 2>&1; then
  if [ "$CONFIG_WRITABLE" = "1" ]; then
    YQ_EXPR="$YQ_EXPR | .theme.features = ((.theme.features // []) + [\"content.action.edit\"])"
    CONFIG_CHANGE=1
    add_change "enable Material content.action.edit for locale-correct raw Markdown links"
  else
    add_manual "add content.action.edit to theme.features manually because mkdocs.yml is not a writable regular file"
  fi
else
  add_manual "theme.features has a custom shape; add content.action.edit manually"
fi

HELPER="$TARGET/scripts/build-docs-site.py"
if [ ! -f "$CANONICAL_HELPER" ]; then
  add_manual "canonical build helper is missing from the installed skill; update/reinstall mkdocs-site-bootstrap"
elif [ ! -e "$HELPER" ]; then
  HELPER_CHANGE=1
  HELPER_READY=1
  add_change "install managed scripts/build-docs-site.py"
elif [ -L "$HELPER" ]; then
  add_manual "scripts/build-docs-site.py is a symlink; replace it manually with the managed helper"
elif grep -Fq "$MANAGED_MARKER" "$HELPER"; then
  HELPER_READY=1
  if ! cmp -s "$CANONICAL_HELPER" "$HELPER"; then
    HELPER_CHANGE=1
    add_change "update managed scripts/build-docs-site.py"
  fi
else
  add_manual "scripts/build-docs-site.py exists without the managed marker; it was not overwritten"
fi

# Do not switch CI/Makefile to the helper while an earlier custom shape or
# collision still needs human work. This keeps --apply from activating a
# build command that is known to be incomplete.
AUTO_ACTIVATE=1
if [ "$MANUAL_COUNT" -gt 0 ] || [ "$HELPER_READY" = "0" ]; then
  AUTO_ACTIVATE=0
fi

WORKFLOW="$TARGET/.github/workflows/docs.yml"
if [ -e "$WORKFLOW" ]; then
  if [ -L "$WORKFLOW" ]; then
    add_manual ".github/workflows/docs.yml is a symlink; update its build command and path filter manually"
  else
    old_workflow_count="$(grep -Ec '^[[:space:]]*-[[:space:]]*run:[[:space:]]*uv run mkdocs build( --strict)?[[:space:]]*$' "$WORKFLOW" || true)"
    new_workflow_count="$(grep -Ec '^[[:space:]]*-[[:space:]]*run:[[:space:]]*uv run python scripts/build-docs-site.py[[:space:]]*$' "$WORKFLOW" || true)"
    any_workflow_count="$(grep -Ec '^[[:space:]]*-[[:space:]]*run:.*(mkdocs build|build-docs-site\.py)' "$WORKFLOW" || true)"
    if [ "$old_workflow_count" -eq 1 ] && [ "$new_workflow_count" -eq 0 ] && [ "$any_workflow_count" -eq 1 ]; then
      if [ "$AUTO_ACTIVATE" = "1" ]; then
        WORKFLOW_CHANGE=1
        add_change "replace the generated Docs workflow build command with the managed helper"
      else
        add_manual "Docs workflow was left unchanged until the earlier manual migration actions are resolved"
      fi
    elif [ "$new_workflow_count" -eq 1 ] && [ "$old_workflow_count" -eq 0 ] && [ "$any_workflow_count" -eq 1 ]; then
      :
    else
      add_manual "Docs workflow build command is custom or ambiguous; invoke uv run python scripts/build-docs-site.py explicitly"
    fi

    if [ "$MANUAL_COUNT" -gt 0 ]; then
      AUTO_ACTIVATE=0
    fi
    if grep -Eq "^[[:space:]]*- ['\"]scripts/build-docs-site\\.py['\"][[:space:]]*$" "$WORKFLOW"; then
      :
    elif [ "$(grep -Ec "^[[:space:]]*- 'uv\.lock'[[:space:]]*$" "$WORKFLOW" || true)" -eq 1 ]; then
      if [ "$AUTO_ACTIVATE" = "1" ]; then
        WORKFLOW_CHANGE=1
        add_change "add scripts/build-docs-site.py to the Docs workflow path filter"
      else
        add_manual "Docs workflow helper path filter was left unchanged until the earlier manual migration actions are resolved"
      fi
    else
      add_manual "Docs workflow path filter is custom; add scripts/build-docs-site.py manually"
    fi
  fi
fi

if [ "$MANUAL_COUNT" -gt 0 ]; then
  AUTO_ACTIVATE=0
fi

MAKEFILE="$TARGET/Makefile"
if [ -e "$MAKEFILE" ]; then
  if [ -L "$MAKEFILE" ]; then
    add_manual "Makefile is a symlink; update docs-build manually"
  else
    docs_target_count="$(grep -Ec '^docs-build:[[:space:]]*(#.*)?$' "$MAKEFILE" || true)"
    docs_target_any_count="$(grep -Ec '^docs-build:' "$MAKEFILE" || true)"
    if [ "$docs_target_count" -eq 1 ]; then
      old_make_count="$(awk '
        /^docs-build:[[:space:]]*(#.*)?$/ { active=1; next }
        active && /^[^[:space:]#][^:]*:/ { active=0 }
        active && /^\tuv run mkdocs build( --strict)?[[:space:]]*$/ { count++ }
        END { print count+0 }
      ' "$MAKEFILE")"
      new_make_count="$(awk '
        /^docs-build:[[:space:]]*(#.*)?$/ { active=1; next }
        active && /^[^[:space:]#][^:]*:/ { active=0 }
        active && /^\tuv run python scripts\/build-docs-site.py[[:space:]]*$/ { count++ }
        END { print count+0 }
      ' "$MAKEFILE")"
      if [ "$old_make_count" -eq 1 ] && [ "$new_make_count" -eq 0 ]; then
        if [ "$AUTO_ACTIVATE" = "1" ]; then
          MAKEFILE_CHANGE=1
          add_change "replace the exact docs-build Makefile command with the managed helper"
        else
          add_manual "Makefile docs-build was left unchanged until the earlier manual migration actions are resolved"
        fi
      elif [ "$new_make_count" -eq 1 ] && [ "$old_make_count" -eq 0 ]; then
        :
      else
        add_manual "Makefile docs-build target is custom or ambiguous; invoke uv run python scripts/build-docs-site.py manually"
      fi
    elif [ "$docs_target_any_count" -gt 0 ]; then
      add_manual "Makefile docs-build target is custom or duplicated; invoke uv run python scripts/build-docs-site.py manually"
    fi
  fi
fi

AFFECTED=0
if [ "$NEEDS_CHANGE" = "1" ] || [ "$MANUAL_COUNT" -gt 0 ]; then
  AFFECTED=1
fi

if [ "$APPLY" = "1" ] && [ "$NEEDS_CHANGE" = "1" ]; then
  if [ "$CONFIG_CHANGE" = "1" ] && [ ! -L "$MKDOCS" ]; then
    if ! yq "$YQ_EXPR" "$MKDOCS" > "$STATE_DIR/mkdocs.yml"; then
      die "yq could not stage the mkdocs.yml migration" 4
    fi
    yq '.' "$STATE_DIR/mkdocs.yml" >/dev/null 2>&1 || \
      die "staged mkdocs.yml did not parse" 4
  fi

  if [ "$WORKFLOW_CHANGE" = "1" ] && [ -f "$WORKFLOW" ] && [ ! -L "$WORKFLOW" ]; then
    sed -E 's|^([[:space:]]*-[[:space:]]*run:[[:space:]]*)uv run mkdocs build( --strict)?[[:space:]]*$|\1uv run python scripts/build-docs-site.py|' \
      "$WORKFLOW" > "$STATE_DIR/docs.yml.step1"
    if grep -Eq "^[[:space:]]*- ['\"]scripts/build-docs-site\\.py['\"][[:space:]]*$" "$STATE_DIR/docs.yml.step1"; then
      cp "$STATE_DIR/docs.yml.step1" "$STATE_DIR/docs.yml"
    else
      awk '
        { print }
        /^[[:space:]]*- '\''uv\.lock'\''[[:space:]]*$/ && !added {
          match($0, /^[[:space:]]*/)
          indent=substr($0, RSTART, RLENGTH)
          print indent "- '\''scripts/build-docs-site.py'\''"
          added=1
        }
      ' "$STATE_DIR/docs.yml.step1" > "$STATE_DIR/docs.yml"
    fi
  fi

  if [ "$MAKEFILE_CHANGE" = "1" ] && [ -f "$MAKEFILE" ] && [ ! -L "$MAKEFILE" ]; then
    awk '
      /^docs-build:[[:space:]]*(#.*)?$/ { active=1; print; next }
      active && /^[^[:space:]#][^:]*:/ { active=0 }
      active && /^\tuv run mkdocs build( --strict)?[[:space:]]*$/ {
        print "\tuv run python scripts/build-docs-site.py"
        next
      }
      { print }
    ' "$MAKEFILE" > "$STATE_DIR/Makefile"
  fi

  if [ "$HELPER_CHANGE" = "1" ] && [ -f "$CANONICAL_HELPER" ]; then
    cp "$CANONICAL_HELPER" "$STATE_DIR/build-docs-site.py"
    chmod +x "$STATE_DIR/build-docs-site.py"
  fi

  if [ "$DRY_RUN" = "0" ]; then
    if [ -f "$STATE_DIR/mkdocs.yml" ]; then
      mv "$STATE_DIR/mkdocs.yml" "$MKDOCS"
      APPLIED_CHANGE=1
    fi
    if [ -f "$STATE_DIR/docs.yml" ]; then
      mv "$STATE_DIR/docs.yml" "$WORKFLOW"
      APPLIED_CHANGE=1
    fi
    if [ -f "$STATE_DIR/Makefile" ]; then
      mv "$STATE_DIR/Makefile" "$MAKEFILE"
      APPLIED_CHANGE=1
    fi
    if [ -f "$STATE_DIR/build-docs-site.py" ]; then
      mkdir -p "$TARGET/scripts"
      mv "$STATE_DIR/build-docs-site.py" "$HELPER"
      chmod +x "$HELPER"
      APPLIED_CHANGE=1
    fi
  fi
fi

VERIFIED_JSON=null
VERIFY_FAILED=0
if [ "$VERIFY" = "1" ] && [ "$DRY_RUN" = "0" ]; then
  if [ ! -f "$HELPER" ] || ! grep -Fq "$MANAGED_MARKER" "$HELPER"; then
    log "Verification cannot start: managed scripts/build-docs-site.py is unavailable."
    VERIFY_FAILED=1
    VERIFIED_JSON=false
  else
    log "Running managed strict two-pass verification..."
    HAS_DOCS_EXTRA=false
    if [ -f "$TARGET/pyproject.toml" ]; then
      HAS_DOCS_EXTRA=$(yq -p=toml -oy -r '.project.optional-dependencies.docs != null' "$TARGET/pyproject.toml" 2>/dev/null || printf false)
    fi
    if [ "$HAS_DOCS_EXTRA" = "true" ]; then
      if (cd "$TARGET" && uv run --extra docs python scripts/build-docs-site.py --target-dir "$TARGET") > "$STATE_DIR/verify.stdout"; then
        VERIFIED_JSON=true
      else
        VERIFY_FAILED=1
        VERIFIED_JSON=false
      fi
    elif (cd "$TARGET" && uv run python scripts/build-docs-site.py --target-dir "$TARGET") > "$STATE_DIR/verify.stdout"; then
      VERIFIED_JSON=true
    else
      log "Verification used the existing environment because pyproject.toml has no [project.optional-dependencies].docs extra."
      log "Install the MkDocs plugins first, or declare the docs extra, then retry --verify."
      VERIFY_FAILED=1
      VERIFIED_JSON=false
    fi
    if [ -s "$STATE_DIR/verify.stdout" ]; then
      log "Build helper result: $(tr '\n' ' ' < "$STATE_DIR/verify.stdout")"
    fi
  fi
fi

CHANGED_JSON=false
if [ "$APPLIED_CHANGE" = "1" ]; then
  CHANGED_JSON=true
fi
DRY_JSON=false
[ "$DRY_RUN" = "0" ] || DRY_JSON=true

if [ "$VERIFY_FAILED" = "1" ]; then
  STATUS=verification_failed
  EXIT_CODE=12
elif [ "$APPLY" = "1" ] && [ "$DRY_RUN" = "0" ] && [ "$MANUAL_COUNT" -gt 0 ]; then
  STATUS=manual_required
  EXIT_CODE=11
elif [ "$APPLY" = "1" ] && [ "$DRY_RUN" = "0" ]; then
  if [ "$AFFECTED" = "1" ]; then
    STATUS=migrated
  else
    STATUS=safe
  fi
  EXIT_CODE=0
elif [ "$AFFECTED" = "1" ]; then
  STATUS=affected
  EXIT_CODE=10
else
  STATUS=safe
  EXIT_CODE=0
fi

if [ "$JSON" = "1" ]; then
  printf '{"status":"%s","affected":%s,"changed":%s,"dry_run":%s,"verified":%s,"changes":' \
    "$STATUS" "$([ "$AFFECTED" = "1" ] && printf true || printf false)" \
    "$CHANGED_JSON" "$DRY_JSON" "$VERIFIED_JSON"
  json_array "$CHANGES_FILE"
  printf ',"manual_actions":'
  json_array "$MANUAL_FILE"
  printf '}\n'
else
  printf 'Status: %s\n' "$STATUS"
  if [ -s "$CHANGES_FILE" ]; then
    printf 'Recognized changes:\n'
    sed 's/^/  - /' "$CHANGES_FILE" | sed 's/^  - "//; s/"$//'
  fi
  if [ -s "$MANUAL_FILE" ]; then
    printf 'Manual actions:\n'
    sed 's/^/  - /' "$MANUAL_FILE" | sed 's/^  - "//; s/"$//'
  fi
fi

exit "$EXIT_CODE"
