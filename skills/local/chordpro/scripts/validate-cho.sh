#!/usr/bin/env bash
# validate-cho.sh — Validate a ChordPro file by strict-parsing it with the chordpro CLI.
#
# The verify loop for this skill: never hand back an unvalidated .cho. Runs
# `chordpro --strict` and reports whether the file parses cleanly. Data (a JSON
# verdict) goes to stdout; human notes and parser warnings go to stderr.
#
# Bash 3.2 compatible (works on stock macOS).

set -euo pipefail

usage() {
  cat <<'EOF'
Usage: validate-cho.sh [OPTIONS] <file.cho>

Strict-parse a ChordPro file and report validity. Emits a JSON verdict on stdout
and any parser warnings on stderr.

Options:
  --help, -h         Show this help and exit.

Examples:
  validate-cho.sh song.cho

Verdict (stdout):
  {"file":"song.cho","valid":true,"warnings":0}

Exit codes:
  0  file parses (valid; warnings may still be present — see stderr)
  1  invalid arguments
  2  file not found
  3  file failed to parse, OR chordpro is not installed (see stderr for guidance)
EOF
}

log() { printf '%s\n' "$*" >&2; }
die() { printf 'error: %s\n' "$*" >&2; exit "${2:-1}"; }

FILE=""
while [ $# -gt 0 ]; do
  case "$1" in
    --help|-h) usage; exit 0 ;;
    --) shift; [ $# -gt 0 ] && FILE="$1"; break ;;
    -*) die "unknown flag: $1 (try --help)" 1 ;;
    *)
      if [ -n "$FILE" ]; then die "only one file allowed (got '$FILE' and '$1')" 1; fi
      FILE="$1"; shift ;;
  esac
done

[ -n "$FILE" ] || die "missing <file.cho> (try --help)" 1
[ -f "$FILE" ] || die "file not found: $FILE" 2

if ! command -v chordpro >/dev/null 2>&1; then
  log "chordpro CLI not found on PATH. Install it (macOS has no Homebrew formula):"
  log "  brew install perl cpanminus && cpanm App::Music::ChordPro"
  log "Then re-run. The file was not validated; the ChordPro format is still"
  log "human-checkable by eye (see references/chordpro-format.md)."
  printf '{"file":"%s","valid":null,"error":"chordpro-not-installed"}\n' "$FILE"
  exit 3
fi

tmperr="$(mktemp)"
trap 'rm -f "$tmperr"' EXIT

# --generate=Text -o /dev/null discards the render so stdout stays clean; strict
# mode surfaces malformed/unknown directives as stderr warnings.
set +e
chordpro --strict --generate=Text -o /dev/null "$FILE" 2>"$tmperr"
rc=$?
set -e

warncount="$(grep -c . "$tmperr" 2>/dev/null || true)"
[ -n "$warncount" ] || warncount=0

# Demystify the most common false-alarm: strict mode warns "Unknown chord" for a
# valid chord it has no built-in diagram for (e.g. Em/C#, F#m7b5). It renders fine.
if grep -q "Unknown chord" "$tmperr" 2>/dev/null; then
  log 'note: "Unknown chord" = no built-in diagram for a valid chord — add a {define} or ignore (not a parse error).'
fi

if [ "$rc" -eq 0 ]; then
  if [ "$warncount" -gt 0 ]; then
    log "PASS (with $warncount warning line(s) — review below): $FILE"
    cat "$tmperr" >&2
  else
    log "PASS: $FILE parses cleanly"
  fi
  printf '{"file":"%s","valid":true,"warnings":%s}\n' "$FILE" "$warncount"
  exit 0
else
  log "FAIL: $FILE did not parse (chordpro exit=$rc)"
  cat "$tmperr" >&2
  printf '{"file":"%s","valid":false,"warnings":%s}\n' "$FILE" "$warncount"
  exit 3
fi
