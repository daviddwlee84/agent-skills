#!/usr/bin/env bash
# lint-skill.sh — Lint a skill directory for quality issues.
#
# Checks:
#   1. Frontmatter & length     — name + description present, description has
#                                  "use when" trigger phrasing, SKILL.md < 500 lines.
#   2. Script hygiene           — every scripts/*.sh has shebang, +x, --help handler.
#   3. Reference reachability   — every references/*.md is mentioned in SKILL.md.
#
# Bash 3.2 compatible (works on stock macOS).

set -euo pipefail

usage() {
  cat <<'EOF'
Usage: lint-skill.sh [OPTIONS] <skill-dir>

Lint a skill directory against agentskills.io best practices.

Options:
  --strict           Treat warnings as errors.
  --quiet            Only print failures (suppress 'ok' lines).
  --json             Emit a JSON summary on stdout (in addition to human output).
  --help, -h         Show this help and exit.

Examples:
  bash lint-skill.sh skills/local/my-skill
  bash lint-skill.sh --strict skills/local/my-skill
  bash lint-skill.sh --json skills/local/my-skill | jq

Exit codes:
  0  all checks passed (warnings allowed unless --strict)
  1  invalid arguments
  2  skill directory not found or missing SKILL.md
  3  one or more lint errors
EOF
}

log()  { printf '%s\n' "$*" >&2; }
die()  { printf 'error: %s\n' "$*" >&2; exit "${2:-1}"; }

STRICT=0
QUIET=0
JSON=0
SKILL_DIR=""

while [ $# -gt 0 ]; do
  case "$1" in
    --strict)  STRICT=1; shift ;;
    --quiet)   QUIET=1; shift ;;
    --json)    JSON=1; shift ;;
    --help|-h) usage; exit 0 ;;
    -*)        die "unknown flag: $1 (try --help)" 1 ;;
    *)
      if [ -n "$SKILL_DIR" ]; then
        die "only one skill directory allowed (got '$SKILL_DIR' and '$1')" 1
      fi
      SKILL_DIR="$1"; shift
      ;;
  esac
done

[ -n "$SKILL_DIR" ] || die "missing <skill-dir> (try --help)" 1
[ -d "$SKILL_DIR" ] || die "not a directory: $SKILL_DIR" 2
[ -f "$SKILL_DIR/SKILL.md" ] || die "no SKILL.md in $SKILL_DIR" 2

ERRORS=0
WARNINGS=0
ERROR_MSGS=()
WARNING_MSGS=()

emit_ok()   { [ "$QUIET" = "1" ] || printf '  ok    %s\n' "$*"; }
emit_warn() {
  printf '  WARN  %s\n' "$*"
  WARNINGS=$((WARNINGS + 1))
  WARNING_MSGS+=("$*")
}
emit_err()  {
  printf '  FAIL  %s\n' "$*"
  ERRORS=$((ERRORS + 1))
  ERROR_MSGS+=("$*")
}

# ----------------------------------------------------------------------
# Check 1: Frontmatter & length
# ----------------------------------------------------------------------
echo "Frontmatter & length:"

SKILL_MD="$SKILL_DIR/SKILL.md"

# Extract frontmatter (between first two `---` lines).
FM_START=$(awk '/^---$/{print NR; exit}' "$SKILL_MD" || true)
FM_END=$(awk -v start="${FM_START:-0}" 'NR>start && /^---$/{print NR; exit}' "$SKILL_MD" || true)

if [ -z "$FM_START" ] || [ -z "$FM_END" ] || [ "$FM_START" != "1" ]; then
  emit_err "SKILL.md missing YAML frontmatter (must start with '---' on line 1)"
else
  emit_ok "frontmatter delimiters present"

  FM=$(sed -n "${FM_START},${FM_END}p" "$SKILL_MD")

  if printf '%s\n' "$FM" | grep -qE '^name:[[:space:]]*[^[:space:]]'; then
    NAME=$(printf '%s\n' "$FM" | sed -nE 's/^name:[[:space:]]*(.+)$/\1/p' | head -n1)
    emit_ok "name field present: $NAME"
    # Compare against directory basename.
    BASENAME=$(basename "$SKILL_DIR")
    if [ "$NAME" != "$BASENAME" ]; then
      emit_warn "name '$NAME' does not match directory '$BASENAME'"
    fi
    # Reject placeholder.
    case "$NAME" in
      *PLACEHOLDER*) emit_err "name still contains PLACEHOLDER text" ;;
    esac
  else
    emit_err "frontmatter missing 'name:' field"
  fi

  if printf '%s\n' "$FM" | grep -qE '^description:[[:space:]]*[^[:space:]]'; then
    DESC=$(printf '%s\n' "$FM" | sed -nE 's/^description:[[:space:]]*(.+)$/\1/p' | head -n1)
    DESC_LEN=${#DESC}
    emit_ok "description field present (${DESC_LEN} chars)"
    case "$DESC" in
      *PLACEHOLDER*) emit_err "description still contains PLACEHOLDER text" ;;
    esac
    # Check for trigger-phrase signal.
    if printf '%s\n' "$DESC" | grep -qiE '\b(use when|use whenever|use this|trigger|invoke when)\b'; then
      emit_ok "description includes trigger phrase ('use when' or similar)"
    else
      emit_warn "description lacks an explicit trigger phrase like 'Use when...'; this hurts triggering"
    fi
    # Length sanity.
    if [ "$DESC_LEN" -lt 80 ]; then
      emit_warn "description is short (${DESC_LEN} chars); consider naming more concrete trigger contexts"
    fi
  else
    emit_err "frontmatter missing 'description:' field"
  fi
