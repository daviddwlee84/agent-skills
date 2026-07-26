#!/usr/bin/env bash
# run-and-mark.sh — run a long command as a child, block until it exits, and
# record completion durably.
#
# Launch this ONCE in the background (e.g. your agent harness's background
# shell flag). The harness wakes you when it exits; you never poll.
#
# The command is run as a *child of this script* so plain `wait` suffices —
# there is no portable way to wait on a foreign pid (`tail --pid` is GNU-only,
# macOS has neither that nor flock/fswatch).
#
# Bash 3.2 compatible (stock macOS).

set -u

usage() {
  cat <<'EOF'
Usage: run-and-mark.sh --marker-dir DIR --name NAME [OPTIONS] -- <command> [args...]

Run <command>, block until it finishes, and write a durable completion marker
so a later session can learn the outcome without re-running anything.

Required:
  --marker-dir DIR   Directory for marker files. Created if absent.
  --name NAME        Run identifier. Must match [A-Za-z0-9._-]+.

Options:
  --dry-run          Print what would happen; run nothing. Exit 0.
  --help, -h         Show this help and exit.

Everything after `--` is the command. It is executed directly (no shell), so
quote nothing extra:
  run-and-mark.sh --marker-dir .runs --name v2 -- python train.py --epochs 40

Files written (all inside DIR):
  NAME.start         Written immediately: JSON with pid, host, start time, cmd.
  NAME.exit          Written at completion: the exit code, one integer + newline.
  NAME.meta          Written at completion: JSON with the full record.

Both terminal files are written to a .tmp sibling and renamed, so a concurrent
reader never observes a half-written marker. Keep DIR on the same filesystem
you read from — `mv` is only atomic within one filesystem.

Output:
  stdout   one JSON object at completion (the same content as NAME.meta)
  stderr   two lines: one at start, one at completion. Nothing per-tick.

Exit codes:
  <cmd>    the command's own exit code (0 on success)
  1        invalid arguments
  2        marker directory not writable

Note: a shell reports a signal-killed child as 128+signal (137 = SIGKILL,
often the OOM killer). That is preserved in NAME.exit.

Examples:
  run-and-mark.sh --marker-dir .runs --name v2_full -- python train.py
  run-and-mark.sh --marker-dir .runs --name eval --dry-run -- ./eval.sh
  run-and-mark.sh --marker-dir .runs --name sweep -- sbatch --wait sweep.sbatch
EOF
}

die() { printf 'error: %s\n' "$1" >&2; exit "${2:-1}"; }

MARKER_DIR=""
NAME=""
DRY_RUN=0

while [ $# -gt 0 ]; do
  case "$1" in
    --marker-dir) [ $# -ge 2 ] || die "--marker-dir requires a value (try --help)" 1
                  MARKER_DIR="$2"; shift 2 ;;
    --name)       [ $# -ge 2 ] || die "--name requires a value (try --help)" 1
                  NAME="$2"; shift 2 ;;
    --dry-run)    DRY_RUN=1; shift ;;
    --help|-h)    usage; exit 0 ;;
    --)           shift; break ;;
    -*)           die "unknown flag: $1 (try --help)" 1 ;;
    *)            die "unexpected argument '$1' — the command goes after '--'" 1 ;;
  esac
done

[ -n "$MARKER_DIR" ] || die "--marker-dir is required (try --help)" 1
[ -n "$NAME" ]       || die "--name is required (try --help)" 1
[ $# -gt 0 ]         || die "no command given — put it after '--' (try --help)" 1

case "$NAME" in
  *[!A-Za-z0-9._-]*) die "--name '$NAME' has characters outside [A-Za-z0-9._-]" 1 ;;
esac

# JSON string escaping: backslash and double-quote only. Control characters are
# not expected in argv or hostnames; if they appear the field is still parseable
# because we escape the two structural characters.
json_escape() {
  printf '%s' "$1" | sed -e 's/\\/\\\\/g' -e 's/"/\\"/g'
}

# Render the command as a JSON array.
cmd_json() {
  local first=1 arg out=""
  for arg in "$@"; do
    if [ $first -eq 1 ]; then first=0; else out="$out, "; fi
    out="$out\"$(json_escape "$arg")\""
  done
  printf '[%s]' "$out"
}

now_iso() { date -u '+%Y-%m-%dT%H:%M:%SZ'; }

START_FILE="$MARKER_DIR/$NAME.start"
EXIT_FILE="$MARKER_DIR/$NAME.exit"
META_FILE="$MARKER_DIR/$NAME.meta"
CMD_JSON=$(cmd_json "$@")
HOST=$(hostname 2>/dev/null || printf 'unknown')

if [ "$DRY_RUN" -eq 1 ]; then
  printf 'dry-run: would create %s\n' "$MARKER_DIR" >&2
  printf 'dry-run: would write %s, then run the command, then %s + %s\n' \
    "$START_FILE" "$EXIT_FILE" "$META_FILE" >&2
  printf '{"dry_run": true, "name": "%s", "marker_dir": "%s", "command": %s}\n' \
    "$(json_escape "$NAME")" "$(json_escape "$MARKER_DIR")" "$CMD_JSON"
  exit 0
fi

mkdir -p "$MARKER_DIR" 2>/dev/null \
  || die "cannot create marker directory '$MARKER_DIR'" 2
[ -w "$MARKER_DIR" ] \
  || die "marker directory '$MARKER_DIR' is not writable" 2

# A stale terminal marker from a previous run would make this run look already
# finished the moment a reader looked. Clear both before starting.
rm -f "$EXIT_FILE" "$META_FILE"

STARTED_AT=$(now_iso)
printf '{"name": "%s", "host": "%s", "pid": %d, "started_at": "%s", "command": %s}\n' \
  "$(json_escape "$NAME")" "$(json_escape "$HOST")" "$$" "$STARTED_AT" "$CMD_JSON" \
  > "$START_FILE.tmp" && mv "$START_FILE.tmp" "$START_FILE"

printf '%s start %s: %s\n' "$STARTED_AT" "$NAME" "$*" >&2

# Run as our own child so `wait` — the one primitive available everywhere —
# is enough. Do not background-and-detach; we must survive to write the marker.
"$@" &
CHILD=$!
wait "$CHILD"
RC=$?

FINISHED_AT=$(now_iso)

# Exit code first: it is what readers key on, so it must not appear before the
# run is genuinely over. Temp-then-rename keeps it atomic.
printf '%s\n' "$RC" > "$EXIT_FILE.tmp" && mv "$EXIT_FILE.tmp" "$EXIT_FILE"

META=$(printf '{"name": "%s", "host": "%s", "pid": %d, "started_at": "%s", "finished_at": "%s", "exit_code": %d, "command": %s}' \
  "$(json_escape "$NAME")" "$(json_escape "$HOST")" "$$" "$STARTED_AT" "$FINISHED_AT" "$RC" "$CMD_JSON")
printf '%s\n' "$META" > "$META_FILE.tmp" && mv "$META_FILE.tmp" "$META_FILE"

printf '%s done %s: exit=%d\n' "$FINISHED_AT" "$NAME" "$RC" >&2
printf '%s\n' "$META"

exit "$RC"
