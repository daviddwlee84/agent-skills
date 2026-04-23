#!/usr/bin/env bash
# start-mlflow-server.sh — Copy the bundled docker-compose stack into a target dir,
#                         customize .env, launch, wait for healthcheck.
#
# Bash 3.2 compatible (works on stock macOS).

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
SKILL_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
STACK_SRC="$SKILL_DIR/assets/docker-compose-stack"

usage() {
  cat <<'EOF'
Usage: start-mlflow-server.sh [OPTIONS]

Bootstrap a production MLflow stack (PostgreSQL + MinIO + tracking server)
using the bundled docker-compose-stack assets.

Steps:
  1. Copy assets/docker-compose-stack/ to <target-dir>/ (skip if exists)
  2. Generate <target-dir>/.env from .env.example (skip if exists)
     — optionally rotate MinIO + PG credentials to random values
  3. `docker compose up -d` in <target-dir>
  4. Wait for healthcheck (up to 60s)
  5. Print the MLflow UI URL and the env vars to export

Options:
  --target-dir DIR        Where to place the stack (default: infra/mlflow)
  --port N                MLFLOW_PORT to write into .env (default: 8000)
  --no-rotate-secrets     Keep .env.example default credentials (NOT for prod)
  --skip-up               Stop after copying + .env generation
  --dry-run               Print actions without executing
  --help, -h              Show this help and exit

Examples:
  start-mlflow-server.sh
  start-mlflow-server.sh --target-dir /srv/mlflow --port 8000
  start-mlflow-server.sh --no-rotate-secrets --dry-run

Exit codes:
  0  success (server is up and healthy)
  1  invalid arguments
  2  docker / docker compose not installed
  3  source assets directory missing
  4  docker compose up failed
  5  healthcheck timed out
EOF
}

log()  { printf '%s\n' "$*" >&2; }
warn() { printf 'warn: %s\n' "$*" >&2; }
die()  { printf 'error: %s\n' "$*" >&2; exit "${2:-1}"; }

TARGET_DIR="infra/mlflow"
PORT=8000
ROTATE_SECRETS=1
SKIP_UP=0
DRY_RUN=0

while [ $# -gt 0 ]; do
  case "$1" in
    --target-dir)        TARGET_DIR="${2:-}"; shift 2 ;;
    --port)              PORT="${2:-}"; shift 2 ;;
    --no-rotate-secrets) ROTATE_SECRETS=0; shift ;;
    --skip-up)           SKIP_UP=1; shift ;;
    --dry-run)           DRY_RUN=1; shift ;;
    --help|-h)           usage; exit 0 ;;
    -*)                  die "unknown flag: $1 (try --help)" 1 ;;
    *)                   die "unexpected positional arg: $1" 1 ;;
  esac
done

[ -d "$STACK_SRC" ] || die "stack source missing: $STACK_SRC" 3

if [ "$SKIP_UP" = "0" ]; then
  command -v docker >/dev/null 2>&1 || die "docker not found in PATH" 2
  docker compose version >/dev/null 2>&1 || die "docker compose plugin not installed" 2
fi

# 1. Copy stack.
if [ -d "$TARGET_DIR" ]; then
  log "✓ $TARGET_DIR already exists — skipping copy (existing files preserved)"
else
  if [ "$DRY_RUN" = "1" ]; then
    log "[dry-run] cp -r $STACK_SRC $TARGET_DIR"
  else
    mkdir -p "$(dirname "$TARGET_DIR")"
    cp -r "$STACK_SRC" "$TARGET_DIR"
    log "✓ Copied stack → $TARGET_DIR"
  fi
fi

# 2. Generate .env.
ENV_FILE="$TARGET_DIR/.env"
ENV_EXAMPLE="$TARGET_DIR/.env.example"

gen_secret() {
  # 24 hex chars from /dev/urandom (bash 3.2 safe).
  if command -v openssl >/dev/null 2>&1; then
    openssl rand -hex 12
  else
    # Fallback — less ideal but portable.
    LC_ALL=C tr -dc 'a-f0-9' < /dev/urandom | head -c 24
  fi
}

if [ -f "$ENV_FILE" ]; then
  log "✓ $ENV_FILE exists — skipping (delete it to regenerate)"
