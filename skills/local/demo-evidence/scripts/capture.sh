#!/usr/bin/env bash
# capture.sh — capture one evidence artifact into a bundle and record it in
# the bundle's manifest.json.
#
#   capture.sh web    --url URL [--steps FILE] [--name N]   (Playwright)
#   capture.sh term   --cmd "CMD" [--log] [--name N]        (asciinema / tee)
#   capture.sh http   --url URL [--method M] [--data D] ... (curl)
#   capture.sh screen [--seconds N] [--device D]            (ffmpeg)
#
# Bundle defaults to <root>/.current (written by new-bundle.sh). Each mode
# preflights its tool and degrades with a clear stderr hint + distinct exit
# code, so a missing tool skips one capture without killing the workflow.
#
# Bash 3.2 compatible (stock macOS).

set -euo pipefail

usage() {
  cat <<'EOF'
Usage: capture.sh <web|term|http|screen> [OPTIONS]

Capture one artifact into an evidence bundle (see new-bundle.sh) and append
it to the bundle's manifest.json.

Common options:
  --bundle DIR    Target bundle (default: <root>/.current, else newest).
  --root DIR      Evidence root used to find .current (default: .evidence).
  --name NAME     Artifact base name (default: <mode>-<n>).
  --note TEXT     Free-text note stored with the artifact.
  --dry-run       Print the capture command; write nothing.
  --help, -h      Show this help and exit.

web    --url URL [--steps FILE] [--timeout MS] [--settle MS]
       Playwright: full-page screenshot + video (webm) + trace (zip).
       --settle holds the final state (default 1200ms) so no-steps clips are usable.
term   --cmd "CMD" [--log]
       asciinema recording of CMD; --log (or no asciinema) tees a plain log.
http   --url URL [--method GET|POST|...] [--data BODY] [--header "K: V"]...
       curl: status + headers + body + timing to http/NAME.txt (+ .json).
screen [--seconds N] [--device IDX] [--display :0]
       ffmpeg screen recording to NAME.mp4 (macOS avfoundation / Linux x11grab).

Exit codes:
  0  success
  1  invalid arguments
  2  no usable evidence bundle (run new-bundle.sh first)
  3  jq not found
  4  capture tool missing (node/playwright, asciinema, curl, or ffmpeg)
  5  capture command failed
EOF
}

log()  { printf '%s\n' "$*" >&2; }
warn() { printf 'warn: %s\n' "$*" >&2; }
die()  { printf 'error: %s\n' "$1" >&2; exit "${2:-1}"; }

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

MODE=""
BUNDLE=""
ROOT=".evidence"
NAME=""
NOTE=""
DRY_RUN=0
# mode-specific
URL=""; STEPS=""; TIMEOUT_MS=15000; SETTLE_MS=1200
CMD=""; LOG_ONLY=0
METHOD="GET"; DATA=""; HEADERS=()
SECONDS_REC=8; DEVICE=""; DISPLAY_OVR="${DISPLAY:-:0}"

[ $# -gt 0 ] || die "missing mode (web|term|http|screen); try --help" 1
case "$1" in
  web|term|http|screen) MODE="$1"; shift ;;
  --help|-h) usage; exit 0 ;;
  *) die "unknown mode: $1 (expected web|term|http|screen)" 1 ;;
esac

