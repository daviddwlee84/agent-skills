---
name: verifiable-surfaces
description: Design and verify exercisable surfaces on apps, CLIs, services, and config. Use when authoring a new CLI/tool/library/service in Python (uv + tyro / click / argparse), Node (commander/yargs), or Bash to ensure it exposes `--help`, `--dry-run`, `--print-config`, isolated-state smoke entrypoints, and explicit exit-code contracts. Also use when editing app/tool config, CLI args/env parsing, dotfiles such as chezmoi, Ansible playbooks, CI/deploy manifests, or generated/rendered config — forces syntax/schema, then app-native loader/parser/debug/dry-run, then narrowest harmless runtime smoke. The invariant: a surface that cannot be exercised cheaply and harmlessly was not actually verified, regardless of how much linting passed.
---

# Verifiable Surfaces

Apply this skill in two complementary modes:

- **Authoring mode** — when creating or extending a CLI, tool, library, or
  service, design surfaces that can be exercised cheaply and harmlessly:
  `--help`, `--dry-run`, `--print-config`, isolated-state smoke, explicit
  exit codes.
- **Verification mode** — when editing config, CLI arg/env parsing, dotfiles,
  Ansible, IaC, or any rendered/generated config, walk the verification
  ladder until the highest *harmless* gate has passed.

## Core Invariant

A surface that cannot be exercised cheaply and harmlessly was not actually
verified. Syntax checks, type checks, and lints are necessary but not
sufficient. If the program has its own loader, dry-run, or check command, run
it. If it does not have one, your authoring job is to add one.

## When To Use

**Authoring mode:**

- Writing a new Python CLI with uv + tyro, click, typer, or argparse
- Writing a new Node CLI with commander, yargs, or oclif
- Writing a new Bash script that takes args or has side effects
- Adding a new subcommand, flag, or env var to an existing tool
- Building a service/daemon with a config file
- Building an SDK/library that loads config or accepts complex inputs

**Verification mode:**

- Editing app/tool config: `next.config.*`, `components.json`, `.prettierrc`,
  `pyproject.toml`, `ruff.toml`, `docker-compose.yml`, `mkdocs.yml`,
  `pueue.yml`, DVC/MLflow config, service manifests
- Changing CLI argument parsing, env var parsing, config discovery order, or
  defaults that are only exercised after startup
- Updating dotfiles or generated config, especially chezmoi templates,
  shell init files, editor config, Git hooks, launchd/systemd units, or
  files that depend on `$HOME`, platform, hostname, or secrets
- Editing Ansible, Terraform, Kubernetes, Docker Compose, CI, deploy, or
  other automation where parse success can still fail at plan/apply/runtime
- Debugging "works in lint/build, breaks when the tool starts" failures

## When NOT To Use

- Pure documentation edits with no executable or loaded configuration
- Formatting-only edits where the tool's own formatter is the requested end
  state and no behavior changes
- Production deploy validation that needs credentials or live infra access the
  user has not approved. Stop at a harmless local smoke and report the gap.

## Authoring Mode: Design Verifiable Surfaces

Every CLI/tool/service surface you add must satisfy this checklist:

1. **`--help` is mandatory.** Show usage, every flag, examples, and exit
   codes. The agent (and the next human) reads this first.
2. **`--dry-run` for any side effect.** File writes, network calls, database
   mutations, config edits, deploys, restarts. Dry-run must still load the
   real config and resolve the real plan, not short-circuit before parsing.
3. **`--print-config` / `--show-config` for config-loading programs.** Print
   the fully resolved config (after env/file/CLI merging) so the user can
   diff what the program actually sees vs. what they edited.
4. **Isolated-state smoke entrypoint.** The tool must accept `--config <path>`
   and respect `$HOME` / `$XDG_CONFIG_HOME` overrides; never hard-code
   `~/.foo`. This lets `env -i HOME=$(mktemp -d) ...` exercise the real load
   path with zero blast radius.
5. **Explicit exit-code contract.** `0` for success; non-zero for failure
   classes (`1` runtime/user error, `2` usage error is a common convention).
   Document the codes in `--help`.
6. **Structured stdout, diagnostics on stderr.** Stdout is the program's
   data output (parseable when reasonable). Logs, progress, and errors go
   to stderr so callers can pipe stdout safely.
