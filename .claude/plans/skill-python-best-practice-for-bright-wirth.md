# Plan: `python-project-best-practice` skill

## Context

There is no skill in this repo that owns Python project conventions. `uv`,
`ruff`, `pytest`, and `pyproject.toml` appear only as *ambient assumptions*
inside `mkdocs-site-bootstrap`, `fastapi-ai-scaffold`, `mlflow-tracking`, and
`skill-author/references/script-design.md` — nobody teaches them. `TODO.md`'s
`## P?` lane has carried **`[?/M] Python + uv workflow skill`** as its first
item for exactly this gap.

The user supplied 18 requirements covering layout/uv, Tyro CLIs, marimo
notebooks, loguru, TDD, task runners, agent-facing docs, FastAPI, Rust/PyO3,
scaffolding, and legacy refactor. Decisions taken: **one skill + references**,
name **`python-project-best-practice`**, **Justfile primary** (taskipy as
escape hatch), and scaffolded projects **point at** the companion skills via
`npx skills add` + AGENTS.md rather than vendoring copies.

Intended outcome: from-zero scaffold *and* legacy-refactor guide in one skill,
built to house style (decision spine ≤500 lines, progressive-disclosure
references, `.tmpl` asset tree, JSON-emitting agentic scripts).

## Boundaries — what this skill does NOT own

Deliberate delegation, stated in `## When NOT to use` so the skill doesn't
restate three existing skills:

| Topic | Owner |
|---|---|
| `--help` / `--dry-run` / `--print-config` / exit-code design | `verifiable-surfaces` (its `references/authoring-checklist.md` already has a "Python: uv + tyro (dataclass)" section) |
| marimo dual-mode UI+script with Tyro | `marimo-batch-mlflow`; marimo mechanics → `vendor/marimo-notebook`; widgets → `vendor/anywidget` |
| FastAPI service internals | `fastapi-ai-patterns` / `fastapi-ai-scaffold` |
| Docs site + llms.txt | `mkdocs-site-bootstrap` |
| Go/Rust compiled-binary release | `cli-release-distribution` (explicitly excludes Python — this skill fills that hole with `uv tool install` / PyPI) |
| pre-commit + transcript hygiene | `agent-history-hygiene` |
| TDD discipline itself | `vendor/engineering-fundamentals/tdd` |

Stays a separate future skill (existing `P?` items, do **not** absorb):
Streamlit, data-viz, Docker Compose, GitHub Actions. PyO3 gets a *reference*
here; the `[?/L] Rust-backed Python package with PyO3` P? item stays open for a
deeper skill.

## Coverage map — the 18 points

