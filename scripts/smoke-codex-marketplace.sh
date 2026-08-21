#!/usr/bin/env bash
# Exercise the native Codex marketplace flow without touching real user state.
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
SKILLS_DIR="$REPO_ROOT/skills"
MANIFEST="$SKILLS_DIR/.claude-plugin/marketplace.json"
REPRESENTATIVE_PLUGIN="version-control"
EXPECTED_SKILL_PATH="./local/git-workflow"

fail() {
  printf 'ERROR: %s\n' "$*" >&2
  exit 1
}

for command in codex jq; do
  command -v "$command" >/dev/null 2>&1 || fail "required command not found: $command"
done

CODEX_BIN="$(command -v codex)"
JQ_BIN="$(command -v jq)"
MARKETPLACE_NAME="$("$JQ_BIN" -er '.name' "$MANIFEST")"
PLUGIN_ID="$REPRESENTATIVE_PLUGIN@$MARKETPLACE_NAME"
TMP_ROOT="$(mktemp -d "${TMPDIR:-/tmp}/agent-skills-codex-smoke.XXXXXX")"
TMP_ROOT="$(cd "$TMP_ROOT" && pwd -P)"

cleanup() {
  rm -rf "$TMP_ROOT"
}
trap cleanup EXIT

export HOME="$TMP_ROOT/home"
export CODEX_HOME="$TMP_ROOT/codex"
mkdir -p "$HOME" "$CODEX_HOME"

printf '%s\n' 'Registering the Claude-format marketplace with Codex in isolated state...'
add_json="$("$CODEX_BIN" plugin marketplace add "$SKILLS_DIR" --json)"
# jq receives both values via --arg; this is not a shell expansion.
# shellcheck disable=SC2016
"$JQ_BIN" -e --arg marketplace "$MARKETPLACE_NAME" --arg root "$SKILLS_DIR" '
  .marketplaceName == $marketplace and
  .installedRoot == $root and
  .alreadyAdded == false
' <<<"$add_json" >/dev/null || fail "Codex did not register the expected local marketplace"

available_json="$("$CODEX_BIN" plugin list --available --json)"
"$JQ_BIN" -e '
  (.installed | type) == "array" and
  (.available | type) == "array"
' <<<"$available_json" >/dev/null || fail "unexpected JSON from 'codex plugin list --available --json'"

expected_plugins="$("$JQ_BIN" -r '.plugins[].name' "$MANIFEST" | LC_ALL=C sort)"
# jq receives $marketplace via --arg; this is not a shell expansion.
# shellcheck disable=SC2016
actual_plugins="$("$JQ_BIN" -r --arg marketplace "$MARKETPLACE_NAME" '
  .available[]
  | select(.marketplaceName == $marketplace)
  | .name
' <<<"$available_json" | LC_ALL=C sort)"

if [[ "$actual_plugins" != "$expected_plugins" ]]; then
  printf '%s\n' 'ERROR: native Codex plugin list does not match marketplace.json' >&2
  diff -u \
    <(printf '%s\n' "$expected_plugins") \
    <(printf '%s\n' "$actual_plugins") >&2 || true
  exit 1
fi
printf 'Found all %s declared plugins.\n' "$("$JQ_BIN" '.plugins | length' "$MANIFEST")"

printf 'Installing representative plugin %s...\n' "$PLUGIN_ID"
install_json="$("$CODEX_BIN" plugin add "$PLUGIN_ID" --json)"
# jq receives $id via --arg; this is not a shell expansion.
# shellcheck disable=SC2016
install_path="$("$JQ_BIN" -er --arg id "$PLUGIN_ID" '
  select(.pluginId == $id)
  | .installedPath
' <<<"$install_json")"
case "$install_path" in
  "$CODEX_HOME"/*) ;;
  *) fail "plugin escaped isolated CODEX_HOME: $install_path" ;;
esac

generated_manifest="$install_path/.codex-plugin/plugin.json"
[[ -f "$generated_manifest" ]] || fail "Codex did not generate its plugin adapter: $generated_manifest"
# jq receives both values via --arg; this is not a shell expansion.
# shellcheck disable=SC2016
"$JQ_BIN" -e \
  --arg name "$REPRESENTATIVE_PLUGIN" \
  --arg skill "$EXPECTED_SKILL_PATH" '
    .name == $name and
    .skills == [$skill]
  ' "$generated_manifest" >/dev/null || {
    printf '%s\n' 'ERROR: generated Codex adapter leaked skills across category boundaries' >&2
    "$JQ_BIN" '.' "$generated_manifest" >&2
    exit 1
  }

installed_json="$("$CODEX_BIN" plugin list --json)"
# jq receives $id via --arg; this is not a shell expansion.
# shellcheck disable=SC2016
"$JQ_BIN" -e --arg id "$PLUGIN_ID" '
  any(.installed[]; .pluginId == $id and .installed == true and .enabled == true)
' <<<"$installed_json" >/dev/null || fail "installed Codex plugin is not enabled"

printf 'PASSED: Codex generated a one-skill adapter for %s and kept state under %s\n' \
  "$PLUGIN_ID" "$CODEX_HOME"
