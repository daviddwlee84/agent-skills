#!/usr/bin/env bash
# check-commit-msg.sh — validate a commit message header against Conventional Commits.
#
# Bash 3.2 compatible (works on stock macOS).

set -euo pipefail

ALLOWED_TYPES="feat fix docs style refactor perf test build ci chore revert"

usage() {
  cat <<'EOF'
Usage: check-commit-msg.sh [OPTIONS] ["<message>"]
       printf 'feat: add x\n' | check-commit-msg.sh
       check-commit-msg.sh --file .git/COMMIT_EDITMSG

Validate the first line (header) of a commit message against Conventional
Commits: `<type>[(scope)][!]: <subject>`. Reads the message from a positional
argument, --file, or stdin (in that order of precedence).

Structural errors fail (exit 1); stylistic issues (long header, capitalized
subject, trailing period) are warnings on stderr and still pass.

Options:
  --file PATH        Read the message from PATH instead of arg/stdin.
  --types            Print the allowed commit types and exit.
  --help, -h         Show this help and exit.

Output (stdout): a JSON object, e.g.
  {"valid":true,"type":"feat","scope":"auth","breaking":false}

Exit codes:
  0  valid header
  1  invalid header (reason on stderr)
  2  bad arguments / no message provided
EOF
}

log()  { printf '%s\n' "$*" >&2; }
warn() { printf 'warn: %s\n' "$*" >&2; }
die()  { printf 'error: %s\n' "$1" >&2; exit "${2:-1}"; }

FILE=""
ARG_MSG=""
HAVE_ARG=0

while [ $# -gt 0 ]; do
  case "$1" in
    --file)
      shift
      [ $# -gt 0 ] || die "--file needs a path (try --help)" 2
      FILE="$1"; shift ;;
    --types)
      printf '%s\n' $ALLOWED_TYPES
      exit 0 ;;
    --help|-h) usage; exit 0 ;;
    --) shift; if [ $# -gt 0 ]; then ARG_MSG="$1"; HAVE_ARG=1; shift; fi ;;
    -*) die "unknown flag: $1 (try --help)" 2 ;;
    *)  ARG_MSG="$1"; HAVE_ARG=1; shift ;;
  esac
done

# --- acquire the message -----------------------------------------------------
msg=""
if [ -n "$FILE" ]; then
  [ -f "$FILE" ] || die "file not found: $FILE" 2
  msg="$(cat "$FILE")"
elif [ "$HAVE_ARG" = "1" ]; then
  msg="$ARG_MSG"
elif [ ! -t 0 ]; then
  msg="$(cat)"
else
  die "no message provided (pass an argument, --file PATH, or pipe via stdin)" 2
fi

# First non-empty line is the header (skip leading blank lines / comments).
header=""
# shellcheck disable=SC2162
while IFS= read -r line; do
  case "$line" in
    ''|'#'*) continue ;;
    *) header="$line"; break ;;
  esac
done <<EOF
$msg
EOF

[ -n "$header" ] || die "empty commit message" 2

types_re="$(printf '%s' "$ALLOWED_TYPES" | tr ' ' '|')"

# --- structural validation ---------------------------------------------------
if ! printf '%s' "$header" | grep -Eq "^(${types_re})(\([a-z0-9][a-z0-9._/-]*\))?!?: .+"; then
  # Diagnose the most likely cause.
  if ! printf '%s' "$header" | grep -Eq '^[a-z]+(\(|!|:)'; then
    log "invalid: header must start with a lowercase type, e.g. 'feat: ...'"
  elif ! printf '%s' "$header" | grep -Eq "^(${types_re})"; then
    log "invalid: unknown type. Allowed: ${ALLOWED_TYPES}"
  elif ! printf '%s' "$header" | grep -Eq ': .+'; then
    log "invalid: missing ': <subject>' after the type/scope"
  else
    log "invalid: does not match '<type>[(scope)][!]: <subject>'"
  fi
  printf '{"valid":false,"header":"%s"}\n' "$(printf '%s' "$header" | sed 's/\\/\\\\/g; s/"/\\"/g')"
  exit 1
fi

# --- parse the parts ---------------------------------------------------------
type="$(printf '%s' "$header" | sed -E 's/^([a-z]+).*/\1/')"
scope=""
if printf '%s' "$header" | grep -Eq '^[a-z]+\('; then
  scope="$(printf '%s' "$header" | sed -E 's/^[a-z]+\(([a-z0-9._/-]+)\).*/\1/')"
fi
breaking=false
printf '%s' "$header" | grep -Eq '^[a-z]+(\([a-z0-9._/-]+\))?!:' && breaking=true

subject="$(printf '%s' "$header" | sed -E 's/^[a-z]+(\([a-z0-9._/-]+\))?!?: //')"

# --- stylistic warnings (do not fail) ---------------------------------------
if [ "${#header}" -gt 72 ]; then
  warn "header is ${#header} chars (aim for <=72)"
fi
case "$subject" in
  [A-Z]*) warn "subject starts with a capital ('$subject') — prefer lowercase imperative" ;;
esac
case "$subject" in
  *.) warn "subject ends with a period — drop it" ;;
esac

bnote=""
[ "$breaking" = "true" ] && bnote=" breaking=true"
log "valid: type=${type}${scope:+ scope=${scope}}${bnote}"
printf '{"valid":true,"type":"%s","scope":"%s","breaking":%s}\n' "$type" "$scope" "$breaking"
