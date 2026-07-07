#!/usr/bin/env bash
# detect-session.sh — best-effort identify the current coding-agent session.
#
# Emits {agent, session_id, source, specstory_path} as JSON (or TSV) so a
# caller can key an evidence bundle to the session it was produced in.
# Self-contained on purpose: mirrors the core of agent-history-hygiene's
# find-session.sh but carries no cross-skill path dependency, so this skill
# works when installed on its own.
#
# Bash 3.2 compatible (stock macOS).

set -euo pipefail

usage() {
  cat <<'EOF'
Usage: detect-session.sh [OPTIONS]

Best-effort discovery of the coding-agent session for $PWD. Heuristics:
  agent      --agent override > env markers ($CLAUDECODE, $CURSOR_*, $CODEX_*)
             > artifact presence > "unknown".
  session_id Claude session UUID (newest *.jsonl under
             ~/.claude/projects/<slug>/, slug = $PWD with '/'->'-'); else the
             newest ./.specstory/history/<timestamp>.md timestamp; else
             "nosession".

Options:
  --agent VALUE   Force the agent kind (claude|cursor|codex|...). Skips detection.
  --json          Emit JSON to stdout (default).
  --tsv           Emit TSV (key<TAB>value per line) instead of JSON.
  --quiet         Suppress stderr diagnostics.
  --help, -h      Show this help and exit.

Output keys: agent, session_id, source, specstory_path

Exit codes:
  0  always (never fails a pipeline; empty/"unknown" values signal absence).
  1  invalid arguments.
EOF
}

log()  { [ "$QUIET" = "1" ] || printf '%s\n' "$*" >&2; }
die()  { printf 'error: %s\n' "$1" >&2; exit "${2:-1}"; }

AGENT_OVERRIDE=""
OUT="json"
QUIET=0

while [ $# -gt 0 ]; do
  case "$1" in
    --agent=*) AGENT_OVERRIDE="${1#--agent=}"; shift ;;
    --agent)   AGENT_OVERRIDE="${2:-}"; [ "$#" -ge 2 ] || die "missing value for $1 (try --help)" 1; shift 2 ;;
    --json)    OUT="json"; shift ;;
    --tsv)     OUT="tsv"; shift ;;
    --quiet)   QUIET=1; shift ;;
    --help|-h) usage; exit 0 ;;
    -*)        die "unknown flag: $1 (try --help)" 1 ;;
    *)         die "unexpected positional arg: $1 (try --help)" 1 ;;
  esac
done

# Claude's project slug: absolute $PWD with EVERY non-alphanumeric char
# replaced by '-' (mirrors Claude Code: '/Users/me/.cache' -> '-Users-me--cache').
cwd_slug() { printf '%s' "$PWD" | sed 's/[^a-zA-Z0-9]/-/g'; }

newest_file() {
  # newest_file <dir> <glob> — newest matching file by mtime, or empty.
  # Bash glob loop (no xargs): avoids the GNU-xargs "run ls on empty input"
  # footgun and NUL-in-variable issues entirely. Bash 3.2 compatible.
  local dir="$1" glob="$2" newest="" f
  [ -d "$dir" ] || { printf ''; return 0; }
  for f in "$dir"/$glob; do
    [ -e "$f" ] || continue   # unmatched glob stays literal -> skip
    if [ -z "$newest" ] || [ "$f" -nt "$newest" ]; then newest="$f"; fi
  done
  printf '%s' "$newest"
}

# --- Resolve Claude session (UUID + jsonl) --------------------------------
CLAUDE_JSONL=""
CLAUDE_UUID=""
proj_dir="$HOME/.claude/projects/$(cwd_slug)"
CLAUDE_JSONL=$(newest_file "$proj_dir" "*.jsonl")
[ -n "$CLAUDE_JSONL" ] && CLAUDE_UUID=$(basename "$CLAUDE_JSONL" .jsonl)

# --- Resolve SpecStory transcript -----------------------------------------
SPECSTORY_PATH=$(newest_file "$PWD/.specstory/history" "*.md")

# --- Detect agent kind -----------------------------------------------------
# Env markers first (authoritative for the live process), then artifacts.
detect_agent() {
  if [ -n "$AGENT_OVERRIDE" ]; then printf '%s' "$AGENT_OVERRIDE"; return; fi
  if [ -n "${CLAUDECODE:-}" ] || [ -n "${CLAUDE_CODE_ENTRYPOINT:-}" ]; then
    printf 'claude'; return
  fi
  if [ -n "${CURSOR_TRACE_ID:-}" ] || [ -n "${CURSOR_AGENT:-}" ] || [ -n "${CURSOR_SESSION_ID:-}" ]; then
    printf 'cursor'; return
  fi
  if [ -n "${CODEX_SANDBOX:-}" ] || [ -n "${CODEX_HOME:-}" ] || [ -n "${CODEX_SESSION_ID:-}" ]; then
    printf 'codex'; return
  fi
  # Artifact fallback: a live Claude jsonl for this CWD is a strong signal.
  if [ -n "$CLAUDE_UUID" ]; then printf 'claude'; return; fi
  printf 'unknown'
}
AGENT=$(detect_agent)

# --- Pick the session id + source -----------------------------------------
# Prefer the Claude UUID (stable, unique). Fall back to the SpecStory
# timestamp slug (strip any title suffix, keep <date>_<time>Z).
SESSION_ID="nosession"
SOURCE="none"
if [ -n "$CLAUDE_UUID" ]; then
  SESSION_ID="$CLAUDE_UUID"
  SOURCE="claude_jsonl"
elif [ -n "$SPECSTORY_PATH" ]; then
  base=$(basename "$SPECSTORY_PATH" .md)
  # SpecStory names: <YYYY-MM-DD_HH-MM[-SS]Z>[-<title-slug>]. Seconds are
  # optional (real transcripts are often minute-precision); keep just the stamp.
  SESSION_ID=$(printf '%s' "$base" | sed -E 's/^([0-9]{4}-[0-9]{2}-[0-9]{2}_[0-9]{2}-[0-9]{2}(-[0-9]{2})?Z).*/\1/')
  SOURCE="specstory"
fi

[ "$AGENT" = "unknown" ] && log "agent kind undetected (pass --agent to override)"
[ "$SOURCE" = "none" ]  && log "no Claude jsonl or SpecStory transcript for $PWD"

if [ "$OUT" = "tsv" ]; then
  printf 'agent\t%s\n'          "$AGENT"
  printf 'session_id\t%s\n'     "$SESSION_ID"
  printf 'source\t%s\n'         "$SOURCE"
  printf 'specstory_path\t%s\n' "$SPECSTORY_PATH"
else
  printf '{"agent":"%s","session_id":"%s","source":"%s","specstory_path":"%s"}\n' \
    "$AGENT" "$SESSION_ID" "$SOURCE" "$SPECSTORY_PATH"
fi
