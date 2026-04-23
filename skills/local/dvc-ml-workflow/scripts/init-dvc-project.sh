#!/usr/bin/env bash
# init-dvc-project.sh — Idempotent DVC project initialization for ML repos.
#
# Bash 3.2 compatible (works on stock macOS).

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
SKILL_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
ASSETS_DIR="$SKILL_DIR/assets"

usage() {
  cat <<'EOF'
Usage: init-dvc-project.sh [OPTIONS]

Idempotently set up DVC in the current directory:
  1. Run `dvc init` (with --subdir if requested)
  2. Update .gitignore so .dvc/cache, .dvc/tmp, .dvc/config.local are ignored
  3. Optionally configure a default remote (--remote URL)
  4. Drop dvc.yaml, params.yaml, .dvcignore templates from the skill's assets/
     IF AND ONLY IF those files don't already exist (never overwrites)

Re-running is safe: existing config is preserved, missing pieces are filled in.

Options:
  --remote URL       Add and set as default a DVC remote at this URL.
                     Examples: s3://bucket/path, ssh://user@host/path,
                               gs://bucket/path, gdrive://folder-id
  --remote-name NAME Name to give the remote (default: 'origin')
  --subdir           Pass --subdir to dvc init (use inside a monorepo subdir
                     that already has its own .git up the tree)
  --force            Overwrite existing dvc.yaml / params.yaml / .dvcignore
  --dry-run          Print actions without executing
  --help, -h         Show this help and exit

Examples:
  init-dvc-project.sh
  init-dvc-project.sh --remote s3://my-bucket/dvc-store
  init-dvc-project.sh --subdir --remote ssh://ml@server/data/dvc
  init-dvc-project.sh --dry-run

Exit codes:
  0  success
  1  invalid arguments
  2  not in a git repo (DVC requires git)
  3  dvc CLI not installed
  4  dvc init failed
EOF
}

log()  { printf '%s\n' "$*" >&2; }
warn() { printf 'warn: %s\n' "$*" >&2; }
die()  { printf 'error: %s\n' "$*" >&2; exit "${2:-1}"; }

REMOTE_URL=""
REMOTE_NAME="origin"
SUBDIR=0
FORCE=0
DRY_RUN=0

while [ $# -gt 0 ]; do
  case "$1" in
    --remote)      REMOTE_URL="${2:-}"; shift 2 ;;
    --remote-name) REMOTE_NAME="${2:-}"; shift 2 ;;
    --subdir)      SUBDIR=1; shift ;;
    --force)       FORCE=1; shift ;;
    --dry-run)     DRY_RUN=1; shift ;;
    --help|-h)     usage; exit 0 ;;
    -*)            die "unknown flag: $1 (try --help)" 1 ;;
    *)             die "unexpected positional arg: $1 (try --help)" 1 ;;
  esac
done

run() {
  if [ "$DRY_RUN" = "1" ]; then
    log "[dry-run] $*"
  else
    eval "$@"
  fi
}

# Preflight checks.
command -v git >/dev/null 2>&1 || die "git not found in PATH" 2
command -v dvc >/dev/null 2>&1 || die "dvc not found in PATH (pip install 'dvc[s3]' or similar)" 3

if ! git rev-parse --git-dir >/dev/null 2>&1; then
  die "not inside a git repository — run 'git init' first" 2
fi

# Step 1: dvc init (skip if already done).
if [ -d ".dvc" ]; then
  log "✓ .dvc/ already exists — skipping 'dvc init'"
else
  if [ "$SUBDIR" = "1" ]; then
    run "dvc init --subdir" || die "dvc init --subdir failed" 4
  else
    run "dvc init" || die "dvc init failed" 4
  fi
  log "✓ Ran 'dvc init'"
fi

# Step 2: ensure .gitignore covers DVC's local-only files.
ensure_gitignore() {
  local pattern="$1"
  if [ -f .gitignore ] && grep -qxF "$pattern" .gitignore; then
    return 0
  fi
  if [ "$DRY_RUN" = "1" ]; then
    log "[dry-run] append '$pattern' to .gitignore"
  else
    printf '%s\n' "$pattern" >> .gitignore
    log "✓ Added to .gitignore: $pattern"
  fi
}

ensure_gitignore ".dvc/cache/"
ensure_gitignore ".dvc/tmp/"
ensure_gitignore ".dvc/config.local"

# Step 3: optional remote.
if [ -n "$REMOTE_URL" ]; then
  if dvc remote list 2>/dev/null | awk '{print $1}' | grep -qx "$REMOTE_NAME"; then
    log "✓ Remote '$REMOTE_NAME' already exists — skipping (use 'dvc remote modify' to change URL)"
  else
    run "dvc remote add -d \"$REMOTE_NAME\" \"$REMOTE_URL\""
    log "✓ Added default remote '$REMOTE_NAME' → $REMOTE_URL"
  fi
fi

# Step 4: copy templates if missing.
copy_template_if_missing() {
  local src="$1" dst="$2"
  if [ -f "$dst" ] && [ "$FORCE" = "0" ]; then
    log "✓ $dst already exists — skipping (use --force to overwrite)"
    return 0
  fi
  if [ ! -f "$src" ]; then
    warn "template not found: $src (skipping)"
    return 0
  fi
  if [ "$DRY_RUN" = "1" ]; then
    log "[dry-run] cp $src → $dst"
  else
    cp "$src" "$dst"
    log "✓ Created $dst from template"
  fi
}

copy_template_if_missing "$ASSETS_DIR/dvc.yaml.template"     "dvc.yaml"
copy_template_if_missing "$ASSETS_DIR/params.yaml.template"  "params.yaml"
copy_template_if_missing "$ASSETS_DIR/.dvcignore.template"   ".dvcignore"

# Structured stdout for agent consumption.
if [ "$DRY_RUN" = "0" ]; then
  printf '{"status":"ok","remote":"%s","remote_url":"%s","next_steps":["Edit dvc.yaml + params.yaml","Run: dvc stage add ... or dvc repro","Commit: git add . && git commit -m \"Initialize DVC\""]}\n' \
    "$REMOTE_NAME" "$REMOTE_URL"
fi
