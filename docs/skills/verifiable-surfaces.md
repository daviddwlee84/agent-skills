# verifiable-surfaces

Design and verify exercisable surfaces on apps, CLIs, services, and config.
This skill operates in two complementary modes:

- **Authoring mode** — when creating a new CLI, tool, library, or service,
  ensure it exposes `--help`, `--dry-run`, `--print-config`, isolated-state
  smoke entrypoints, and an explicit exit-code contract.
- **Verification mode** — when editing config, CLI args/env parsing,
  dotfiles, Ansible, IaC, or generated/rendered config, walk the
  verification ladder until the highest *harmless* gate has passed.

The invariant: a surface that cannot be exercised cheaply and harmlessly
was not actually verified, regardless of how much linting passed.

## When the skill triggers

**Authoring mode:**

- Writing a new Python CLI with uv + tyro / click / argparse, a Node CLI
  with commander/yargs/oclif, or a Bash script that takes args or has side
  effects
- Adding a new subcommand, flag, or env var to an existing tool
- Building a service/daemon with a config file or an SDK that loads config

**Verification mode:**

- Editing app/tool config (`next.config.*`, `pyproject.toml`, `mkdocs.yml`,
  `docker-compose.yml`, `pueue.yml`, DVC/MLflow config, service manifests)
- Changing CLI args, env parsing, config discovery order, or startup-time
  defaults
- Updating dotfiles or generated config (chezmoi templates, shell init
  files, Git hooks, editor config, launchd/systemd units, Ansible,
  Terraform, Kubernetes, CI, deploy manifests)

## Authoring checklist (universal)

1. `--help` lists usage, every flag, examples, and exit codes
2. `--dry-run` exists for any side-effecting operation and **still loads
   the real config / resolves the real plan**
3. `--print-config` (or `--show-config`) prints the fully-merged effective
   config when the program loads config
4. `--config <path>` accepted; `$HOME` / `$XDG_CONFIG_HOME` respected
5. Exit-code contract documented in `--help`
6. Stdout is data; stderr is logs and diagnostics
7. Self-verification before declaring done: `--help`, `--dry-run`,
   `--print-config`, intentionally-bad input → non-zero, isolated-state
   smoke (`env -i HOME=$(mktemp -d) ...`)

## Verification ladder

1. Syntax/schema gate
2. Rendered/applied config gate (validate output, not template source)
3. App/tool-native loader gate (`config check`, `doctor`, `--print-config`,
   `plan`, `--dry-run`)
4. Compile/build gate
5. Harmless runtime smoke (temp `$HOME`, `/tmp`, container, `--check`,
   limited tag/target)

## Examples

The bundled references cover both modes:

- [`references/authoring-checklist.md`](https://github.com/daviddwlee84/agent-skills/blob/main/skills/local/verifiable-surfaces/references/authoring-checklist.md)
  — Python (tyro/click), Node (commander/yargs), Bash templates plus a
  five-command self-verification snippet
- [`references/config-examples.md`](https://github.com/daviddwlee84/agent-skills/blob/main/skills/local/verifiable-surfaces/references/config-examples.md)
  — chezmoi (`apply --dry-run --verbose`, `diff`, `execute-template`),
  Ansible (`--syntax-check` is gate 1 only; then `--check`/`--diff`/
  `--tags`/`--limit`), JS/TS, Python settings, Docker Compose, Kubernetes,
  Terraform/OpenTofu

## Canonical SKILL.md

See [skills/local/verifiable-surfaces/SKILL.md](https://github.com/daviddwlee84/agent-skills/blob/main/skills/local/verifiable-surfaces/SKILL.md)
for the full triggering description, dual-mode workflow, gotchas, and
reference links.