fi

# Length check.
LINES=$(wc -l < "$SKILL_MD" | tr -d ' ')
if [ "$LINES" -lt 500 ]; then
  emit_ok "SKILL.md is ${LINES} lines (< 500)"
elif [ "$LINES" -lt 700 ]; then
  emit_warn "SKILL.md is ${LINES} lines (recommended <500; move detail to references/)"
else
  emit_err "SKILL.md is ${LINES} lines (>700 is hurting context budget; split into references/)"
fi

# ----------------------------------------------------------------------
# Check 2: Script hygiene
# ----------------------------------------------------------------------
echo
echo "Script hygiene:"

if [ -d "$SKILL_DIR/scripts" ]; then
  HAS_SCRIPTS=0
  for script in "$SKILL_DIR"/scripts/*.sh; do
    [ -e "$script" ] || continue
    HAS_SCRIPTS=1
    NAME=$(basename "$script")

    # Shebang on line 1.
    FIRST_LINE=$(head -n1 "$script")
    case "$FIRST_LINE" in
      "#!"*) emit_ok "$NAME has shebang" ;;
      *)     emit_err "$NAME missing shebang on line 1" ;;
    esac

    # Executable bit.
    if [ -x "$script" ]; then
      emit_ok "$NAME is executable"
    else
      emit_err "$NAME is not executable (chmod +x)"
    fi

    # --help handler (look for the literal flag, not just the word "help").
    if grep -qE -- '--help' "$script"; then
      emit_ok "$NAME handles --help"
    else
      emit_warn "$NAME has no --help handler"
    fi
  done

  # Also lint .py scripts for shebang/+x/argparse-help.
  for script in "$SKILL_DIR"/scripts/*.py; do
    [ -e "$script" ] || continue
    HAS_SCRIPTS=1
    NAME=$(basename "$script")

    FIRST_LINE=$(head -n1 "$script")
    case "$FIRST_LINE" in
      "#!"*) emit_ok "$NAME has shebang" ;;
      *)     emit_warn "$NAME missing shebang (less critical for .py if invoked via 'python …' / 'uv run …')" ;;
    esac

    if [ -x "$script" ]; then
      emit_ok "$NAME is executable"
    else
      emit_warn "$NAME is not executable"
    fi

    if grep -qE 'argparse|click|typer|--help' "$script"; then
      emit_ok "$NAME appears to expose --help"
    else
      emit_warn "$NAME has no obvious --help mechanism"
    fi
  done

  if [ "$HAS_SCRIPTS" = "0" ]; then
    emit_ok "scripts/ exists but is empty (no .sh/.py files to check)"
  fi
else
  emit_ok "no scripts/ directory (nothing to check)"
fi

# ----------------------------------------------------------------------
# Check 3: Reference reachability
# ----------------------------------------------------------------------
echo
echo "Reference reachability:"

if [ -d "$SKILL_DIR/references" ]; then
  HAS_REFS=0
  for ref in "$SKILL_DIR"/references/*.md; do
    [ -e "$ref" ] || continue
    HAS_REFS=1
    REF_BASE=$(basename "$ref")
    # Look for the filename mentioned anywhere in SKILL.md.
    if grep -qF "$REF_BASE" "$SKILL_MD"; then
      emit_ok "$REF_BASE is referenced from SKILL.md"
    else
      emit_warn "$REF_BASE is not mentioned in SKILL.md (dead reference?)"
    fi
  done

  if [ "$HAS_REFS" = "0" ]; then
    emit_ok "references/ exists but is empty"
  fi
else
  emit_ok "no references/ directory (nothing to check)"
fi

# ----------------------------------------------------------------------
# Summary
# ----------------------------------------------------------------------
echo
echo "Summary:"
echo "  errors:   $ERRORS"
echo "  warnings: $WARNINGS"

if [ "$JSON" = "1" ]; then
  # Build JSON arrays manually (bash 3.2 safe).
  printf '{"skill_dir":"%s","errors":%d,"warnings":%d,"error_messages":[' \
    "$SKILL_DIR" "$ERRORS" "$WARNINGS"
  first=1
  for msg in ${ERROR_MSGS[@]+"${ERROR_MSGS[@]}"}; do
    if [ "$first" = "1" ]; then first=0; else printf ','; fi
    printf '"%s"' "$(printf '%s' "$msg" | sed 's/"/\\"/g')"
  done
  printf '],"warning_messages":['
  first=1
  for msg in ${WARNING_MSGS[@]+"${WARNING_MSGS[@]}"}; do
    if [ "$first" = "1" ]; then first=0; else printf ','; fi
    printf '"%s"' "$(printf '%s' "$msg" | sed 's/"/\\"/g')"
  done
  printf ']}\n'
fi

if [ "$ERRORS" -gt 0 ]; then
  exit 3
fi
if [ "$STRICT" = "1" ] && [ "$WARNINGS" -gt 0 ]; then
  exit 3
fi
exit 0