while [ $# -gt 0 ]; do
  case "$1" in
    --bundle=*)  BUNDLE="${1#--bundle=}"; shift ;;
    --bundle)    BUNDLE="${2:-}"; [ "$#" -ge 2 ] || die "missing value for $1 (try --help)" 1; shift 2 ;;
    --root=*)    ROOT="${1#--root=}"; shift ;;
    --root)      ROOT="${2:-}"; [ "$#" -ge 2 ] || die "missing value for $1 (try --help)" 1; shift 2 ;;
    --name=*)    NAME="${1#--name=}"; shift ;;
    --name)      NAME="${2:-}"; [ "$#" -ge 2 ] || die "missing value for $1 (try --help)" 1; shift 2 ;;
    --note=*)    NOTE="${1#--note=}"; shift ;;
    --note)      NOTE="${2:-}"; [ "$#" -ge 2 ] || die "missing value for $1 (try --help)" 1; shift 2 ;;
    --url=*)     URL="${1#--url=}"; shift ;;
    --url)       URL="${2:-}"; [ "$#" -ge 2 ] || die "missing value for $1 (try --help)" 1; shift 2 ;;
    --steps=*)   STEPS="${1#--steps=}"; shift ;;
    --steps)     STEPS="${2:-}"; [ "$#" -ge 2 ] || die "missing value for $1 (try --help)" 1; shift 2 ;;
    --timeout=*) TIMEOUT_MS="${1#--timeout=}"; shift ;;
    --timeout)   TIMEOUT_MS="${2:-}"; [ "$#" -ge 2 ] || die "missing value for $1 (try --help)" 1; shift 2 ;;
    --settle=*)  SETTLE_MS="${1#--settle=}"; shift ;;
    --settle)    SETTLE_MS="${2:-}"; [ "$#" -ge 2 ] || die "missing value for $1 (try --help)" 1; shift 2 ;;
    --cmd=*)     CMD="${1#--cmd=}"; shift ;;
    --cmd)       CMD="${2:-}"; [ "$#" -ge 2 ] || die "missing value for $1 (try --help)" 1; shift 2 ;;
    --log)       LOG_ONLY=1; shift ;;
    --method=*)  METHOD="${1#--method=}"; shift ;;
    --method)    METHOD="${2:-}"; [ "$#" -ge 2 ] || die "missing value for $1 (try --help)" 1; shift 2 ;;
    --data=*)    DATA="${1#--data=}"; shift ;;
    --data)      DATA="${2:-}"; [ "$#" -ge 2 ] || die "missing value for $1 (try --help)" 1; shift 2 ;;
    --header=*)  HEADERS+=("${1#--header=}"); shift ;;
    --header)    HEADERS+=("${2:-}"); [ "$#" -ge 2 ] || die "missing value for $1 (try --help)" 1; shift 2 ;;
    --seconds=*) SECONDS_REC="${1#--seconds=}"; shift ;;
    --seconds)   SECONDS_REC="${2:-}"; [ "$#" -ge 2 ] || die "missing value for $1 (try --help)" 1; shift 2 ;;
    --device=*)  DEVICE="${1#--device=}"; shift ;;
    --device)    DEVICE="${2:-}"; [ "$#" -ge 2 ] || die "missing value for $1 (try --help)" 1; shift 2 ;;
    --display=*) DISPLAY_OVR="${1#--display=}"; shift ;;
    --display)   DISPLAY_OVR="${2:-}"; [ "$#" -ge 2 ] || die "missing value for $1 (try --help)" 1; shift 2 ;;
    --dry-run)   DRY_RUN=1; shift ;;
    --help|-h)   usage; exit 0 ;;
    -*)          die "unknown flag: $1 (try --help)" 1 ;;
    *)           die "unexpected positional arg: $1 (try --help)" 1 ;;
  esac
done

command -v jq >/dev/null 2>&1 || die "jq not found in PATH (install: brew install jq)" 3

# Anchor at repo top level so relative --root resolves consistently.
if git rev-parse --show-toplevel >/dev/null 2>&1; then
  cd "$(git rev-parse --show-toplevel)"
fi

# --- Resolve target bundle -------------------------------------------------
if [ -z "$BUNDLE" ]; then
  if [ -f "$ROOT/.current" ]; then
    BUNDLE="$(head -n1 "$ROOT/.current")"
  else
    BUNDLE="$(find "$ROOT" -type f -name manifest.json -print0 2>/dev/null \
      | xargs -0 ls -t 2>/dev/null | head -n1 | sed 's|/manifest.json$||')"
  fi
fi
[ -n "$BUNDLE" ] && [ -f "$BUNDLE/manifest.json" ] \
  || die "no evidence bundle found (run new-bundle.sh first)" 2
MANIFEST="$BUNDLE/manifest.json"

# Default artifact name: <mode>-<n> where n = existing artifact count + 1.
if [ -z "$NAME" ]; then
  n=$(jq '.artifacts | length' "$MANIFEST")
  NAME="$MODE-$((n + 1))"
fi

