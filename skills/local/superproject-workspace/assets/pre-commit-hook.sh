#!/bin/sh
# superproject-workspace: refuse outer commits whose staged gitlinks point at
# commits that are not pushed to the child's origin/<branch>.
root=$(git rev-parse --show-toplevel) || exit 1
if command -v uv >/dev/null 2>&1; then
  exec uv run --quiet --script "$root/__CLI__" preflight
fi
exec python3 "$root/__CLI__" preflight
