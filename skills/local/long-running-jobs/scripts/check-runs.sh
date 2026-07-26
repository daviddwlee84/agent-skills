#!/usr/bin/env bash
# check-runs.sh — report what finished while the agent was away.
#
# The resume path: after a session dies, compacts, or the laptop sleeps, this
# reads the marker directory written by run-and-mark.sh and says what actually
# happened — without re-running anything.
#
# Bash 3.2 compatible (stock macOS).

set -u

usage() {
  cat <<'EOF'
Usage: check-runs.sh [OPTIONS]

Read a marker directory written by run-and-mark.sh and report the state of each
run. Use this to recover after losing a session, instead of assuming or
re-running.

Options:
  --marker-dir DIR   Directory holding the markers. Default: .runs
  --name NAME        Report only this run.
  --json             Emit a JSON array on stdout instead of a table.
  --help, -h         Show this help and exit.

States:
  succeeded   marker present, exit code 0
  failed      marker present, exit code non-zero
  unknown     started, but no completion marker — killed, node died, or STILL
              RUNNING. Never treat this as "not done, so re-run": you may
              launch a second copy of a job that is still going.

Output:
  stdout   aligned table, or a JSON array with --json
  stderr   diagnostics only

Exit codes:
  0  every run recorded succeeded
  1  invalid arguments
  2  marker directory missing or unreadable
  3  at least one run failed
  4  at least one run is unknown (takes precedence over 3 — unknown is the
     state that needs a human decision)

Examples:
  check-runs.sh --marker-dir .runs
  check-runs.sh --marker-dir .runs --json | jq -r '.[] | select(.state != "succeeded")'
  check-runs.sh --name v2_full || echo "needs attention"
EOF
}

die() { printf 'error: %s\n' "$1" >&2; exit "${2:-1}"; }

MARKER_DIR=".runs"
ONLY_NAME=""
AS_JSON=0

while [ $# -gt 0 ]; do
  case "$1" in
    --marker-dir) [ $# -ge 2 ] || die "--marker-dir requires a value (try --help)" 1
                  MARKER_DIR="$2"; shift 2 ;;
    --name)       [ $# -ge 2 ] || die "--name requires a value (try --help)" 1
                  ONLY_NAME="$2"; shift 2 ;;
    --json)       AS_JSON=1; shift ;;
    --help|-h)    usage; exit 0 ;;
    *)            die "unknown argument: $1 (try --help)" 1 ;;
  esac
done

[ -d "$MARKER_DIR" ] || die "marker directory '$MARKER_DIR' not found — was run-and-mark.sh ever run with --marker-dir '$MARKER_DIR'?" 2
[ -r "$MARKER_DIR" ] || die "marker directory '$MARKER_DIR' is not readable" 2

json_escape() {
  printf '%s' "$1" | sed -e 's/\\/\\\\/g' -e 's/"/\\"/g'
}

n_total=0
n_failed=0
n_unknown=0
rows=""      # newline-separated "name<TAB>state<TAB>exit<TAB>started<TAB>finished"

# Iterate over .start files: a run only exists if it was started.
for start_file in "$MARKER_DIR"/*.start; do
  [ -e "$start_file" ] || continue          # no matches: glob stayed literal

  base=$(basename "$start_file")
  name=${base%.start}

  if [ -n "$ONLY_NAME" ] && [ "$name" != "$ONLY_NAME" ]; then
    continue
  fi

  exit_file="$MARKER_DIR/$name.exit"
  n_total=$((n_total + 1))

  started=$(sed -n 's/.*"started_at": "\([^"]*\)".*/\1/p' "$start_file" 2>/dev/null)
  [ -n "$started" ] || started="-"

  if [ -f "$exit_file" ]; then
    code=$(head -n 1 "$exit_file" 2>/dev/null | tr -d '[:space:]')
    case "$code" in
      ''|*[!0-9]*)
        # Present but not an integer — a truncated or corrupt marker is not
        # evidence of success.
        state="unknown"; code="-"; n_unknown=$((n_unknown + 1)) ;;
      0)
        state="succeeded" ;;
      *)
        state="failed"; n_failed=$((n_failed + 1)) ;;
    esac
  else
    state="unknown"; code="-"; n_unknown=$((n_unknown + 1))
  fi

  meta_file="$MARKER_DIR/$name.meta"
  finished="-"
  if [ -f "$meta_file" ]; then
    f=$(sed -n 's/.*"finished_at": "\([^"]*\)".*/\1/p' "$meta_file" 2>/dev/null)
    [ -n "$f" ] && finished="$f"
  fi

  rows="$rows$name	$state	$code	$started	$finished
"
done

if [ "$n_total" -eq 0 ]; then
  if [ -n "$ONLY_NAME" ]; then
    printf 'no run named %s in %s\n' "$ONLY_NAME" "$MARKER_DIR" >&2
  else
    printf 'no runs recorded in %s\n' "$MARKER_DIR" >&2
  fi
  [ "$AS_JSON" -eq 1 ] && printf '[]\n'
  exit 0
fi

if [ "$AS_JSON" -eq 1 ]; then
  printf '['
  first=1
  printf '%s' "$rows" | while IFS='	' read -r name state code started finished; do
    [ -n "$name" ] || continue
    if [ $first -eq 1 ]; then first=0; else printf ','; fi
    if [ "$code" = "-" ]; then code_json="null"; else code_json="$code"; fi
    printf '{"name": "%s", "state": "%s", "exit_code": %s, "started_at": "%s", "finished_at": "%s"}' \
      "$(json_escape "$name")" "$state" "$code_json" \
      "$(json_escape "$started")" "$(json_escape "$finished")"
  done
  printf ']\n'
else
  printf '%-24s %-10s %-6s %-21s %s\n' NAME STATE EXIT STARTED FINISHED
  printf '%s' "$rows" | while IFS='	' read -r name state code started finished; do
    [ -n "$name" ] || continue
    printf '%-24s %-10s %-6s %-21s %s\n' "$name" "$state" "$code" "$started" "$finished"
  done
fi

if [ "$n_unknown" -gt 0 ]; then
  printf '%d run(s) in unknown state — still running, or killed. Check before re-running.\n' \
    "$n_unknown" >&2
  exit 4
fi
[ "$n_failed" -gt 0 ] && exit 3
exit 0
