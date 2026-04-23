#!/usr/bin/env bash
# add-docs-page.sh — Create a new docs/ page and insert it into mkdocs.yml nav.
#
# Bash 3.2 compatible. Requires `yq` (mikefarah/yq v4+) for nav editing.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
SKILL_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
ASSETS="$SKILL_DIR/assets"

usage() {
  cat <<'EOF'
Usage: add-docs-page.sh [OPTIONS]

Create docs/<section>/<slug>.md from a template and insert a nav entry into
mkdocs.yml under the matching section heading.

Options:
  --section NAME      Section name (must match an existing top-level nav section
                      heading in mkdocs.yml, e.g. "Workflows", "Reference").
                      Use "_root" to add at top level (no section).
  --title TITLE       Display title (e.g., "My new workflow"). Required.
  --slug SLUG         Filename slug without .md (default: derived from --title).
  --template PATH     Page template (default: skill's assets/page.md.template).
  --target-dir DIR    Repo root (default: walk up from CWD looking for mkdocs.yml).
  --dry-run           Print actions without writing.
  --force             Overwrite existing page file.
  --help, -h          Show this help and exit.

Examples:
  add-docs-page.sh --section Workflows --title "My new workflow"
  add-docs-page.sh --section Reference --title "API schema" --slug api-schema
  add-docs-page.sh --section _root --title "About" --slug about

Exit codes:
  0  success (idempotent: re-running with same slug is a no-op)
  1  invalid arguments
  2  mkdocs.yml not found
  3  refusing to overwrite (use --force)
  4  yq error or section not found in nav
EOF
}

log()  { printf '%s\n' "$*" >&2; }
die()  { printf 'error: %s\n' "$*" >&2; exit "${2:-1}"; }

SECTION=""
TITLE=""
SLUG=""
TEMPLATE=""
TARGET=""
DRY_RUN=0
FORCE=0

while [ $# -gt 0 ]; do
  case "$1" in
    --section)     SECTION="${2:-}"; shift 2 ;;
    --title)       TITLE="${2:-}"; shift 2 ;;
    --slug)        SLUG="${2:-}"; shift 2 ;;
    --template)    TEMPLATE="${2:-}"; shift 2 ;;
    --target-dir)  TARGET="${2:-}"; shift 2 ;;
    --dry-run)     DRY_RUN=1; shift ;;
    --force)       FORCE=1; shift ;;
    --help|-h)     usage; exit 0 ;;
    -*)            die "unknown flag: $1 (try --help)" 1 ;;
    *)             die "unexpected positional argument: $1" 1 ;;
  esac
done

[ -n "$SECTION" ] || die "--section is required (use _root for top-level)" 1
[ -n "$TITLE" ]   || die "--title is required" 1

command -v yq >/dev/null 2>&1 || die "yq not found in PATH (install: brew install yq)" 4

# Resolve target.
if [ -z "$TARGET" ]; then
  cur="$(pwd)"
  while [ "$cur" != "/" ]; do
    if [ -f "$cur/mkdocs.yml" ]; then TARGET="$cur"; break; fi
    cur="$(dirname "$cur")"
  done
  [ -n "$TARGET" ] || die "could not find mkdocs.yml walking up from $(pwd)" 2
fi
[ -f "$TARGET/mkdocs.yml" ] || die "no mkdocs.yml in $TARGET" 2

# Derive slug from title if not given.
if [ -z "$SLUG" ]; then
  SLUG=$(printf '%s' "$TITLE" | tr '[:upper:]' '[:lower:]' | tr -cs '[:alnum:]' '-' | sed 's/^-//; s/-$//')
fi

# Compute paths.
if [ "$SECTION" = "_root" ]; then
  REL_PATH="${SLUG}.md"
else
  # Section dir = lowercased section name (matches our convention).
  SECTION_DIR=$(printf '%s' "$SECTION" | tr '[:upper:]' '[:lower:]' | tr ' ' '-')
  REL_PATH="${SECTION_DIR}/${SLUG}.md"
fi
ABS_PATH="$TARGET/docs/$REL_PATH"

[ -n "$TEMPLATE" ] || TEMPLATE="$ASSETS/page.md.template"
[ -f "$TEMPLATE" ] || die "template not found: $TEMPLATE" 4

# --- 1. Create page file ---
if [ -e "$ABS_PATH" ] && [ "$FORCE" = "0" ]; then
  log "Page already exists: $ABS_PATH (use --force to overwrite)"
  log "Skipping page creation; will still ensure nav entry."
else
  if [ "$DRY_RUN" = "1" ]; then
    log "[dry-run] mkdir -p $(dirname "$ABS_PATH"); cp $TEMPLATE → $ABS_PATH"
  else
    mkdir -p "$(dirname "$ABS_PATH")"
    cp "$TEMPLATE" "$ABS_PATH"
    sed -i.bak \
      -e "s|{{PAGE_TITLE}}|${TITLE}|g" \
      "$ABS_PATH"
    rm -f "${ABS_PATH}.bak"
    log "Created: $ABS_PATH"
  fi
fi

# --- 2. Insert into mkdocs.yml nav ---
MKDOCS="$TARGET/mkdocs.yml"

# Idempotency check: does the nav already mention this path?
if grep -qF "$REL_PATH" "$MKDOCS"; then
  log "Nav already references $REL_PATH — no-op."
  printf '{"page":"%s","section":"%s","status":"already_exists"}\n' "$REL_PATH" "$SECTION"
  exit 0
fi

if [ "$SECTION" = "_root" ]; then
  EXPR=".nav += [{\"$TITLE\": \"$REL_PATH\"}]"
else
  # Find the index of the section in nav (top-level dict whose only key is $SECTION).
  IDX=$(SEC="$SECTION" yq 'env(SEC) as $s | [.nav[] | keys | .[0]] | to_entries | map(select(.value == $s)) | .[0].key' \
    "$MKDOCS" 2>/dev/null || echo "null")
  if [ "$IDX" = "null" ] || [ -z "$IDX" ]; then
    EXISTING_SECTIONS=$(yq '[.nav[] | keys | .[0]] | join(",")' "$MKDOCS" 2>/dev/null || echo "?")
    die "section '$SECTION' not found at top of nav: in $MKDOCS (existing: $EXISTING_SECTIONS)" 4
  fi
  EXPR=".nav[$IDX].\"$SECTION\" += [{\"$TITLE\": \"$REL_PATH\"}]"
fi

if [ "$DRY_RUN" = "1" ]; then
  log "[dry-run] yq -i '$EXPR' $MKDOCS"
else
  TMP="${MKDOCS}.tmp.$$"
  yq "$EXPR" "$MKDOCS" > "$TMP" || { rm -f "$TMP"; die "yq failed: $EXPR" 4; }
  mv "$TMP" "$MKDOCS"
  log "Updated nav in: $MKDOCS"
fi

printf '{"page":"%s","section":"%s","status":"created"}\n' "$REL_PATH" "$SECTION"
