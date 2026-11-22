# Quality gates: ruff, types, pytest, CI

Load this when configuring lint/format/type/test tooling, setting up CI, or
deciding what `just check` should contain.

## One gate, four rungs

`just check` = `fmt-check` → `lint-check` → `types` → `test` → `docs-check`,
ordered so the cheapest failure comes first. CI runs the same commands. If a
check exists only in CI, contributors discover it after pushing; if it exists
only locally, it stops being true.

## ruff does lint AND format

```toml
[tool.ruff]
line-length = 100
target-version = "py311"
src = ["src", "tests"]

[tool.ruff.lint]
select = ["E", "W", "F", "I", "UP", "B", "SIM", "C4", "RUF"]
```

- `I` replaces isort, `UP` modernizes syntax to your `target-version`, `B`
  catches real bugs (mutable defaults, loop-variable capture), `SIM` and `C4`
  simplify, `RUF` is ruff's own set.
- **Do not also install black.** `ruff format` is a reimplementation of black's
  algorithm; running both means two tools rewriting the same file, disagreeing
  over magic trailing commas and string quoting. Pick ruff.
- `target-version` should equal your `requires-python` floor, not your
  development pin. `UP` rewrites to the *lowest* version you claim to support.
- **Scope the formatter past the coding-agent directories, and set
  `force-exclude`.** Agent transcripts and plans are records, not source; since
  ruff 0.16 `ruff format` also formats Python inside Markdown code blocks, so it
  rewrites them — falsifying the record and churning forever against the agent
  rewriting the same file. `.agents/` and `.claude/` additionally hold skills
  installed by `npx skills`: vendored code that no rule set keeps format-clean.

  ```toml
  [tool.ruff]
  extend-exclude = [".agents", ".claude", ".codex", ".cursor",
                    ".opencode", ".specify", ".specstory"]
  force-exclude = true
  ```

  `force-exclude = true` is the load-bearing half. Ruff ignores `exclude` /
  `extend-exclude` for paths passed **explicitly on the command line**, and
  passing every changed file explicitly is exactly what pre-commit does — so
  `extend-exclude` alone protects `ruff format .` and silently does nothing
  under the `ruff-pre-commit` hook. Verify rather than assume:

  ```console
  $ ruff format --check .agents/skills/<any>/scripts/x.py
  warning: No Python files found under the given path(s)   # correct
  1 file would be reformatted                              # exclude not in effect
  ```

  List `.claude` even when `.agents` is present: `.claude/skills/<name>`
  symlinks into `.agents`, so an `.agents`-only exclude still reaches the same
  bytes by the other path. `audit-python-project.py` checks this
  (`artifact-dirs-excluded`).

Per-file ignores earn their keep in exactly two places:

```toml
[tool.ruff.lint.per-file-ignores]
"notebooks/*" = ["E402", "F401", "B018"]   # marimo cells are not linear scripts
"tests/*" = ["S101"]                        # only if you enable flake8-bandit
```

## Type checking

Two defensible defaults:

| | `ty` | `mypy` |
|---|---|---|
| Speed | very fast (Rust, incremental) | slow on large trees |
| Maturity | **0.0.x, pre-1.0** — diagnostics change between patch releases | stable, a decade of edge cases |
| Editor | ships a language server | via pylsp/pyright |

The template defaults to `ty` and pins it, because a type checker that reruns
in under a second is one people actually run. Pin it *exactly* — `ty==0.0.74`,
not `>=` — or a routine `uv lock --upgrade` will change what your gate accepts.

Switch to mypy by replacing the dev dependency and the `just types` recipe:

```toml
[tool.mypy]
strict = true
files = ["src", "tests"]
```

Whichever you pick: ship `py.typed` in the package. Without that marker, a
consumer's type checker ignores every annotation you wrote.

Compiled extensions are invisible to both. A PyO3 module needs a hand-written
`.pyi` next to it or the checker reports `has no member`; see
[`rust-pyo3.md`](rust-pyo3.md).

## pytest layout

```
src/my_tool/core.py
tests/test_core.py        # mirrors src/, module for module
```

Tests live outside `src/`. With a src layout, `uv run pytest` imports the
*installed* package, so a missing `__init__.py`, a missing `py.typed`, or
un-shipped package data fails in your test run instead of in a user's install.
A flat layout imports the working directory and hides all three.

```toml
[tool.pytest.ini_options]
addopts = "-q --strict-markers --strict-config"
testpaths = ["tests"]
```

Keep coverage out of `addopts`. Always-on coverage slows every run, breaks
debugger attach, and trains people to ignore the number. Put it in one recipe
and in CI:

```bash
uv run pytest --cov --cov-report=term-missing --cov-fail-under=80
```

## TDD, and why it is the loop that works with agents

Write the failing test first, then the code that passes it. With an agent in
the loop this stops being a style preference: the test is the only part of the
exchange that is machine-checkable. "Make the tests pass" is a verifiable
instruction; "implement the feature" is not.

Practical shape:

1. Write the test. Run it. **Confirm it fails, and for the stated reason** — a
   test that passes before the implementation exists is testing nothing.
2. Implement the smallest change that passes it.
3. `just check`.
4. Refactor with the gate green.

For the discipline itself — how to pick the next test, when to stub, how to
avoid tests that encode the implementation — use the vendored
`engineering-fundamentals/tdd` skill. This section only covers the mechanics.

## CI

```yaml
- uses: actions/checkout@v5
- uses: astral-sh/setup-uv@v10
  with:
    enable-cache: true
    python-version: ${{ matrix.python-version }}
- run: uv sync --locked        # fails on a stale lock instead of re-resolving
- run: uv run ruff format --check .
- run: uv run ruff check .
- run: uv run ty check
- run: uv run pytest --cov --cov-fail-under=80
```

Notes worth the line each:

- `--locked`, not plain `uv sync`. Without it, CI silently resolves a different
  dependency set than your machine and the lockfile stops meaning anything.
- Matrix the `requires-python` floor and the `.python-version` pin. Testing
  only the pin means your declared floor is untested.
- Pin actions to a release tag, or a commit SHA if you want supply-chain
  hardening. `@master` is a remote-code-execution surface you do not control.
- Action majors move. Check the current one rather than copying an old
  workflow — `setup-uv` was on v6 not long ago.

## pre-commit

Useful for the fast rungs (format, lint, secret detection) so bad commits never
land. Do not duplicate the whole gate there — a pre-commit hook that runs the
test suite gets bypassed with `-n` within a week.

The `agent-history-hygiene` skill already bootstraps pre-commit with secret
scanning; add ruff hooks to that config rather than starting a second one. That
template already scopes its own in-place rewriters (`end-of-file-fixer`,
`trailing-whitespace`) past the agent directories; the ruff hooks you add need
`force-exclude = true` in `pyproject.toml` to get the same treatment.

Keep such excludes **per-hook**. A top-level `exclude:` applies to every hook in
the file, so it would also switch off the secret scanners on the artifact dirs —
precisely where leaked keys land.
