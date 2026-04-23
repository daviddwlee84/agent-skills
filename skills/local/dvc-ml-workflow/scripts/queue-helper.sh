#!/usr/bin/env bash
# queue-helper.sh — Agent-friendly wrapper around `dvc queue` and `dvc exp run --queue`.
#
# Stdout is structured (JSON), stderr is prose. Designed for an LLM caller.
#
# Bash 3.2 compatible (works on stock macOS).

set -euo pipefail

usage() {
  cat <<'EOF'
Usage: queue-helper.sh [GLOBAL OPTIONS] <subcommand> [ARGS]

Wraps `dvc queue` / `dvc exp run --queue` with structured JSON stdout.

Subcommands:
  enqueue PARAM=VAL[,PARAM=VAL...] [...]   Enqueue one experiment per arg group.
                                           Each ARG is comma-joined param overrides.
  grid PARAM=VAL1,VAL2 [PARAM=VAL1,VAL2]   Cartesian-product grid sweep.
  start [--jobs N]                         Start the worker pool (default: 1).
  status                                   Print queue status as JSON array.
  logs TASK_ID                             Stream logs of one queued/running task.
  stop                                     Stop worker pool (queued tasks survive).
  clear                                    Remove all queued (not-yet-started) tasks.

Global options:
  --dry-run          Show what would be enqueued/started; don't run.
  --help, -h         Show this help and exit.

Examples:
  # Enqueue 3 explicit experiments:
  queue-helper.sh enqueue model.lr=1e-4 model.lr=5e-4 model.lr=1e-3

  # 2x3 grid (6 experiments enqueued):
  queue-helper.sh grid model.lr=1e-4,5e-4,1e-3 train.batch_size=32,64

  # Start 4 workers and wait:
  queue-helper.sh start --jobs 4

  # Check what's queued:
  queue-helper.sh status

Exit codes:
  0  success
  1  invalid arguments
  2  dvc CLI not installed
  3  dvc command failed
EOF
}

log()  { printf '%s\n' "$*" >&2; }
die()  { printf 'error: %s\n' "$*" >&2; exit "${2:-1}"; }

DRY_RUN=0

# Pre-parse global flags before subcommand.
while [ $# -gt 0 ]; do
  case "$1" in
    --dry-run) DRY_RUN=1; shift ;;
    --help|-h) usage; exit 0 ;;
    --) shift; break ;;
    -*) die "unknown global flag: $1 (try --help)" 1 ;;
    *)  break ;;
  esac
done

[ $# -gt 0 ] || die "missing subcommand (try --help)" 1
command -v dvc >/dev/null 2>&1 || die "dvc not found in PATH" 2

SUB="$1"; shift

run_dvc() {
  if [ "$DRY_RUN" = "1" ]; then
    log "[dry-run] dvc $*"
    return 0
  fi
  dvc "$@" || die "dvc $* failed" 3
}

# Build -S flags from a comma-separated list like "model.lr=1e-4,train.bs=32".
build_s_flags() {
  local spec="$1" out=""
  local IFS=','
  for kv in $spec; do
    [ -n "$kv" ] || continue
    out="$out -S $kv"
  done
  printf '%s' "$out"
}

case "$SUB" in
  enqueue)
    [ $# -gt 0 ] || die "enqueue: provide at least one PARAM=VAL spec" 1
    count=0
    for spec in "$@"; do
      flags=$(build_s_flags "$spec")
      if [ "$DRY_RUN" = "1" ]; then
        log "[dry-run] dvc exp run --queue$flags"
      else
        # shellcheck disable=SC2086
        dvc exp run --queue $flags || die "enqueue failed for: $spec" 3
      fi
      count=$((count + 1))
    done
    printf '{"action":"enqueue","enqueued":%d}\n' "$count"
    ;;

  grid)
    [ $# -gt 0 ] || die "grid: provide at least one PARAM=V1,V2,... axis" 1

    # Cartesian product. Bash 3.2 has no associative arrays; build incrementally.
    # Combos starts as one empty combo "".
    combos=""
    first=1
    for axis in "$@"; do
      key="${axis%%=*}"
      vals="${axis#*=}"
      [ "$key" = "$axis" ] && die "grid axis missing '=': $axis" 1

      new_combos=""
      IFS=','
      for v in $vals; do
        [ -n "$v" ] || continue
        if [ "$first" = "1" ]; then
          item="${key}=${v}"
          new_combos="${new_combos}|${item}"
        else
          # Append "${key}=${v}" to every existing combo.
          IFS='|'
          for existing in $combos; do
            [ -n "$existing" ] || continue
            new_combos="${new_combos}|${existing},${key}=${v}"
          done
          IFS=','
        fi
      done
      unset IFS
      combos="$new_combos"
      first=0
    done

    count=0
    IFS='|'
    for combo in $combos; do
      [ -n "$combo" ] || continue
      flags=$(build_s_flags "$combo")
      if [ "$DRY_RUN" = "1" ]; then
        log "[dry-run] dvc exp run --queue$flags"
      else
        # shellcheck disable=SC2086
        dvc exp run --queue $flags || die "enqueue failed for combo: $combo" 3
      fi
      count=$((count + 1))
    done
    unset IFS
    printf '{"action":"grid","enqueued":%d}\n' "$count"
    ;;

  start)
    JOBS=1
    while [ $# -gt 0 ]; do
      case "$1" in
        --jobs) JOBS="${2:-1}"; shift 2 ;;
        *) die "start: unexpected arg $1" 1 ;;
      esac
    done
    run_dvc queue start --jobs "$JOBS"
    printf '{"action":"start","jobs":%d}\n' "$JOBS"
    ;;

  status)
    if [ "$DRY_RUN" = "1" ]; then
      log "[dry-run] dvc queue status"
      printf '{"action":"status","tasks":[]}\n'
      exit 0
    fi
    # `dvc queue status` outputs human-readable text; capture and re-emit raw under "raw"
    # plus structured stub. Future: parse properly when dvc gains --json.
    raw=$(dvc queue status 2>&1 || true)
    # Escape for JSON.
    raw_esc=$(printf '%s' "$raw" | sed -e 's/\\/\\\\/g' -e 's/"/\\"/g' -e ':a;N;$!ba;s/\n/\\n/g')
    printf '{"action":"status","raw":"%s"}\n' "$raw_esc"
    ;;

  logs)
    [ $# -gt 0 ] || die "logs: TASK_ID required" 1
    TASK_ID="$1"
    if [ "$DRY_RUN" = "1" ]; then
      log "[dry-run] dvc queue logs $TASK_ID"
      exit 0
    fi
    dvc queue logs "$TASK_ID"
    ;;

  stop)
    run_dvc queue stop
    printf '{"action":"stop"}\n'
    ;;

  clear)
    if [ "$DRY_RUN" = "1" ]; then
      log "[dry-run] dvc queue remove --all --queued"
    else
      dvc queue remove --queued || true
    fi
    printf '{"action":"clear"}\n'
    ;;

  *)
    die "unknown subcommand: $SUB (try --help)" 1
    ;;
esac
