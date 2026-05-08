# Authoring Checklist: Verifiable Surfaces

Use this when authoring a new CLI, tool, library, or service — or when
extending one. Stub each item before declaring the change "done." If you
skip an item, write down which one and why in the change summary.

## Universal Checklist

- [ ] `--help` lists usage, every flag, examples, and exit codes
- [ ] `--dry-run` exists for any side-effecting operation and **still loads
      the real config / resolves the real plan**
- [ ] `--print-config` (or `--show-config`) prints the fully-merged effective
      config when the program loads config
- [ ] `--config <path>` accepted; `$HOME` / `$XDG_CONFIG_HOME` respected;
      no hard-coded `~/.foo` paths
- [ ] Exit-code contract documented in `--help`
      (`0` success / `1` runtime/user error / `2` usage error / extras as
      needed)
- [ ] Stdout is data; stderr is logs and diagnostics
- [ ] Self-verification run before commit: `--help`, `--dry-run`,
      `--print-config`, an intentionally-bad input that returns non-zero,
      and one isolated-state smoke

## Python: uv + tyro (dataclass)

```python
# /// script
# requires-python = ">=3.11"
# dependencies = ["tyro>=0.8"]
# ///
"""mytool — does X. See --help."""
from __future__ import annotations
import dataclasses, json, os, sys
import tyro

@dataclasses.dataclass
class Args:
    config: str = "config.toml"
    """Path to config file (overrides $MYTOOL_CONFIG)."""
    dry_run: bool = False
    """Resolve plan and print actions; do not mutate."""
    print_config: bool = False
    """Print the fully-merged effective config to stdout and exit."""

def main(args: Args) -> int:
    cfg = load_config(args.config)
    if args.print_config:
        json.dump(cfg, sys.stdout, indent=2)
        return 0
    plan = build_plan(cfg)
    if args.dry_run:
        for step in plan:
            print(step)            # stdout: data
        return 0
    try:
        execute(plan)
    except UserError as e:
        print(f"error: {e}", file=sys.stderr)
        return 1
    return 0

if __name__ == "__main__":
    sys.exit(main(tyro.cli(Args)))
```

Self-verification:

```bash
uv run mytool.py --help
uv run mytool.py --print-config
uv run mytool.py --dry-run --config examples/min.toml
env -i HOME="$(mktemp -d)" PATH="$PATH" uv run mytool.py --dry-run
uv run mytool.py --config /nonexistent.toml; echo "exit=$?"   # expect non-zero
```

## Python: click

```python
import click

@click.command()
@click.option("--config", default="config.toml", show_default=True,
              help="Path to config file.")
@click.option("--dry-run", is_flag=True,
              help="Resolve plan and print actions; do not mutate.")
@click.option("--print-config", is_flag=True,
              help="Print effective config and exit.")
def cli(config, dry_run, print_config):
    """mytool — does X."""
    ...

if __name__ == "__main__":
    cli()
```

`click` already wires `--help`. Document exit codes in the docstring.

## Node: commander

```js
#!/usr/bin/env node
import { Command } from "commander";
import fs from "node:fs";

const program = new Command();
program
  .name("mytool")
  .description("Does X.")
  .option("-c, --config <path>", "config file", "config.json")
  .option("--dry-run", "resolve plan; do not mutate", false)
  .option("--print-config", "print effective config and exit", false)
  .addHelpText("after", `
Exit codes:
  0  success
  1  runtime/user error
  2  usage error
`);
program.parse();
const opts = program.opts();
const cfg = loadConfig(opts.config);
if (opts.printConfig) { process.stdout.write(JSON.stringify(cfg, null, 2)); process.exit(0); }
const plan = buildPlan(cfg);
if (opts.dryRun) { for (const s of plan) console.log(s); process.exit(0); }
try { await execute(plan); } catch (e) { console.error(`error: ${e.message}`); process.exit(1); }
```

## Node: yargs

```js
import yargs from "yargs";
import { hideBin } from "yargs/helpers";

const argv = yargs(hideBin(process.argv))
  .scriptName("mytool")
  .option("config", { type: "string", default: "config.json" })
  .option("dry-run", { type: "boolean", default: false })
  .option("print-config", { type: "boolean", default: false })
  .strict()
  .help()
  .epilogue("Exit codes: 0 ok / 1 runtime / 2 usage")
  .parseSync();
```

`yargs.strict()` rejects unknown flags with a usage error, which gives you
the exit-code-2 contract for free.

## Bash

This repo's `skills/local/skill-author/assets/script-bash.template` is the
canonical pattern. Minimum viable shape:

```bash
#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'EOF'
Usage: mytool [OPTIONS] <input>

Options:
  --config PATH      Config file (default: ./config.yml)
  --dry-run          Show planned actions; do not mutate
  --print-config     Print effective config and exit
  --help, -h         Show this help and exit

Exit codes:
  0  success
  1  runtime/user error
  2  usage error
EOF
}

die() { printf 'error: %s\n' "$*" >&2; exit "${2:-1}"; }

CONFIG="./config.yml"
DRY_RUN=0
PRINT_CONFIG=0

while [ $# -gt 0 ]; do
  case "$1" in
    --config)        CONFIG="$2"; shift 2 ;;
    --dry-run)       DRY_RUN=1; shift ;;
    --print-config)  PRINT_CONFIG=1; shift ;;
    --help|-h)       usage; exit 0 ;;
    -*)              die "unknown flag: $1 (try --help)" 2 ;;
    *)               INPUT="$1"; shift ;;
  esac
done

[ -n "${INPUT:-}" ] || die "missing <input> (try --help)" 2
[ -f "$CONFIG" ]    || die "config not found: $CONFIG" 1

if [ "$PRINT_CONFIG" = "1" ]; then cat "$CONFIG"; exit 0; fi
if [ "$DRY_RUN" = "1" ];      then printf 'would process: %s\n' "$INPUT"; exit 0; fi

# real work here
```

## Library / SDK Surfaces

When you ship a library that loads config or accepts complex inputs:

- Provide a pure `load_config(path) -> Config` (or `parseConfig`) that the
  CLI wraps. Tests and integrators import that function directly.
- Expose a `validate_config(cfg) -> list[Error]` that returns errors as
  data, not exceptions, so callers can surface multiple issues at once.
- Document defaults and discovery order (file → env → CLI). Provide a
  `Config.dump()` / `toJSON()` so callers can implement their own
  `--print-config`.

## Self-Verification Snippet (any language)

```bash
# 1. help works
mytool --help >/dev/null

# 2. dry-run on smallest valid input
mytool --dry-run --config fixtures/minimal.yml

# 3. print-config matches the loaded file (if applicable)
mytool --print-config --config fixtures/minimal.yml

# 4. bad input returns non-zero
mytool --config /nonexistent 2>/dev/null; test $? -ne 0

# 5. isolated-state smoke
env -i HOME="$(mktemp -d)" PATH="$PATH" mytool --dry-run
```

If any of these five fails, the surface is not yet verifiable.