| # | Requirement | Where it lands |
|---|---|---|
| 1 | uv, src layout, README getting-started | `references/uv-and-pyproject.md` + template |
| 2 | Tyro, subcommand modules, completion, `uv tool install` | `references/tyro-cli.md` |
| 3 | marimo script mode, `notebooks/`, anywidget | `references/notebooks-and-widgets.md` (delegates) |
| 4 | loguru | `references/logging-and-config.md` |
| 5 | CLI + AGENTS.md kept in sync on every package change | `references/agent-interface.md` + `just sync-agent-docs` gate |
| 6 | Recommend companion skills | `references/agent-interface.md` + scaffold `next_steps[]` |
| 7 | Legacy refactor guide | Workflow B + `references/legacy-refactor.md` + audit script |
| 8 | TDD loop | `references/quality-gates.md` |
| 9 | Non-package helpers in `scripts/` | SKILL.md layout section (PEP 723 rule) |
| 10 | Justfile (taskipy noted) | template `Justfile.tmpl` |
| 11 | Package ships its own agent skill | template `.agents/skills/PACKAGE/SKILL.md.tmpl` |
| 12 | Scaffold CLI | `scripts/new-python-project.py` (PEP 723 + Tyro — dogfoods the skill) |
| 13 | FastAPI + Pydantic + OpenAPI | `references/api-and-services.md` (thin, delegates) |
| 14 | MCP when a skill isn't enough | same reference, decision rule → `vendor/mcp-builder` |
| 15 | Start minimal, grow | scaffold `--profile` ladder, each additive |
| 16 | Rust + PyO3 | `references/rust-pyo3.md` |
| 17 | Project-type extra skills | profile → recommended-skills table |
| 18 | ruff / formatting / LSP | `references/quality-gates.md` |
| — | `.envrc` / direnv | template `.envrc.tmpl` (user's exact snippet) + gotcha |

### Gaps found in the original 18 (added)

Type checking; PEP 735 `[dependency-groups]` vs extras; `uv.lock` commit
policy; `.python-version` pinning; `py.typed`; build-backend choice
(hatchling / `uv_build` / maturin); versioning + `uv build`/`uv publish` with
Trusted Publishing; pydantic-settings + `.env` (pairs with the user's
`.envrc`); pytest layout + coverage gate; CI workflow with `astral-sh/setup-uv`
+ `uv lock --check`; uv workspaces for monorepos; `[project.scripts]` entry
points as the precondition for `uv tool install`.

## Opinionated defaults (the "avoid outdated practices" payload)

- `uv` + **src layout** (`src/<pkg>/`), `uv python pin`, commit `uv.lock`.
- Dev tooling in **PEP 735 `[dependency-groups]`**, not
  `[project.optional-dependencies]` — a group is not published to PyPI.
- **`ruff check` + `ruff format`; do not also install black.** This corrects
  point 18: `ruff format` *is* a black reimplementation and the two fight over
  magic trailing commas.
- Type check with **`ty`** in the default `Justfile` (matches the approved
  preview); `references/quality-gates.md` documents mypy as the conservative
  choice and flags that `ty` is pre-1.0.
- **loguru in applications/CLIs only.** Libraries use stdlib
  `logging.getLogger(__name__)` + `NullHandler`; the template ships an
  `InterceptHandler` bridge.
- Build backend **hatchling** (`uv_build` noted for lean packages, `maturin`
  for Rust).
- Distribution tier 0 is `uv tool install git+https://…@v0.1.0`; PyPI via
  `uv build` + `uv publish` with **Trusted Publishing (OIDC), no API token**.

## Deliverable

`skills/local/python-project-best-practice/`, created with
`bash skills/local/skill-author/scripts/new-skill.sh --local python-project-best-practice`
(LOCAL auto-detect; it also fans out `.agents/skills/` + `.claude/skills/`
symlinks — **remove both afterwards**, per CLAUDE.md this is a downstream-only
skill and must not load into every in-repo session).

### `SKILL.md` (~350–420 lines, hard cap 500)

Section order follows `skills/local/skill-author/assets/SKILL.md.template`:

1. Title + one-paragraph overview.
2. `## Core principles` — clear / portable / plug-and-play / easy to use,
   each restated as a testable invariant (e.g. "one canonical command per
   operation, discoverable from `just --list` and `--help`").
3. `## When to use` / `## When NOT to use` (the delegation table above).
4. `## Authoritative sources` — uv, tyro, ruff, ty, loguru, pydantic-settings,
   marimo, maturin, PyPA packaging. Copy the `dvc-ml-workflow` /
   `mlflow-tracking` instruction verbatim in spirit: *fetch the doc page, don't
   guess — uv's CLI surface changes between minor versions.*
5. `## The canonical layout` — single annotated tree block (output template).
6. `## Decision: which profile?` — table mapping
   `minimal | cli | lib | api | ml | rust` → template chunks, references to
   read, and companion skills to recommend (point 17).
7. `## Workflow A — new project from zero` (scaffold → `uv sync` → `just check`
   → register agent docs → offer companion skills).
8. `## Workflow B — modernize an existing project` — run the audit, then the
   **migration ladder, one rung per PR**: env/lock → src layout → dependency
   groups → ruff → types → tests/CI → CLI entry point → agent docs.
9. `## Available scripts`, `## Bundled assets`, `## Reference files`
   (each with an explicit *load when…* condition).
10. `## Gotchas` — stays in SKILL.md, never moved to a reference.
11. `## Related skills`.

Frontmatter `description` — single-quoted (contains `:` and backticks),
~480 chars, inside the 120–500 preferred band:

> 'Opinionated modern Python project conventions for the agentic-coding era:
> uv + src layout, Tyro CLIs with shell completion, marimo notebooks in script
> mode, loguru, ruff + type + pytest gates behind a Justfile, and an
> AGENTS.md/CLAUDE.md contract the agent can drive. Use when starting a new
> Python project or package, scaffolding a pyproject.toml, choosing a
> CLI/test/lint/logging stack, making a tool installable via `uv tool install`,
> or modernizing a legacy setup.py / requirements.txt / conda repo.'

### `## Gotchas` (the highest-value section — draft contents)

1. `uv sync` removes anything not in the lock — a manual `uv pip install`
   vanishes on the next sync. Use `uv add`.
2. Don't pair black with `ruff format`.
3. Flat layout imports your *source dir*, not the installed package — missing
   `__init__.py` / package-data bugs pass tests and break users. src layout is
   what makes `uv run pytest` exercise the real artifact.
4. loguru in a library hijacks the host app's logging config.
5. `logger.add()` without `logger.remove()` duplicates every line (loguru
   installs a default stderr sink at import).
6. `[dependency-groups]` vs `[project.optional-dependencies]`: extras are
   published and consumer-installable, groups are not. `uv sync` installs `dev`
   by default.
7. `uv.lock` pins *your* dev env only — it is ignored when your package is
   installed as someone's dependency.
8. `uv run` re-syncs first; `--no-sync` for hot loops.
9. `.python-version` is read by both uv and pyenv — a stale value silently
   changes the interpreter. Write it with `uv python pin`.
10. direnv cannot change `PS1`, so there is no `(.venv)` prompt even when the
    env is active — and `.envrc` needs `direnv allow` after every edit.
11. marimo notebooks are real `.py`: ruff will flag `E402`/unused-name and the
    formatter can reorder cell imports. Add `per-file-ignores` for `notebooks/`.
12. Tyro has no built-in shell completion — it comes from `shtab` over
    `tyro.extras.get_parser()`, and package managers never install completions
    for you (cross-ref `cli-release-distribution` Workflow D).
13. `uv tool install` needs `[project.scripts]`; `python -m pkg` alone gives the
    user no command.
14. Never replace the `AGENTS.md`↔`CLAUDE.md` symlink with a real file (git
    mode `120000`; a Windows checkout without symlink support materializes a
    text file containing the path).
15. PEP 723 helpers in `scripts/` must not import your package unless it is a
    declared script dependency.
16. Don't `uv add -r requirements.txt` blindly — it promotes transitive pins to
    direct dependencies. Separate direct from transitive first.
17. uv does not supply non-Python system libraries; some scientific stacks
    still need conda or OS packages.
18. maturin: `uv sync` does not rebuild the Rust extension — run
    `uv run maturin develop --uv` after every Rust edit.
19. Trusted Publishing means no PyPI token in Actions secrets.

**Verify before shipping** (do not write from memory): the shtab/`get_parser`
completion recipe, `ty`'s current CLI + pre-1.0 status, PEP 735 group support
in the pinned uv version, and current `astral-sh/setup-uv` major (TODO.md line
17 tracks a pending bump to `@v6`).

### `references/` (9 files — every one must be linked from SKILL.md or `lint-skill.sh` fails)

| File | Load when |
|---|---|
| `uv-and-pyproject.md` | writing/fixing `pyproject.toml`, lockfile, python pin, workspaces, build backend, versioning, publishing |
| `tyro-cli.md` | building or splitting a CLI, adding completions, entry points |
| `quality-gates.md` | configuring ruff/type checker/pytest/coverage/pre-commit/CI |
| `logging-and-config.md` | wiring loguru, pydantic-settings, `.env`/direnv |
| `notebooks-and-widgets.md` | adding `notebooks/` or a packaged anywidget |
| `api-and-services.md` | project exposes HTTP or the user asks "skill or MCP?" |
| `rust-pyo3.md` | adding a compiled extension |
| `agent-interface.md` | writing AGENTS.md, the in-repo self-skill, or the drift gate |
| `legacy-refactor.md` | Workflow B — interpreting the audit scorecard |

### `assets/project/` — `.tmpl` skeleton

Same mechanism as `skills/local/fastapi-ai-scaffold/assets/project/`: every
file ends `.tmpl`, the generator strips the suffix and substitutes
`PROJECT_SLUG_PLACEHOLDER` / `PACKAGE_NAME_PLACEHOLDER`. Profile-conditional
chunks use `__IF_CLI__` / `__END_CLI__` marker lines, matching the
`__MARKER__` convention already used by
`skills/local/mkdocs-site-bootstrap/scripts/init-docs-site.sh`.

```
pyproject.toml  README.md  AGENTS.md  Justfile  .python-version
.gitignore  .envrc  .env.example
src/PACKAGE/{__init__.py, py.typed, logging.py, settings.py}
src/PACKAGE/cli/{__init__.py, main.py, completion.py}
tests/{test_smoke.py, test_cli.py}
notebooks/example.py            # marimo dual-mode, points at marimo-batch-mlflow
scripts/README.md               # PEP 723 helper convention
.agents/skills/PACKAGE/SKILL.md # the package's own agent skill (point 11)
.github/workflows/ci.yml
```

`CLAUDE.md` is created by the generator as a symlink to `AGENTS.md` (real file
= `AGENTS.md`, the cross-agent standard). Note: this repo itself uses the
inverse direction; the direction is arbitrary as long as one side is a symlink.

### `scripts/` — both PEP 723 + Tyro (the skill eats its own cooking)

- **`new-python-project.py <target-dir>`** — `--profile {minimal,cli,lib,api,ml,rust}`,
  `--name SLUG`, `--python 3.13`, `--dry-run`, `--force`, `--no-git`, `--help`.
  Copies the `.tmpl` tree offline (no network, no `uv init`), creates the
  `CLAUDE.md` symlink, `git init` unless `--no-git`. **JSON on stdout**
  (`{project, package, profile, path, files[], recommended_skills[], next_steps[]}`),
  prose on stderr. `next_steps[]` carries `uv sync`, `just check`, and
  `npx skills@latest add daviddwlee84/agent-skills/skills`.
- **`audit-python-project.py [path]`** — read-only scorecard (~20 checks: src
  layout, `uv.lock`, `.python-version`, ruff configured, black+ruff conflict,
  groups-vs-extras, `tests/`, `[project.scripts]`, `py.typed`, AGENTS.md,
  Justfile, legacy `setup.py`/`requirements.txt`/`environment.yml`/`poetry.lock`,
  loguru-imported-in-library, unpinned CI actions). Emits
  `{checks:[{id,status,evidence,fix}], migration_plan:[…]}` with
  `--format json|table`. Explicitly has **no `--fix`** — Workflow B applies
  changes one rung per PR under human review.

Both: shebang `#!/usr/bin/env -S uv run --script`, `chmod +x`, exit codes
`0/1/2/3/4` documented in `--help`, per
`skills/local/skill-author/references/script-design.md`.

## Repo registration (CLAUDE.md + `this-repo-conventions.md` checklist)

1. `docs/skills/python-project-best-practice.md` **and** `.zh-TW.md`.
2. Row in `docs/skills/index.md` (+ zh-TW sibling).
3. Nav entry in `mkdocs.yml`.
4. Row in the README "What's in here" table.
5. `skills/.claude-plugin/marketplace.json`: **new group `06-python-project`**
   with `./local/python-project-best-practice`. Slots `01`–`05` are taken;
   `06-` pins it above the unprefixed groups and leaves room for the deferred
   Marimo+Tyro / PyO3 / Streamlit skills. (Fallback if a new group is
   unwanted: `engineering-quality`.)
6. `./scripts/promote-todo.sh --title "Python + uv workflow skill" --summary "…"`.
7. Delete the two discovery symlinks `new-skill.sh` creates.

## Verification

Skill-level:

```bash
bash skills/local/skill-author/scripts/lint-skill.sh skills/local/python-project-best-practice
make lint-frontmatter && make marketplace && make kanban && make validate
```

End-to-end — the scaffold must produce a project that passes its own gate:

```bash
D=$(mktemp -d)
uv run skills/local/python-project-best-practice/scripts/new-python-project.py --help
uv run .../new-python-project.py --dry-run --profile cli "$D/demo"   # writes nothing
uv run .../new-python-project.py --profile cli "$D/demo"             # JSON on stdout
cd "$D/demo" && uv sync && just check                                # fmt+lint+types+test green
uv run demo --help && uv run demo completion zsh                     # verifiable-surfaces rungs
uv tool install "$D/demo" && demo --help && uv tool uninstall demo   # entry point really works
```

Also scaffold `--profile minimal` and `--profile ml` and confirm `just check`
passes for each. Audit script: run against the freshly scaffolded project
(expect all-pass) **and** against a synthetic legacy fixture
(`setup.py` + `requirements.txt`, no `src/`) to confirm it produces a non-empty
ordered `migration_plan[]` and a non-zero exit on `fail`-status checks.

Record which verification rung was reached, per `verifiable-surfaces`.

## Out of scope for this change

No edits to existing skills. Two inconsistencies are noted but **not** fixed
here — raise as separate TODO items if wanted:

- `fastapi-ai-scaffold` generates `uv venv` + `uv pip install -e ".[dev]"`,
  which this skill's defaults supersede (`uv sync` + dependency groups).
- `mkdocs-site-bootstrap` writes `[project.optional-dependencies] docs`, an
  extra rather than a group. `references/uv-and-pyproject.md` will document the
  interop (`uv sync --extra docs` keeps working) rather than force a migration.
