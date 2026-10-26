#!/usr/bin/env bash
set -euo pipefail

# One-shot setup for forge-native-dev workflow in a target project.
# Detects forge, creates labels, scaffolds issue templates, configures git,
# and appends agent-guidance snippet to AGENTS.md.
#
# Idempotent: existing files are skipped; snippets append only if the
# sentinel marker is missing.
# Compatibility: macOS system Bash 3.2+.

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
SKILL_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

# shellcheck source=forge.sh
source "$SCRIPT_DIR/forge.sh"

usage() {
  cat <<'EOF'
Usage: forge-init.sh [OPTIONS]

Set up forge-native-dev workflow files in a target project.

Options:
  --target DIR              Target project root (default: current directory)
  --project-name NAME       Project name (default: basename of --target)
  --agent-contract FILE     Path (relative to --target) to the agent contract
                            file (AGENTS.md / CLAUDE.md). Default: auto-detect.
  --skip-labels             Do not create labels on the forge.
  --skip-templates          Do not scaffold issue templates.
  --skip-git-config         Do not set git config (fetch.prune, pull.rebase, etc).
  --force                   Overwrite existing files.
  -h, --help                Show this help and exit.
EOF
}

target="."
project_name=""
agent_contract=""
skip_labels=0
skip_templates=0
skip_git_config=0
force=0

while [ $# -gt 0 ]; do
  case "$1" in
    -h|--help) usage; exit 0 ;;
    --target) target="$2"; shift 2 ;;
    --project-name) project_name="$2"; shift 2 ;;
    --agent-contract) agent_contract="$2"; shift 2 ;;
    --skip-labels) skip_labels=1; shift ;;
    --skip-templates) skip_templates=1; shift ;;
    --skip-git-config) skip_git_config=1; shift ;;
    --force) force=1; shift ;;
    *) echo "Unknown argument: $1" >&2; usage >&2; exit 2 ;;
  esac
done

target="$(cd "$target" && pwd)"
[ -z "$project_name" ] && project_name="$(basename "$target")"

cd "$target"

_forge_log "=== forge-native-dev init ==="
_forge_log "Target: $target"
_forge_log "Project: $project_name"

# --- Step 1: Detect forge ---------------------------------------------------

forge_detect

if [ "$FORGE_TYPE" = "unknown" ]; then
  _forge_die "Cannot set up forge-native-dev: no GitHub or GitLab remote detected." 1
fi

# --- Step 2: Create labels ---------------------------------------------------

if [ "$skip_labels" -eq 0 ] && [ -n "$FORGE_CLI" ]; then
  _forge_log ""
  _forge_log "--- Creating labels ---"

  forge_label_ensure "priority/P1" "d73a4a" "Critical priority"
  forge_label_ensure "priority/P2" "fbca04" "Medium priority"
  forge_label_ensure "priority/P3" "0e8a16" "Low priority"
  forge_label_ensure "type/bug" "d73a4a" "Bug report"
  forge_label_ensure "type/feature" "a2eeef" "Feature request"
  forge_label_ensure "type/chore" "e4e669" "Maintenance task"
  forge_label_ensure "agent-task" "7057ff" "Task for AI agent"
  forge_label_ensure "backlog" "c5def5" "Backlog item"
  forge_label_ensure "in-progress" "0075ca" "Work in progress"
  forge_label_ensure "discussion" "d4c5f9" "Discussion topic"

  _forge_log "Labels ready."
elif [ "$skip_labels" -eq 1 ]; then
  _forge_log "Skipping label creation (--skip-labels)."
else
  _forge_warn "Skipping label creation (no CLI available)."
fi

# --- Step 3: Scaffold issue templates ----------------------------------------

