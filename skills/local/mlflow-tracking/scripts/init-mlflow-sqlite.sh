#!/usr/bin/env bash
# init-mlflow-sqlite.sh — Set up MLflow in SQLite mode in the current dir.
#
# Bash 3.2 compatible (works on stock macOS).

set -euo pipefail

usage() {
  cat <<'EOF'
Usage: init-mlflow-sqlite.sh [OPTIONS]

Idempotently initialize MLflow in SQLite mode in the current directory:
  1. Touch <db-path> if missing
  2. Add mlflow.db, mlruns/, mlartifacts/ to .gitignore
  3. Print the tracking URI to export and the exact `mlflow ui` command

Re-running is safe: existing files are preserved.

Options:
  --db-path PATH     SQLite DB path (default: mlflow.db)
  --port N           Port for `mlflow ui` (default: 5001 — avoids macOS AirPlay on 5000)
  --dry-run          Show actions without executing
  --help, -h         Show this help and exit

Examples:
  init-mlflow-sqlite.sh
  init-mlflow-sqlite.sh --db-path data/mlflow.db --port 5002
  init-mlflow-sqlite.sh --dry-run

Exit codes:
  0  success
  1  invalid arguments
  2  not in a git repo (warning only — script still works without git)
EOF
}

log()  { printf '%s\n' "$*" >&2; }
warn() { printf 'warn: %s\n' "$*" >&2; }
die()  { printf 'error: %s\n' "$*" >&2; exit "${2:-1}"; }

DB_PATH="mlflow.db"
PORT=5001
DRY_RUN=0

while [ $# -gt 0 ]; do
  case "$1" in
    --db-path) DB_PATH="${2:-}"; shift 2 ;;
    --port)    PORT="${2:-}"; shift 2 ;;
    --dry-run) DRY_RUN=1; shift ;;
    --help|-h) usage; exit 0 ;;
    -*)        die "unknown flag: $1 (try --help)" 1 ;;
    *)         die "unexpected positional arg: $1 (try --help)" 1 ;;
  esac
done

# 1. Touch DB.
if [ -f "$DB_PATH" ]; then
  log "✓ $DB_PATH already exists — skipping"
else
  if [ "$DRY_RUN" = "1" ]; then
    log "[dry-run] touch $DB_PATH"
  else
    mkdir -p "$(dirname "$DB_PATH")"
    : > "$DB_PATH"
    log "✓ Created $DB_PATH"
  fi
fi

# 2. .gitignore (only if we're in a git repo).
if git rev-parse --git-dir >/dev/null 2>&1; then
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
  ensure_gitignore "$DB_PATH"
  ensure_gitignore "mlruns/"
  ensure_gitignore "mlartifacts/"
else
  warn "not in a git repo — skipping .gitignore updates"
fi

# 3. Print instructions.
URI="sqlite:///$DB_PATH"

cat >&2 <<EOF

────────────────────────────────────────────────────────────
MLflow SQLite mode initialized.

In your code:
    import mlflow
    mlflow.set_tracking_uri("$URI")

Or as an env var:
    export MLFLOW_TRACKING_URI=$URI

Launch the UI (MUST pass --backend-store-uri matching the URI):
    mlflow ui --backend-store-uri $URI --port $PORT

Then open: http://localhost:$PORT
────────────────────────────────────────────────────────────
EOF

# Structured stdout for agent consumption.
printf '{"status":"ok","tracking_uri":"%s","ui_command":"mlflow ui --backend-store-uri %s --port %d","ui_url":"http://localhost:%d"}\n' \
  "$URI" "$URI" "$PORT" "$PORT"