7. **Self-verification after authoring.** Before declaring done, run:
   `cmd --help`, `cmd --dry-run <smallest input>`, `cmd --print-config`
   (if applicable), an intentionally-bad input to confirm non-zero exit,
   and one isolated-state smoke (`env -i HOME=$(mktemp -d) ...`).

See `references/authoring-checklist.md` for concrete templates per
language (Python tyro/click, Node commander/yargs, Bash).

## Verification Mode: Verification Ladder

Pick the highest safe rung that exercises the actual failure mode. Do not
stop at a lower rung when the next harmless rung exists.

1. **Syntax/schema gate** — `yamllint`, `jsonschema`, `ansible-playbook
   --syntax-check`, `terraform validate`, `docker compose config`,
   `mkdocs build`, `tsc --noEmit`.
2. **Rendered/applied config gate** — render templates and generated files,
   then validate those outputs. For chezmoi, inspect `chezmoi diff`,
   `chezmoi apply --dry-run --verbose`, or `chezmoi execute-template`; do
   not validate only the `.tmpl` source.
3. **App/tool-native loader gate** — prefer the command the app itself
   exposes: `config check`, `doctor`, `debug`, `--print-config`,
   `--show-config`, `--dry-run`, `--check`, `validate`, `plan`, or a small
   script that imports and loads the same config module used at startup.
4. **Compile/build gate** — when config influences generated code, bundling,
   routing, plugins, import paths, or type definitions, run the narrowest
   compile/build that loads it.
5. **Harmless runtime smoke** — for runtime-only failures, run the narrowest
   local smoke with isolated state: `/tmp`, temp `$HOME`, temp config path,
   temp database/file store, local container, `--check`, `--dry-run`,
   limited tag, limited target, or loopback-only service.

Record which rung you reached. If you cannot reach the app-native loader or
runtime smoke safely, say so explicitly and explain what is still untested.

See `references/config-examples.md` for concrete commands per ecosystem
(Ansible, chezmoi, JS/TS, Python settings, Docker Compose, Kubernetes,
Terraform/OpenTofu, generic loaders).

## Default Workflow

1. Identify which mode applies. Authoring (new surface) and verification
   (changed surface) often co-occur — handle both.
2. **Authoring**: walk the 7-point checklist above. Stub out missing items
   before the change is "done."
3. **Verification**: list the minimum ladder for this change, then run the
   lowest cheap gate first and continue until the highest harmless gate has
   passed.
4. When a gate fails, fix the cause and re-run all earlier affected gates.
5. Summarize the exact commands and the highest gate passed.

## Ansible Rule

`ansible-playbook --syntax-check` is only the first step. It does not execute
tasks, evaluate all runtime conditions, contact targets, validate module side
effects, or prove variables are correct for the selected hosts. If a
playbook, role, inventory, or variable change can fail at execution time, run
the narrowest relevant smoke: `--check`, `--diff`, `--tags`, `--skip-tags`,
`--limit`, localhost/container inventory, or a role-specific test harness.

## Gotchas

- **A surface without `--dry-run` is a surface you cannot rehearse.** When
  authoring, add it before the destructive code path, not after.
- **`--help` must list exit codes and side effects.** "What does this
  command do?" should be answerable without reading source.
- **Validate rendered config, not just source templates.** Template syntax
  can pass while the rendered file has invalid paths, missing env vars,
  duplicate keys, or host-specific values the app rejects.
- **The app's own loader is the authority.** Generic YAML/JSON/TOML parsing
  does not catch semantic errors such as unsupported keys, wrong plugin
  names, invalid enum values, env interpolation bugs, or changed default
  paths.
- **Dry-run must still load.** A no-op preview that never invokes the real
  parser is not enough. Prefer dry-runs that render, resolve includes, load
  plugins, and build the final plan/config.
- **Runtime-only failures need harmless smoke.** Use temp dirs, temp `$HOME`,
  temp config files, local containers, check mode, or tag/target narrowing
  rather than skipping runtime validation entirely.
- **Secrets and machine-specific config require isolation.** Do not read or
  write real home-directory state, cloud resources, production inventories,
  or credentialed endpoints unless the user explicitly asked for that
  level.
- **Report the gap, not false confidence.** If only syntax validation was
  safe, say "syntax passed; loader/runtime not exercised" and name the
  command that should be run in the right environment.
