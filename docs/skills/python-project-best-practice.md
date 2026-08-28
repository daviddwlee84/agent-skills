# python-project-best-practice

An opinionated baseline for Python projects that both people and agents work
in — and the two entry points that get you there: **scaffold a new project**,
or **score and modernize an existing one**. Same conventions, one skill.

The bias throughout: every operation has one canonical, discoverable,
non-interactive command. That is what makes a repo workable by an agent, and
it happens to be what makes it pleasant for humans.

> Scope note: this skill deliberately does **not** restate
> [`verifiable-surfaces`](verifiable-surfaces.md) (CLI surface design),
> [`marimo-batch-mlflow`](marimo-batch-mlflow.md) (dual-mode notebooks),
> [`fastapi-ai-patterns`](fastapi-ai-patterns.md) (production FastAPI), or
> [`mkdocs-site-bootstrap`](mkdocs-site-bootstrap.md) (docs sites). It links
> to them and fills the gap none of them covered: the project itself.

## The defaults it argues for

| Concern | Default | Why not the alternative |
|---|---|---|
| Environment | `uv` + committed `uv.lock` + `.python-version` | poetry/pip-tools/conda all solve less of it; `uv.lock` never constrains your users |
| Layout | `src/<pkg>/` | a flat layout imports the source dir, so missing `__init__.py` / package data passes tests and breaks installs |
| Dev deps | PEP 735 `[dependency-groups]` | an extra is **published**; your test runner should not be in your users' dependency graph |
| Lint + format | `ruff check` + `ruff format` | `ruff format` *is* a black reimplementation — running both makes them fight |
| Types | `ty` (pinned exactly), mypy documented as the conservative swap | `ty` is 0.0.x: fast enough that people run it, unstable enough that `>=` is a trap |
| CLI | Tyro, one frozen dataclass per subcommand | commands as data are testable without argv or subprocesses |
| Completion | `--tyro-write-completion` | built in; shtab/argcomplete wiring is redundant |
| Logging | loguru at entry points, stdlib in library code | a library that calls `loguru.logger.add()` hijacks the importing program's logging |
| Config | pydantic-settings, defaults < `.env` < environment | and `<tool> info` prints what actually resolved |
| Task runner | `Justfile` (taskipy noted) | `just` needs no Python, so `just setup` can bootstrap the venv itself |

## What ships

