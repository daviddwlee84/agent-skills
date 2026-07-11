#!/usr/bin/env bash
set -euo pipefail

# Initialise experiment-knowledge-harness in a target repo:
# - Create experiments/{LEDGER.md,ROADMAP.md,README.md} from templates
# - Append agent guidance to AGENTS.md / CLAUDE.md (auto-detect)
# - Run render-index.py --validate-only at the end
#
# Idempotent: existing files are NEVER overwritten unless --force is given;
# the guidance snippet is appended only if its sentinel marker is missing.
#
# Composes with project-knowledge-harness (TODO.md / backlog/ / pitfalls/):
# if those are absent, this script suggests setting them up but does not
# require them.
#
# Compatibility: macOS system Bash 3.2.

usage() {
  cat <<'EOF'
Usage: init.sh [OPTIONS]

Set up experiment-knowledge-harness files in a target project. Safe to re-run.

Options:
  --target DIR              Target project root (default: current directory)
  --project-name NAME       Substituted into <PROJECT NAME> placeholders
                            (default: basename of --target)
  --experiments-dir DIR     Research-memory root, relative to --target
                            (default: experiments)
  --agent-contract FILE     Path (relative to --target) to the agent contract
                            file receiving the guidance snippet. Default:
                            auto-detect AGENTS.md, CLAUDE.md,
                            .opencode/AGENTS.md, .cursorrules; created as
                            AGENTS.md if none exist.
  --force                   Overwrite LEDGER.md / ROADMAP.md / README.md
                            if they already exist.
  --no-validate             Skip the final render-index.py validation pass.
  -h, --help                Show this help and exit.

Heavy experiment outputs (caches, checkpoints, mlruns.db) should be
gitignored inside each experiment folder; the harness docs themselves are
meant to be committed.
EOF
}

target="."
project_name=""
experiments_dir="experiments"
agent_contract=""
force=0
do_validate=1

while [ $# -gt 0 ]; do
  case "$1" in
    -h|--help) usage; exit 0 ;;
    --target) target="$2"; shift 2 ;;
    --project-name) project_name="$2"; shift 2 ;;
    --experiments-dir) experiments_dir="$2"; shift 2 ;;
    --agent-contract) agent_contract="$2"; shift 2 ;;
    --force) force=1; shift ;;
    --no-validate) do_validate=0; shift ;;
    *) echo "Unknown argument: $1" >&2; usage >&2; exit 2 ;;
  esac
done

target_abs="$(cd "$target" && pwd)"
[ -n "$project_name" ] || project_name="$(basename "$target_abs")"

skill_dir="$(cd "$(dirname "$0")/.." && pwd)"
assets_dir="$skill_dir/assets"
scripts_dir="$skill_dir/scripts"

if [ ! -d "$assets_dir" ]; then
  echo "Error: assets/ not found next to scripts/ (looked in $assets_dir)" >&2
  exit 1
fi

exp_root="$target_abs/$experiments_dir"
agent_marker="<!-- experiment-knowledge-harness:agent-guidance -->"

render_template() {
  sed \
    -e "s|<PROJECT NAME>|${project_name}|g" \
    -e "s|experiments/|${experiments_dir}/|g" \
    "$1"
}

create_file() {
  local rel="$1"
  local src="$2"
  local dest="$exp_root/$rel"
  mkdir -p "$(dirname "$dest")"
  if [ -e "$dest" ] && [ "$force" -eq 0 ]; then
    echo "skip: $experiments_dir/$rel already exists (use --force to overwrite)"
    return
  fi
  render_template "$src" > "$dest"
  echo "create: $experiments_dir/$rel"
}

detect_agent_contract() {
  local candidates=(AGENTS.md CLAUDE.md .opencode/AGENTS.md .cursorrules)
  local c
  for c in "${candidates[@]}"; do
    if [ -e "$target_abs/$c" ]; then
      echo "$c"
      return
    fi
  done
  echo "AGENTS.md"
}

[ -n "$agent_contract" ] || agent_contract="$(detect_agent_contract)"

echo "Project root:    $target_abs"
echo "Project name:    $project_name"
echo "Experiments dir: $experiments_dir/"
echo "Agent contract:  $agent_contract"
echo

create_file "LEDGER.md" "$assets_dir/LEDGER.md.template"
create_file "ROADMAP.md" "$assets_dir/ROADMAP.md.template"
create_file "INBOX.md" "$assets_dir/INBOX.md.template"
create_file "README.md" "$assets_dir/experiments-README.md.template"

# Append agent guidance under a sentinel marker.
dest="$target_abs/$agent_contract"
if [ -e "$dest" ] && grep -qF "$agent_marker" "$dest" 2>/dev/null; then
  echo "skip: $agent_contract already contains $agent_marker"
else
  mkdir -p "$(dirname "$dest")"
  [ -e "$dest" ] || : > "$dest"
  end_marker="${agent_marker% -->} (end) -->"
  {
    printf '\n%s\n' "$agent_marker"
    render_template "$assets_dir/agent-guidance.md.template"
    printf '%s\n' "$end_marker"
  } >> "$dest"
  echo "append: $agent_contract"
fi

echo
if [ ! -e "$target_abs/TODO.md" ]; then
  echo "note: no TODO.md found — consider also setting up project-knowledge-harness"
  echo "      (engineering chores and pitfalls route there; the two compose)."
  echo
fi

if [ "$do_validate" -eq 1 ]; then
  echo "Validating surfaces..."
  python3 "$scripts_dir/render-index.py" --root "$exp_root" --validate-only || true
fi

cat <<EOF

Next steps:
  1. Replace the example finding / roadmap item with real content, or queue
     ideas straight into $experiments_dir/ROADMAP.md (payoff: + cat: required).
  2. Scaffold the first experiment:
       python3 $scripts_dir/new-experiment.py --title "..." --question "..." \\
         --axis "..." --baseline "..." --root $experiments_dir
  3. Render the index whenever front-matter changes:
       python3 $scripts_dir/render-index.py --root $experiments_dir
  4. Gitignore heavy outputs inside experiment folders (cache/, results/,
     mlruns.db) — commit the REPORTs, LEDGER, ROADMAP, README.
EOF