else
  [ -f "$ENV_EXAMPLE" ] || die ".env.example missing: $ENV_EXAMPLE" 3

  if [ "$DRY_RUN" = "1" ]; then
    log "[dry-run] generate $ENV_FILE from $ENV_EXAMPLE (rotate=$ROTATE_SECRETS, port=$PORT)"
  else
    cp "$ENV_EXAMPLE" "$ENV_FILE"

    # Always set MLFLOW_PORT.
    sed -i.bak -E "s|^MLFLOW_PORT=.*|MLFLOW_PORT=$PORT|" "$ENV_FILE" && rm -f "${ENV_FILE}.bak"

    if [ "$ROTATE_SECRETS" = "1" ]; then
      PG_PW=$(gen_secret)
      MINIO_KEY=$(gen_secret)
      MINIO_SECRET=$(gen_secret)
      sed -i.bak -E "s|^PG_PASSWORD=.*|PG_PASSWORD=$PG_PW|" "$ENV_FILE" && rm -f "${ENV_FILE}.bak"
      sed -i.bak -E "s|^MINIO_ACCESS_KEY=.*|MINIO_ACCESS_KEY=$MINIO_KEY|" "$ENV_FILE" && rm -f "${ENV_FILE}.bak"
      sed -i.bak -E "s|^MINIO_SECRET_ACCESS_KEY=.*|MINIO_SECRET_ACCESS_KEY=$MINIO_SECRET|" "$ENV_FILE" && rm -f "${ENV_FILE}.bak"
      log "✓ Generated $ENV_FILE with rotated PG/MinIO secrets"
    else
      log "✓ Generated $ENV_FILE with default credentials (--no-rotate-secrets)"
      warn "Default credentials are NOT safe outside localhost"
    fi
  fi
fi

if [ "$SKIP_UP" = "1" ]; then
  log "Skipping 'docker compose up' (--skip-up)"
  printf '{"status":"prepared","target_dir":"%s","port":%d}\n' "$TARGET_DIR" "$PORT"
  exit 0
fi

# 3. Launch.
if [ "$DRY_RUN" = "1" ]; then
  log "[dry-run] (cd $TARGET_DIR && docker compose up -d)"
  printf '{"status":"dry-run","target_dir":"%s","port":%d}\n' "$TARGET_DIR" "$PORT"
  exit 0
fi

(cd "$TARGET_DIR" && docker compose up -d) || die "docker compose up failed" 4

# 4. Healthcheck wait.
log "Waiting for MLflow server to become healthy (up to 60s)..."
DEADLINE=$(( $(date +%s) + 60 ))
HEALTHY=0
while [ "$(date +%s)" -lt "$DEADLINE" ]; do
  if curl -fsS "http://localhost:$PORT/health" >/dev/null 2>&1; then
    HEALTHY=1
    break
  fi
  sleep 2
done

if [ "$HEALTHY" = "0" ]; then
  warn "Healthcheck timed out — check 'docker compose -f $TARGET_DIR/docker-compose.yaml logs tracking_server'"
  printf '{"status":"timeout","url":"http://localhost:%d","target_dir":"%s"}\n' "$PORT" "$TARGET_DIR"
  exit 5
fi

# 5. Print success info.
# Read back creds from .env (for client-side export hints).
PG_PW=$(grep -E '^PG_PASSWORD=' "$ENV_FILE" | head -1 | cut -d= -f2-)
MINIO_KEY=$(grep -E '^MINIO_ACCESS_KEY=' "$ENV_FILE" | head -1 | cut -d= -f2-)
MINIO_SECRET=$(grep -E '^MINIO_SECRET_ACCESS_KEY=' "$ENV_FILE" | head -1 | cut -d= -f2-)
MINIO_API_PORT=$(grep -E '^MINIO_API_PORT=' "$ENV_FILE" | head -1 | cut -d= -f2-)
MINIO_CONSOLE_PORT=$(grep -E '^MINIO_CONSOLE_PORT=' "$ENV_FILE" | head -1 | cut -d= -f2-)

cat >&2 <<EOF

────────────────────────────────────────────────────────────
MLflow server is healthy at http://localhost:$PORT

Client environment to export (so artifacts can upload to MinIO):
    export MLFLOW_TRACKING_URI=http://localhost:$PORT
    export AWS_ACCESS_KEY_ID=$MINIO_KEY
    export AWS_SECRET_ACCESS_KEY=$MINIO_SECRET
    export MLFLOW_S3_ENDPOINT_URL=http://localhost:$MINIO_API_PORT

UIs:
    MLflow UI:     http://localhost:$PORT
    MinIO console: http://localhost:$MINIO_CONSOLE_PORT  (login: $MINIO_KEY / $MINIO_SECRET)

Stop the stack:
    (cd $TARGET_DIR && docker compose down)
────────────────────────────────────────────────────────────
EOF

printf '{"status":"healthy","url":"http://localhost:%d","target_dir":"%s","minio_console":"http://localhost:%s"}\n' \
  "$PORT" "$TARGET_DIR" "$MINIO_CONSOLE_PORT"
