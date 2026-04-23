#!/usr/bin/env bash
# lint-dvcyaml.sh — Validate dvc.yaml schema by parsing the DAG (no execution).
#
# Bash 3.2 compatible (works on stock macOS).

set -euo pipefail

usage() {
  cat <<'EOF'
Usage: lint-dvcyaml.sh [OPTIONS] [DVC_YAML_PATH]

Parse-only validation of a dvc.yaml file. Runs `dvc dag --dot` which exercises
the full schema validator and DAG resolver but executes no stages.

Args:
  DVC_YAML_PATH   Path to dvc.yaml (default: ./dvc.yaml in current dir)

Options:
  --dry-run       Show what would run without running.
  --help, -h      Show this help and exit.

Examples:
  lint-dvcyaml.sh
  lint-dvcyaml.sh path/to/dvc.yaml
  cd subproject && lint-dvcyaml.sh

Exit codes:
  0  dvc.yaml is valid
  1  invalid arguments
  2  dvc CLI not installed
  3  dvc.yaml not found
  4  dvc.yaml has schema or DAG errors (output on stderr)
EOF
}

log()  { printf '%s\n' "$*" >&2; }
die()  { printf 'error: %s\n' "$*" >&2; exit "${2:-1}"; }

DRY_RUN=0
DVC_YAML=""

while [ $# -gt 0 ]; do
  case "$1" in
    --dry-run) DRY_RUN=1; shift ;;
    --help|-h) usage; exit 0 ;;
    -*)        die "unknown flag: $1 (try --help)" 1 ;;
    *)
      [ -z "$DVC_YAML" ] || die "only one path allowed" 1
      DVC_YAML="$1"; shift
      ;;
  esac
done

[ -n "$DVC_YAML" ] || DVC_YAML="dvc.yaml"
[ -f "$DVC_YAML" ] || die "not found: $DVC_YAML" 3
command -v dvc >/dev/null 2>&1 || die "dvc not found in PATH" 2

# Run from the dir containing dvc.yaml so relative paths resolve.
WORKDIR="$(cd "$(dirname "$DVC_YAML")" && pwd)"

if [ "$DRY_RUN" = "1" ]; then
  log "[dry-run] cd $WORKDIR && dvc dag --dot >/dev/null"
  printf '{"file":"%s","status":"dry-run"}\n' "$DVC_YAML"
  exit 0
fi

if (cd "$WORKDIR" && dvc dag --dot >/dev/null 2>/tmp/dvc-lint.$$); then
  rm -f /tmp/dvc-lint.$$
  printf '{"file":"%s","status":"valid"}\n' "$DVC_YAML"
  exit 0
else
  log "dvc.yaml validation failed:"
  cat /tmp/dvc-lint.$$ >&2
  rm -f /tmp/dvc-lint.$$
  printf '{"file":"%s","status":"invalid"}\n' "$DVC_YAML"
  exit 4
fi
