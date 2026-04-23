#!/usr/bin/env bash
# new-skill.sh — Scaffold a new local skill under skills/local/<name>/.
#
# Bash 3.2 compatible (works on stock macOS).

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
SKILL_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
ASSETS_DIR="$SKILL_DIR/assets"

usage() {
  cat <<'EOF'
Usage: new-skill.sh [OPTIONS] <skill-name>

Scaffold a new agent skill under skills/local/<skill-name>/ with the standard
layout (SKILL.md, references/, scripts/, assets/) seeded from skill-author's
templates.

Options:
  --vendor           Place under skills/vendor/<name>/ instead of skills/local/.
                     (Rare — vendored skills normally come via vendor.yaml.)
  --root DIR         Repo root (default: walk up from CWD looking for skills/).
  --dry-run          Print what would be created without writing.
  --force            Overwrite if the target directory already exists.
  --help, -h         Show this help and exit.

Examples:
  bash new-skill.sh mkdocs-site-bootstrap
  bash new-skill.sh --dry-run my-experiment
  bash new-skill.sh --root /path/to/repo my-skill

Exit codes:
  0  success
  1  invalid arguments
  2  target already exists (use --force to overwrite)
  3  could not find a `skills/` directory
EOF
}

log()  { printf '%s\n' "$*" >&2; }
die()  { printf 'error: %s\n' "$*" >&2; exit "${2:-1}"; }

NAME=""
ROOT=""
DRY_RUN=0
FORCE=0
SUBDIR="local"

while [ $# -gt 0 ]; do
  case "$1" in
    --vendor)  SUBDIR="vendor"; shift ;;
    --root)    ROOT="${2:-}"; shift 2 ;;
    --dry-run) DRY_RUN=1; shift ;;
    --force)   FORCE=1; shift ;;
    --help|-h) usage; exit 0 ;;
    -*)        die "unknown flag: $1 (try --help)" 1 ;;
    *)
      if [ -n "$NAME" ]; then
        die "only one skill name allowed (got '$NAME' and '$1')" 1
      fi
      NAME="$1"; shift
      ;;
  esac
done

[ -n "$NAME" ] || die "missing <skill-name> (try --help)" 1

# Validate name (kebab-case, no spaces, no leading dots).
case "$NAME" in
  -*|.*) die "invalid skill name: '$NAME' (cannot start with '-' or '.')" 1 ;;
  *[!a-zA-Z0-9_-]*) die "invalid skill name: '$NAME' (use a-z, 0-9, _, -)" 1 ;;
esac

# Discover repo root if not given.
if [ -z "$ROOT" ]; then
  cur="$(pwd)"
  while [ "$cur" != "/" ]; do
    if [ -d "$cur/skills" ]; then ROOT="$cur"; break; fi
    cur="$(dirname "$cur")"
  done
fi
[ -n "$ROOT" ] || die "could not find a 'skills/' directory walking up from $(pwd) (use --root)" 3
[ -d "$ROOT/skills" ] || die "expected $ROOT/skills/ to exist" 3

TARGET="$ROOT/skills/$SUBDIR/$NAME"

if [ -e "$TARGET" ] && [ "$FORCE" = "0" ]; then
  die "target already exists: $TARGET (use --force to overwrite)" 2
fi

create_dir() {
  if [ "$DRY_RUN" = "1" ]; then
    log "[dry-run] mkdir -p $1"
  else
    mkdir -p "$1"
  fi
}

write_template() {
  local src="$1" dst="$2"
  if [ "$DRY_RUN" = "1" ]; then
    log "[dry-run] cp $src → $dst"
    return 0
  fi
  if [ ! -f "$src" ]; then
    die "template missing: $src" 3
  fi
  cp "$src" "$dst"
}

substitute() {
  local file="$1"
  if [ "$DRY_RUN" = "1" ]; then
    log "[dry-run] would substitute placeholders in $file"
    return 0
  fi
  # Bash 3.2 safe: use sed in-place with a backup then remove backup.
  sed -i.bak \
    -e "s/SKILL_NAME_PLACEHOLDER/$NAME/g" \
    -e "s/SKILL_TITLE_PLACEHOLDER/$(printf '%s' "$NAME" | tr '-' ' ')/g" \
    "$file"
  rm -f "${file}.bak"
}

log "Creating skill at: $TARGET"

create_dir "$TARGET"
create_dir "$TARGET/references"
create_dir "$TARGET/scripts"
create_dir "$TARGET/assets"

write_template "$ASSETS_DIR/SKILL.md.template" "$TARGET/SKILL.md"
substitute "$TARGET/SKILL.md"

# Add a .gitkeep so empty subdirs survive `git add`.
if [ "$DRY_RUN" = "0" ]; then
  for sub in references scripts assets; do
    if [ -z "$(ls -A "$TARGET/$sub" 2>/dev/null)" ]; then
      : > "$TARGET/$sub/.gitkeep"
    fi
  done
fi

if [ "$DRY_RUN" = "1" ]; then
  log "Dry run complete. Re-run without --dry-run to actually create files."
  exit 0
fi

# Structured success output for agent consumption.
printf '{"skill":"%s","path":"%s","next_steps":["Edit %s/SKILL.md to fill in description and workflow","Run lint-skill.sh %s to verify"]}\n' \
  "$NAME" "$TARGET" "$TARGET" "$TARGET"
