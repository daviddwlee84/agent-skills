#!/usr/bin/env bash
# new-fastapi-ai-service.sh — Scaffold a production-grade FastAPI AI/ML service.
#
# Copies the skeleton under assets/project/ into a target directory, stripping
# the .tmpl suffix from every file and substituting the project slug. The
# generated tree follows clean architecture (router / service / repository) and
# bakes in the production patterns from the fastapi-ai-patterns skill: model +
# httpx client loaded in lifespan, /health + /ready split, JWT auth, SQLModel +
# Alembic, an LLM gateway with SSE streaming, input/output guardrails with a
# Pydantic validation loop, structured logging, and tests using
# dependency_overrides.
#
# Bash 3.2 compatible (works on stock macOS — no mapfile, no ${var,,}).

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
SKILL_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
ASSETS_DIR="$SKILL_DIR/assets/project"

usage() {
  cat <<'EOF'
Usage: new-fastapi-ai-service.sh [OPTIONS] <target-dir>

Scaffold a production-grade FastAPI AI/ML service into <target-dir>.

The generated project includes:
  - app/ with router / service / repository layering
  - lifespan-loaded model handle + shared httpx.AsyncClient
  - /health (liveness, cheap) + /ready (readiness, checks deps)
  - JWT auth with a pinned algorithm + bcrypt password hashing
  - SQLModel models + repository + Alembic migration env
  - an LLM gateway endpoint with SSE token streaming
  - input/output guardrails + a Pydantic validation loop helper
  - structured JSON logging
  - tests using dependency_overrides + SQLite in-memory
  - Dockerfile, .dockerignore, gunicorn_conf.py, pyproject.toml, .env.example

Options:
  --name SLUG        Override the project slug (default: sanitized <target-dir>
                     basename). Used as the package metadata name, the FastAPI
                     title default, and in README/.env.
  --force            Overwrite files if <target-dir> already exists.
  --dry-run          List the files that would be created, write nothing.
  --help, -h         Show this help and exit.

Examples:
  new-fastapi-ai-service.sh ./my-inference-api
  new-fastapi-ai-service.sh --name churn-scorer ./services/churn
  new-fastapi-ai-service.sh --dry-run ./demo

Output:
  Single JSON object on stdout (parseable by an agent), prose on stderr.
  Keys: project, slug, path, files, dry_run, next_steps[].

Exit codes:
  0  success
  1  invalid arguments
  2  target already exists (use --force) or assets missing
EOF
}

log()  { printf '%s\n' "$*" >&2; }
die()  { printf 'error: %s\n' "$1" >&2; exit "${2:-1}"; }

TARGET=""
SLUG_OVERRIDE=""
FORCE=0
DRY_RUN=0

while [ $# -gt 0 ]; do
  case "$1" in
    --name)    SLUG_OVERRIDE="${2:-}"; shift 2 ;;
    --force)   FORCE=1; shift ;;
    --dry-run) DRY_RUN=1; shift ;;
    --help|-h) usage; exit 0 ;;
    --)        shift; [ $# -gt 0 ] && { TARGET="$1"; shift; } ;;
    -*)        die "unknown flag: $1 (try --help)" 1 ;;
    *)
      if [ -n "$TARGET" ]; then
        die "only one target directory allowed (got '$TARGET' and '$1')" 1
      fi
      TARGET="$1"; shift
      ;;
  esac
done

[ -n "$TARGET" ] || die "missing <target-dir> (try --help)" 1
[ -d "$ASSETS_DIR" ] || die "skeleton assets not found at $ASSETS_DIR" 2

# Derive a sanitized slug: lowercase, non-alnum -> '-', collapse repeats, trim.
sanitize_slug() {
  printf '%s' "$1" \
    | tr '[:upper:]' '[:lower:]' \
    | tr -c 'a-z0-9' '-' \
    | sed -e 's/-\{1,\}/-/g' -e 's/^-//' -e 's/-$//'
}

if [ -n "$SLUG_OVERRIDE" ]; then
  SLUG="$(sanitize_slug "$SLUG_OVERRIDE")"
else
  SLUG="$(sanitize_slug "$(basename "$TARGET")")"
fi
[ -n "$SLUG" ] || die "could not derive a valid slug from target/name (use --name)" 1

if [ -e "$TARGET" ] && [ "$FORCE" = "0" ] && [ "$DRY_RUN" = "0" ]; then
  die "target already exists: $TARGET (use --force to overwrite, or --dry-run)" 2
fi

# Substitute the slug placeholder. Slug is [a-z0-9-] only, so it is sed-safe.
render() {
  sed "s/PROJECT_SLUG_PLACEHOLDER/$SLUG/g" "$1"
}

log "Project:   $SLUG"
log "Target:    $TARGET"
[ "$DRY_RUN" = "1" ] && log "Mode:      dry-run (no files written)"

COUNT=0
# Iterate every file in the skeleton. find is fine inside a bundled script.
while IFS= read -r src; do
  [ -n "$src" ] || continue
  rel="${src#"$ASSETS_DIR"/}"
  dest="$TARGET/${rel%.tmpl}"
  COUNT=$((COUNT + 1))

  if [ "$DRY_RUN" = "1" ]; then
    log "  would create  ${rel%.tmpl}"
    continue
  fi

  mkdir -p "$(dirname "$dest")"
  case "$src" in
    *.tmpl) render "$src" > "$dest" ;;
    *)      cp "$src" "$dest" ;;
  esac
done <<EOF
$(find "$ASSETS_DIR" -type f | sort)
EOF

NEXT_STEPS='"cd '"$TARGET"'","uv venv \u0026\u0026 source .venv/bin/activate","uv pip install -e \".[dev]\"","cp .env.example .env and fill secrets","uvicorn app.main:app --reload","pytest -q"'

printf '{"project":"%s","slug":"%s","path":"%s","files":%d,"dry_run":%s,"next_steps":[%s]}\n' \
  "$SLUG" "$SLUG" "$TARGET" "$COUNT" \
  "$([ "$DRY_RUN" = "1" ] && echo true || echo false)" \
  "$NEXT_STEPS"