# add_artifact <name> <kind> <tool> <path-for-size> <note> [meta-json]
# meta-json (optional) is a JSON object of structured fields (e.g. HTTP status);
# omit or pass "null" for none.
add_artifact() {
  local n="$1" kind="$2" tool="$3" path="$4" note="$5" meta="${6:-null}" bytes=0 tmp
  [ -f "$path" ] && bytes=$(wc -c < "$path" | tr -d ' ')
  tmp="$(mktemp)"
  jq --arg n "$n" --arg k "$kind" --arg t "$tool" \
     --argjson b "${bytes:-0}" --arg note "$note" --argjson meta "$meta" \
     '.artifacts += [{name:$n, kind:$k, tool:$t, bytes:$b, note:$note}
        + (if $meta==null then {} else {meta:$meta} end)]' \
     "$MANIFEST" > "$tmp" && mv "$tmp" "$MANIFEST"
  log "recorded artifact: $n ($kind, ${bytes:-0} bytes)"
}

# ==========================================================================
capture_web() {
  [ -n "$URL" ] || die "web mode requires --url" 1
  local mjs="$HERE/../assets/capture-web.mjs"
  [ -f "$mjs" ] || die "missing $mjs" 4
  command -v node >/dev/null 2>&1 || die "node not found — install Node.js, or use the microsoft/playwright-cli skill" 4
  node -e "require('module').createRequire(process.cwd()+'/').resolve('playwright')" 2>/dev/null \
    || die "playwright not resolvable from $(pwd) — run: npm i -D playwright && npx playwright install chromium (or use the microsoft/playwright-cli skill)" 4

  if [ "$DRY_RUN" = "1" ]; then
    log "[dry-run] node $mjs --url $URL --out $BUNDLE --name $NAME --settle $SETTLE_MS ${STEPS:+--steps $STEPS}"
    return 0
  fi
  # capture-web.mjs exits 5 on nav/step failure but STILL flushes+prints whatever
  # trace/video/screenshot it managed to write — record those partials rather than
  # discarding them. Only a non-{0,5} exit is a hard failure.
  local out_json rc partial_note=""
  set +e
  out_json="$(node "$mjs" --url "$URL" --out "$BUNDLE" --name "$NAME" \
    --timeout "$TIMEOUT_MS" --settle "$SETTLE_MS" ${STEPS:+--steps "$STEPS"})"
  rc=$?
  set -e
  if [ "$rc" -ne 0 ] && [ "$rc" -ne 5 ]; then
    die "capture-web.mjs failed for $URL (exit $rc)" 5
  fi
  if [ "$rc" -eq 5 ]; then
    warn "web capture incomplete (nav/steps failed) — recording partial artifacts"
    partial_note=" (partial: capture failed)"
  fi
  # mjs prints {"screenshot":"..","video":"..","trace":".."} (relative to bundle)
  local shot vid trace
  shot="$(printf '%s' "$out_json" | jq -r '.screenshot // empty')"
  vid="$(printf '%s' "$out_json" | jq -r '.video // empty')"
  trace="$(printf '%s' "$out_json" | jq -r '.trace // empty')"
  [ -n "$shot" ]  && add_artifact "$shot"  screenshot playwright "$BUNDLE/$shot"  "$NOTE$partial_note"
  [ -n "$vid" ]   && add_artifact "$vid"   video      playwright "$BUNDLE/$vid"   "$NOTE$partial_note"
  [ -n "$trace" ] && add_artifact "$trace" trace      playwright "$BUNDLE/$trace" "$NOTE$partial_note"
}

capture_term() {
  [ -n "$CMD" ] || die "term mode requires --cmd" 1
  local have_asciinema=0
  command -v asciinema >/dev/null 2>&1 && have_asciinema=1

  if [ "$LOG_ONLY" = "0" ] && [ "$have_asciinema" = "1" ]; then
    local out="$BUNDLE/$NAME.cast"
    if [ "$DRY_RUN" = "1" ]; then log "[dry-run] asciinema rec -c \"$CMD\" $out"; return 0; fi
    asciinema rec --overwrite -c "$CMD" "$out" >/dev/null 2>&1 \
      || die "asciinema recording failed" 5
    add_artifact "$NAME.cast" asciicast asciinema "$out" "$NOTE"
  else
    [ "$have_asciinema" = "1" ] || log "asciinema not found — falling back to plain log"
    local out="$BUNDLE/$NAME.log"
    if [ "$DRY_RUN" = "1" ]; then log "[dry-run] tee log of: $CMD -> $out"; return 0; fi
    {
      printf '$ %s\n\n' "$CMD"
      set +e
      bash -c "$CMD" 2>&1
      rc=$?
      set -e
      printf '\n[exit %s]\n' "$rc"
    } | tee "$out" >/dev/null
    add_artifact "$NAME.log" log tee "$out" "$NOTE"
  fi
}

