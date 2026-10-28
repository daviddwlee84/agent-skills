#!/bin/sh
# superproject-workspace: refuse outer commits whose staged gitlinks point at
# commits that are not pushed. Resolves the CLI like the justfile recipes do.
root=$(git rev-parse --show-toplevel) || exit 1
rel=skills/superproject-workspace/scripts/superproject.py
cli=${SUPERPROJECT_CLI:-}
for cand in "$root/scripts/superproject.py" "$root/.agents/$rel" "$HOME/.agents/$rel"; do
  [ -n "$cli" ] && break
  [ -f "$cand" ] && cli=$cand
done
cli=${cli:-https://raw.githubusercontent.com/daviddwlee84/agent-skills/${SUPERPROJECT_CLI_REF:-main}/skills/local/superproject-workspace/scripts/superproject.py}
exec uv run --quiet --script "$cli" preflight
