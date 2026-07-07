#!/usr/bin/env bash
# finalize.sh — stamp a verdict on an evidence bundle, refresh artifact sizes,
# and render the human-facing MANIFEST.md from manifest.json.
#
# Bash 3.2 compatible (stock macOS).

set -euo pipefail

usage() {
  cat <<'EOF'
Usage: finalize.sh [OPTIONS]

Finalize an evidence bundle for acceptance review: record a verdict, append
reproduction steps, refresh artifact byte sizes, and (re)render MANIFEST.md.

Options:
  --bundle DIR      Target bundle (default: <root>/.current, else newest).
  --root DIR        Evidence root used to find .current (default: .evidence).
  --verdict V       PASS | NEEDS_WORK | pending (default: leave unchanged).
  --step TEXT       Append a reproduction step (repeatable).
  --scrub           Scan text artifacts for secrets with gitleaks (report-only).
  --dry-run         Print what would change; write nothing.
  --help, -h        Show this help and exit.

Exit codes:
  0  success
  1  invalid arguments
  2  no usable evidence bundle
  3  jq not found
EOF
}

log()  { printf '%s\n' "$*" >&2; }
warn() { printf 'warn: %s\n' "$*" >&2; }
die()  { printf 'error: %s\n' "$1" >&2; exit "${2:-1}"; }

BUNDLE=""
ROOT=".evidence"
VERDICT=""
STEPS=()
SCRUB=0
DRY_RUN=0

while [ $# -gt 0 ]; do
  case "$1" in
    --bundle=*)  BUNDLE="${1#--bundle=}"; shift ;;
    --bundle)    BUNDLE="${2:-}"; [ "$#" -ge 2 ] || die "missing value for $1 (try --help)" 1; shift 2 ;;
    --root=*)    ROOT="${1#--root=}"; shift ;;
    --root)      ROOT="${2:-}"; [ "$#" -ge 2 ] || die "missing value for $1 (try --help)" 1; shift 2 ;;
    --verdict=*) VERDICT="${1#--verdict=}"; shift ;;
    --verdict)   VERDICT="${2:-}"; [ "$#" -ge 2 ] || die "missing value for $1 (try --help)" 1; shift 2 ;;
    --step=*)    STEPS+=("${1#--step=}"); shift ;;
    --step)      STEPS+=("${2:-}"); [ "$#" -ge 2 ] || die "missing value for $1 (try --help)" 1; shift 2 ;;
    --scrub)     SCRUB=1; shift ;;
    --dry-run)   DRY_RUN=1; shift ;;
    --help|-h)   usage; exit 0 ;;
    -*)          die "unknown flag: $1 (try --help)" 1 ;;
    *)           die "unexpected positional arg: $1 (try --help)" 1 ;;
  esac
done

command -v jq >/dev/null 2>&1 || die "jq not found in PATH (install: brew install jq)" 3

if [ -n "$VERDICT" ]; then
  # Accept any case; PASS/NEEDS_WORK are canonically upper, pending is lower.
  VERDICT=$(printf '%s' "$VERDICT" | tr '[:lower:]' '[:upper:]')
  case "$VERDICT" in
    PASS|NEEDS_WORK) ;;
    PENDING) VERDICT="pending" ;;
    *) die "invalid --verdict: $VERDICT (expected PASS|NEEDS_WORK|pending)" 1 ;;
  esac
fi

if git rev-parse --show-toplevel >/dev/null 2>&1; then
  cd "$(git rev-parse --show-toplevel)"
fi

# --- Resolve target bundle (same contract as capture.sh) ------------------
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

# --- Refresh artifact byte sizes (files may have grown since capture) -----
refresh_sizes() {
  local names name size tmp
  names=$(jq -r '.artifacts[].name' "$MANIFEST")
  tmp="$(mktemp)"; cp "$MANIFEST" "$tmp"
  while IFS= read -r name; do
    [ -n "$name" ] || continue
    size=0
    if [ -f "$BUNDLE/$name" ]; then
      size=$(wc -c < "$BUNDLE/$name" | tr -d ' ')
    else
      warn "artifact missing on disk: $name (recorded as 0 B)"
    fi
    jq --arg n "$name" --argjson s "${size:-0}" \
      '(.artifacts[] | select(.name==$n) | .bytes) = $s' "$tmp" > "$tmp.2" \
      && mv "$tmp.2" "$tmp"
  done <<EOF
$names
EOF
  mv "$tmp" "$MANIFEST"
}

# --- Optional secret scan (report-only) -----------------------------------
scrub() {
  if ! command -v gitleaks >/dev/null 2>&1; then
    warn "gitleaks not found — skipping secret scan (install: brew install gitleaks)"
    warn "screenshots/video are NOT auto-scrubbed — review them manually before sharing"
    return 0
  fi
  local hits=0 f rc
  while IFS= read -r f; do
    [ -n "$f" ] || continue
    gitleaks stdin --no-banner < "$f" >/dev/null 2>&1; rc=$?
    if [ "$rc" -eq 0 ]; then
      :  # clean
    elif [ "$rc" -eq 1 ]; then
      warn "possible secret in $f — review before sharing"
      hits=$((hits + 1))
    else
      warn "gitleaks error scanning $f (exit $rc) — not counted as a leak"
    fi
  done <<EOF
$(find "$BUNDLE" -type f \( -name '*.log' -o -name '*.txt' \) 2>/dev/null)
EOF
  [ "$hits" -eq 0 ] && log "gitleaks: no secrets flagged in text artifacts"
  warn "screenshots/video are NOT auto-scrubbed — review them manually before sharing"
}