capture_http() {
  [ -n "$URL" ] || die "http mode requires --url" 1
  command -v curl >/dev/null 2>&1 || die "curl not found in PATH" 4
  mkdir -p "$BUNDLE/http"
  local body="$BUNDLE/http/$NAME.body" hdr="$BUNDLE/http/$NAME.headers"
  local txt="$BUNDLE/http/$NAME.txt" sj="$BUNDLE/http/$NAME.json"
  local curl_args=(-sS -X "$METHOD" -D "$hdr" -o "$body"
                   -w '%{http_code}\t%{time_total}\t%{size_download}')
  local h; for h in "${HEADERS[@]:-}"; do [ -n "$h" ] && curl_args+=(-H "$h"); done
  [ -n "$DATA" ] && curl_args+=(--data "$DATA")

  if [ "$DRY_RUN" = "1" ]; then log "[dry-run] curl ${curl_args[*]} $URL"; return 0; fi
  local meta status time_total size_dl
  meta="$(curl "${curl_args[@]}" "$URL")" || die "curl failed for $URL" 5
  status="$(printf '%s' "$meta" | cut -f1)"
  time_total="$(printf '%s' "$meta" | cut -f2)"
  size_dl="$(printf '%s' "$meta" | cut -f3)"
  {
    printf '%s %s\n\n' "$METHOD" "$URL"
    printf '=== response headers ===\n'; cat "$hdr"
    printf '\n=== body ===\n'; cat "$body"
  } > "$txt"
  jq -n --arg url "$URL" --arg method "$METHOD" --arg status "$status" \
        --arg time "$time_total" --arg bytes "$size_dl" \
        '{url:$url, method:$method, status:($status|tonumber?), time_total:($time|tonumber?), bytes:($bytes|tonumber?)}' \
        > "$sj"
  rm -f "$hdr" "$body"
  log "http $METHOD $URL -> $status (${time_total}s)"
  # Structured meta (status/time) on BOTH the human dump and the machine sidecar,
  # so the reviewer gets a real status field instead of a note suffix, and the
  # .json sidecar is recorded too (its bytes are the body only, not the full dump).
  local meta
  meta="$(jq -nc --arg s "$status" --arg t "$time_total" \
            '{status:($s|tonumber?), time_total:($t|tonumber?)}')"
  add_artifact "http/$NAME.txt"  http curl "$txt" "$NOTE" "$meta"
  add_artifact "http/$NAME.json" http curl "$sj"  "$NOTE" "$meta"
}

capture_screen() {
  command -v ffmpeg >/dev/null 2>&1 || die "ffmpeg not found in PATH (install: brew install ffmpeg)" 4
  local out="$BUNDLE/$NAME.mp4" os; os="$(uname -s)"
  local ff=(ffmpeg -y -t "$SECONDS_REC")
  if [ "$os" = "Darwin" ]; then
    local dev="${DEVICE:-1}"   # avfoundation screen index; varies per machine
    ff+=(-f avfoundation -i "$dev:none")
    log "macOS: recording avfoundation device '$dev' — needs Screen Recording permission."
    log "  list devices: ffmpeg -f avfoundation -list_devices true -i \"\""
  else
    ff+=(-f x11grab -i "$DISPLAY_OVR")
  fi
  ff+=("$out")
  if [ "$DRY_RUN" = "1" ]; then log "[dry-run] ${ff[*]}"; return 0; fi
  "${ff[@]}" >/dev/null 2>&1 || die "ffmpeg screen capture failed (check device/permission)" 5
  add_artifact "$NAME.mp4" video ffmpeg "$out" "$NOTE"
}

case "$MODE" in
  web)    capture_web ;;
  term)   capture_term ;;
  http)   capture_http ;;
  screen) capture_screen ;;
esac