if [ "$skip_templates" -eq 0 ]; then
  _forge_log ""
  _forge_log "--- Scaffolding issue templates ---"

  case "$FORGE_TYPE" in
    github)
      local_template_dir=".github/ISSUE_TEMPLATE"
      mkdir -p "$local_template_dir"

      if [ ! -f "$local_template_dir/bug_report.md" ] || [ "$force" -eq 1 ]; then
        if [ -f "$SKILL_DIR/assets/issue-templates/github-bug-report.md" ]; then
          cp "$SKILL_DIR/assets/issue-templates/github-bug-report.md" "$local_template_dir/bug_report.md"
          _forge_log "Created $local_template_dir/bug_report.md"
        fi
      else
        _forge_log "Skipping $local_template_dir/bug_report.md (exists; use --force to overwrite)"
      fi

      if [ ! -f "$local_template_dir/feature_request.md" ] || [ "$force" -eq 1 ]; then
        if [ -f "$SKILL_DIR/assets/issue-templates/github-feature-request.md" ]; then
          cp "$SKILL_DIR/assets/issue-templates/github-feature-request.md" "$local_template_dir/feature_request.md"
          _forge_log "Created $local_template_dir/feature_request.md"
        fi
      else
        _forge_log "Skipping $local_template_dir/feature_request.md (exists)"
      fi
      ;;
    gitlab)
      local_template_dir=".gitlab/issue_templates"
      mkdir -p "$local_template_dir"

      if [ ! -f "$local_template_dir/Bug Report.md" ] || [ "$force" -eq 1 ]; then
        if [ -f "$SKILL_DIR/assets/issue-templates/gitlab-bug-report.md" ]; then
          cp "$SKILL_DIR/assets/issue-templates/gitlab-bug-report.md" "$local_template_dir/Bug Report.md"
          _forge_log "Created $local_template_dir/Bug Report.md"
        fi
      else
        _forge_log "Skipping $local_template_dir/Bug Report.md (exists)"
      fi

      if [ ! -f "$local_template_dir/Feature Request.md" ] || [ "$force" -eq 1 ]; then
        if [ -f "$SKILL_DIR/assets/issue-templates/gitlab-feature-request.md" ]; then
          cp "$SKILL_DIR/assets/issue-templates/gitlab-feature-request.md" "$local_template_dir/Feature Request.md"
          _forge_log "Created $local_template_dir/Feature Request.md"
        fi
      else
        _forge_log "Skipping $local_template_dir/Feature Request.md (exists)"
      fi
      ;;
  esac
else
  _forge_log "Skipping issue templates (--skip-templates)."
fi

# --- Step 4: Git config ------------------------------------------------------

if [ "$skip_git_config" -eq 0 ]; then
  _forge_log ""
  _forge_log "--- Configuring git ---"

  git config fetch.prune true
  _forge_log "Set fetch.prune = true"

  git config pull.rebase true
  _forge_log "Set pull.rebase = true"

  git config merge.ff only
  _forge_log "Set merge.ff = only"

  # Ensure .worktrees/ is gitignored
  if [ ! -f .gitignore ] || ! grep -qF '.worktrees/' .gitignore 2>/dev/null; then
    printf '\n# forge-native-dev worktrees\n.worktrees/\n' >> .gitignore
    _forge_log "Added .worktrees/ to .gitignore"
  fi
else
  _forge_log "Skipping git config (--skip-git-config)."
fi

# --- Step 5: Agent guidance snippet -------------------------------------------

_forge_log ""
_forge_log "--- Agent guidance ---"

SENTINEL="forge-native-dev:guidance"

# Auto-detect agent contract file
if [ -z "$agent_contract" ]; then
  for candidate in AGENTS.md CLAUDE.md .opencode/AGENTS.md .cursorrules; do
    if [ -f "$candidate" ]; then
      agent_contract="$candidate"
      break
    fi
  done
  [ -z "$agent_contract" ] && agent_contract="AGENTS.md"
fi

if [ -f "$agent_contract" ] && grep -qF "$SENTINEL" "$agent_contract" 2>/dev/null; then
  _forge_log "Agent guidance already present in $agent_contract (sentinel: $SENTINEL)"
else
  if [ -f "$SKILL_DIR/assets/agent-guidance.md.template" ]; then
    {
      printf '\n'
      sed "s/<PROJECT NAME>/$project_name/g; s/<FORGE_TYPE>/$FORGE_TYPE/g" \
        "$SKILL_DIR/assets/agent-guidance.md.template"
    } >> "$agent_contract"
    _forge_log "Appended agent guidance to $agent_contract"
  else
    _forge_warn "Template not found: $SKILL_DIR/assets/agent-guidance.md.template"
  fi
fi

# --- Summary ------------------------------------------------------------------

_forge_log ""
_forge_log "=== Setup complete ==="
_forge_log ""
_forge_log "Forge:      $FORGE_TYPE"
_forge_log "CLI:        ${FORGE_CLI:-not available}"
_forge_log "Contract:   $agent_contract"
_forge_log ""

if [ "$FORGE_TYPE" = "github" ]; then
  _forge_log "Manual steps you may want to do:"
  _forge_log "  1. Enable Discussions on the repo (Settings > Features > Discussions)"
  _forge_log "  2. Create a GitHub Project board for backlog visualization"
  _forge_log "  3. Review .gitignore changes and commit"
elif [ "$FORGE_TYPE" = "gitlab" ]; then
  _forge_log "Manual steps you may want to do:"
  _forge_log "  1. Create a GitLab Board for backlog visualization"
  _forge_log "  2. Review .gitignore changes and commit"
fi
