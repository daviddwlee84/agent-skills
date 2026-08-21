#!/usr/bin/env bash
# Exercise the native Claude Code marketplace flow without touching real user state.
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
SKILLS_DIR="$REPO_ROOT/skills"
MANIFEST="$SKILLS_DIR/.claude-plugin/marketplace.json"
REPRESENTATIVE_PLUGIN="version-control"
EXPECTED_SKILL="git-workflow"

fail() {
  printf 'ERROR: %s\n' "$*" >&2
  exit 1
}

for command in claude jq; do
  command -v "$command" >/dev/null 2>&1 || fail "required command not found: $command"
done

CLAUDE_BIN="$(command -v claude)"
JQ_BIN="$(command -v jq)"
MARKETPLACE_NAME="$("$JQ_BIN" -er '.name' "$MANIFEST")"
PLUGIN_ID="$REPRESENTATIVE_PLUGIN@$MARKETPLACE_NAME"
TMP_ROOT="$(mktemp -d "${TMPDIR:-/tmp}/agent-skills-claude-smoke.XXXXXX")"
TMP_ROOT="$(cd "$TMP_ROOT" && pwd -P)"

cleanup() {
  rm -rf "$TMP_ROOT"
}
trap cleanup EXIT

export HOME="$TMP_ROOT/home"
export CLAUDE_CONFIG_DIR="$TMP_ROOT/claude"
mkdir -p "$HOME" "$CLAUDE_CONFIG_DIR"

printf '%s\n' 'Validating the Claude marketplace manifest...'
"$CLAUDE_BIN" plugin validate "$SKILLS_DIR" --strict

printf '%s\n' 'Registering the local marketplace in isolated state...'
"$CLAUDE_BIN" plugin marketplace add "$SKILLS_DIR"

available_json="$("$CLAUDE_BIN" plugin list --available --json)"
"$JQ_BIN" -e '
  (.installed | type) == "array" and
  (.available | type) == "array"
' <<<"$available_json" >/dev/null || fail "unexpected JSON from 'claude plugin list --available --json'"

expected_plugins="$("$JQ_BIN" -r '.plugins[].name' "$MANIFEST" | LC_ALL=C sort)"
# jq receives $marketplace via --arg; this is not a shell expansion.
# shellcheck disable=SC2016
actual_plugins="$("$JQ_BIN" -r --arg marketplace "$MARKETPLACE_NAME" '
  .available[]
  | select(.marketplaceName == $marketplace)
  | .name
' <<<"$available_json" | LC_ALL=C sort)"

if [[ "$actual_plugins" != "$expected_plugins" ]]; then
  printf '%s\n' 'ERROR: native Claude plugin list does not match marketplace.json' >&2
  diff -u \
    <(printf '%s\n' "$expected_plugins") \
    <(printf '%s\n' "$actual_plugins") >&2 || true
  exit 1
fi
printf 'Found all %s declared plugins.\n' "$("$JQ_BIN" '.plugins | length' "$MANIFEST")"

printf 'Installing representative plugin %s...\n' "$PLUGIN_ID"
"$CLAUDE_BIN" plugin install --scope user "$PLUGIN_ID"

installed_json="$("$CLAUDE_BIN" plugin list --json)"
# jq receives $id via --arg; this is not a shell expansion.
# shellcheck disable=SC2016
install_path="$("$JQ_BIN" -er --arg id "$PLUGIN_ID" '
  first(.[] | select(.id == $id and .scope == "user" and .enabled == true))
  | .installPath
' <<<"$installed_json")"
case "$install_path" in
  "$CLAUDE_CONFIG_DIR"/*) ;;
  *) fail "plugin escaped isolated CLAUDE_CONFIG_DIR: $install_path" ;;
esac

details="$("$CLAUDE_BIN" plugin details "$PLUGIN_ID")"
expected_inventory="Skills (1)  $EXPECTED_SKILL"
if [[ "$details" != *"$expected_inventory"* ]]; then
  printf '%s\n' "ERROR: expected component inventory '$expected_inventory'" >&2
  printf '%s\n' "$details" >&2
  exit 1
fi

printf 'PASSED: %s exposes only %s and all state stayed under %s\n' \
  "$PLUGIN_ID" "$EXPECTED_SKILL" "$CLAUDE_CONFIG_DIR"