- The full SKILL.md ([SKILL.md](https://github.com/daviddwlee84/agent-skills/blob/main/skills/local/python-project-best-practice/SKILL.md)) — decision spine, two workflows,
  and a 22-item gotchas section.
- **Nine references**, loaded on demand:
    - [`uv-and-pyproject.md`](https://github.com/daviddwlee84/agent-skills/blob/main/skills/local/python-project-best-practice/references/uv-and-pyproject.md) — commands,
      groups vs extras, lockfile policy, interpreter pinning, build backends,
      `uv tool install` / Trusted Publishing, workspaces.
    - [`tyro-cli.md`](https://github.com/daviddwlee84/agent-skills/blob/main/skills/local/python-project-best-practice/references/tyro-cli.md) — dataclass commands,
      subcommand unions, module splits, completion, config objects.
    - [`quality-gates.md`](https://github.com/daviddwlee84/agent-skills/blob/main/skills/local/python-project-best-practice/references/quality-gates.md) — ruff rule
      selection, `ty` vs mypy, pytest layout, coverage placement, CI, pre-commit.
    - [`logging-and-config.md`](https://github.com/daviddwlee84/agent-skills/blob/main/skills/local/python-project-best-practice/references/logging-and-config.md) — the
      app/library layering rule, the three loguru traps, pydantic-settings, direnv.
    - [`notebooks-and-widgets.md`](https://github.com/daviddwlee84/agent-skills/blob/main/skills/local/python-project-best-practice/references/notebooks-and-widgets.md) —
      where notebooks live, dual mode, ruff conflicts, packaged anywidgets.
    - [`api-and-services.md`](https://github.com/daviddwlee84/agent-skills/blob/main/skills/local/python-project-best-practice/references/api-and-services.md) — the FastAPI
      stub's boundary, and a decision rule for **skill vs MCP** (usually: neither,
      add a subcommand).
    - [`rust-pyo3.md`](https://github.com/daviddwlee84/agent-skills/blob/main/skills/local/python-project-best-practice/references/rust-pyo3.md) — maturin layout, abi3, the
      stale-binary trap, why type checkers need a hand-written `.pyi`.
    - [`agent-interface.md`](https://github.com/daviddwlee84/agent-skills/blob/main/skills/local/python-project-best-practice/references/agent-interface.md) — AGENTS.md vs
      README vs the package's own skill, the symlink rule, the docs-drift gate.
    - [`legacy-refactor.md`](https://github.com/daviddwlee84/agent-skills/blob/main/skills/local/python-project-best-practice/references/legacy-refactor.md) — the migration
      ladder, one rung per PR, and what *not* to migrate.
- **Two PEP 723 scripts** (`uv run`, inline deps, JSON on stdout):
    - [`new-python-project.py`](https://github.com/daviddwlee84/agent-skills/blob/main/skills/local/python-project-best-practice/scripts/new-python-project.py) — scaffold
      from the bundled template tree. `--profile {minimal,cli,lib,api,ml,rust}`,
      `--dry-run`, `--force`, `--no-git`. Offline; writes nothing outside the
      target directory.
    - [`audit-python-project.py`](https://github.com/daviddwlee84/agent-skills/blob/main/skills/local/python-project-best-practice/scripts/audit-python-project.py) — 26
      read-only checks with evidence and a fix hint, plus an ordered
      `migration_plan[]`. `--format {json,table}`, `--fail-on {fail,warn,never}`.
      Deliberately has **no `--fix`**.
- **A template tree** (`assets/project/`, 29 `.tmpl` files) plus
  [`assets/manifest.toml`](https://github.com/daviddwlee84/agent-skills/blob/main/skills/local/python-project-best-practice/assets/manifest.toml) mapping each destination to
  the profiles that get it. A file not in the manifest is never copied, and the
  generator exits 4 if the manifest and the tree disagree either way.

## Profiles

Additive, so "agentic later" costs nothing now.

| Profile | Adds |
|---|---|
| `minimal` | package, tests, Justfile, CI, AGENTS.md |
| `cli` *(default)* | Tyro CLI, loguru, pydantic-settings, `[project.scripts]` |
| `lib` | publishing metadata, `py.typed` |
| `api` | FastAPI app with `/docs` and `/openapi.json` |
| `ml` | a marimo notebook that is also a batch CLI |
| `rust` | maturin backend, PyO3 crate, `.pyi` stubs |

## The docs-drift gate

The piece worth stealing even if you use none of the rest. Prose about a CLI
rots the first time someone renames a flag, so the generated project makes it
a build artifact instead:

```bash
just docs-sync     # rewrite the CLI block in AGENTS.md + .agents/skills/ from --help
just docs-check    # exit 1 if the committed block is stale — part of `just check`
```

`scripts/sync_agent_docs.py` runs `python -m <pkg>.cli --help` plus each
subcommand's `--help`, strips ANSI, and splices the result between
`<!-- BEGIN CLI -->` markers. Because `--check` runs in the gate and in CI, a
flag rename that skips the docs fails the build.

## Verified, not asserted

Every profile was generated and run before shipping: `uv sync` → `just check`
(ruff format, ruff lint, `ty`, pytest, docs-drift) green on all six, coverage
between 89% and 100%, and `uv tool install` → run → uninstall exercised
end-to-end. Two claims changed as a result of checking them:

- **Tyro already ships shell completion.** The first draft told you to wire up
  shtab. It does not need it — `--tyro-write-completion {bash,zsh,tcsh,fish} PATH`
  is built in, and `--tyro-print-completion` is deprecated because a stray
  `print()` corrupts the output.
- **`uv sync` silently keeps a stale Rust binary.** Editing `rust/src/lib.rs`
  and re-running `uv sync` leaves the old `.so` in place with no warning —
  including any debug prints you just added. Confirmed by experiment;
  `uv sync --reinstall-package <slug>` is the fix.

## Related

[`verifiable-surfaces`](verifiable-surfaces.md) ·
[`project-knowledge-harness`](project-knowledge-harness.md) ·
[`agent-history-hygiene`](agent-history-hygiene.md) ·
[`mkdocs-site-bootstrap`](mkdocs-site-bootstrap.md) ·
[`git-workflow`](git-workflow.md) ·
[`marimo-batch-mlflow`](marimo-batch-mlflow.md) ·
[`fastapi-ai-patterns`](fastapi-ai-patterns.md) ·
`cli-release-distribution`