# --- Render MANIFEST.md from manifest.json --------------------------------
render_md() {
  local title verdict agent sid branch sha dirty created feature
  title=$(jq -r '.title // ""' "$MANIFEST")
  verdict=$(jq -r '.verdict // "pending"' "$MANIFEST")
  agent=$(jq -r '.agent // "unknown"' "$MANIFEST")
  sid=$(jq -r '.session.id // ""' "$MANIFEST")
  branch=$(jq -r '.git.branch // ""' "$MANIFEST")
  sha=$(jq -r '.git.sha // ""' "$MANIFEST")
  dirty=$(jq -r '.git.dirty // false' "$MANIFEST")
  created=$(jq -r '.created_utc // ""' "$MANIFEST")
  feature=$(jq -r '.feature // ""' "$MANIFEST")

  local badge="⏳ pending"
  [ "$verdict" = "PASS" ] && badge="✅ PASS"
  [ "$verdict" = "NEEDS_WORK" ] && badge="❌ NEEDS_WORK"

  {
    printf '# Evidence: %s\n\n' "${title:-$(basename "$BUNDLE")}"
    printf '> **verdict: %s**\n\n' "$badge"
    [ -n "$feature" ] && printf '%s\n\n' "$feature"
    printf '## Context\n\n'
    printf -- '- agent / session: `%s` / `%s`\n' "$agent" "$sid"
    printf -- '- git: `%s` @ `%s` (dirty: %s)\n' "$branch" "$sha" "$dirty"
    printf -- '- created: `%s`\n\n' "$created"

    local nsteps; nsteps=$(jq '.steps | length' "$MANIFEST")
    if [ "$nsteps" -gt 0 ]; then
      printf '## How to reproduce\n\n'
      jq -r '.steps | to_entries[] | "\(.key+1). \(.value)"' "$MANIFEST"
      printf '\n'
    fi

    printf '## Artifacts\n\n'
    local nart; nart=$(jq '.artifacts | length' "$MANIFEST")
    if [ "$nart" -eq 0 ]; then
      printf '_No artifacts captured._\n\n'
    else
      printf '| artifact | kind | tool | size |\n|---|---|---|---|\n'
      jq -r '.artifacts[] | [.name, .kind, .tool, (.bytes|tostring)] | @tsv' "$MANIFEST" \
      | while IFS=$'\t' read -r name kind tool bytes; do
          # Escape '|' so a pipe in a field can't break the table; percent-encode
          # it in the link target.
          local href="${name//|/%7C}"
          printf '| [%s](%s) | %s | %s | %s B |\n' \
            "${name//|/\\|}" "$href" "${kind//|/\\|}" "${tool//|/\\|}" "$bytes"
        done
      printf '\n'
    fi

    printf '## Review checklist\n\n'
    printf -- '- [ ] Artifacts match the described feature\n'
    printf -- '- [ ] No secrets leaked in logs/screenshots\n'
    printf -- '- [ ] Behavior is correct → set verdict PASS\n'
  } > "$BUNDLE/MANIFEST.md"
}

# --- Apply changes ---------------------------------------------------------
if [ "$DRY_RUN" = "1" ]; then
  log "[dry-run] bundle: $BUNDLE"
  [ -n "$VERDICT" ] && log "[dry-run] would set verdict=$VERDICT"
  [ "${#STEPS[@]}" -gt 0 ] && log "[dry-run] would append ${#STEPS[@]} step(s)"
  log "[dry-run] would refresh sizes + render MANIFEST.md"
  exit 0
fi

tmp="$(mktemp)"
cp "$MANIFEST" "$tmp"
[ -n "$VERDICT" ] && jq --arg v "$VERDICT" '.verdict=$v' "$tmp" > "$tmp.2" && mv "$tmp.2" "$tmp"
for s in "${STEPS[@]:-}"; do
  [ -n "$s" ] || continue
  # Idempotent: skip a step that's already recorded (finalize is safe to re-run).
  jq --arg s "$s" 'if (.steps | index($s)) then . else .steps += [$s] end' \
    "$tmp" > "$tmp.2" && mv "$tmp.2" "$tmp"
done
mv "$tmp" "$MANIFEST"

refresh_sizes
[ "$SCRUB" = "1" ] && scrub
render_md

FINAL_VERDICT=$(jq -r '.verdict' "$MANIFEST")
NART=$(jq '.artifacts | length' "$MANIFEST")
log "finalized $BUNDLE — verdict=$FINAL_VERDICT, artifacts=$NART"
jq -c --arg b "$BUNDLE" \
  '{bundle:$b, verdict:.verdict, artifacts:(.artifacts|length), manifest_md:($b+"/MANIFEST.md")}' \
  "$MANIFEST"
