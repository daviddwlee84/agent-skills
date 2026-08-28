# uv and pyproject.toml

Load this when writing or repairing `pyproject.toml`, deciding what goes in a
lockfile, choosing a build backend, pinning the interpreter, or publishing.

uv's CLI surface changes between minor versions. When you are unsure of a flag,
fetch <https://docs.astral.sh/uv/reference/cli/> rather than guessing.

## The commands that matter

| Goal | Command |
|---|---|
| Start a project | `uv init --package --lib` (or `--app`) |
| Add a runtime dependency | `uv add httpx` |
| Add dev tooling | `uv add --dev pytest ruff` |
| Add to a named group | `uv add --group docs mkdocs-material` |
| Add a published extra | `uv add --optional postgres asyncpg` |
| Recreate the env from the lock | `uv sync` |
| Fail instead of re-resolving | `uv sync --locked` (use this in CI) |
| Check the lock is current | `uv lock --check` |
| Pin the interpreter | `uv python pin 3.13` |
| Run anything | `uv run <cmd>` |
| Bump the version | `uv version --bump minor` |
| Build + publish | `uv build && uv publish` |

`uv run` re-syncs before running. In a hot loop where you know the environment
is current, `uv run --no-sync` skips it.

## Groups vs extras

This is the distinction people get wrong, and getting it wrong ships your test
runner to your users.

```toml
[project.optional-dependencies]   # PUBLISHED. `pip install yourpkg[postgres]`
postgres = ["asyncpg>=0.30"]

[dependency-groups]               # LOCAL ONLY. PEP 735. Never published.
dev = ["pytest>=8.3", "ruff>=0.9"]
docs = ["mkdocs-material>=9.5"]
```

`dev` is special-cased: `uv sync` and `uv run` include it by default. Other
groups need `--group docs`. `--no-default-groups` gives a runtime-only env.

A dev tool in `optional-dependencies` is a real defect: it appears in your
package metadata, resolves into your users' dependency graph if they ever
install the extra, and cannot be removed without a release.

> Interop note: some tooling still generates a `docs` **extra** — for example
> the `mkdocs-site-bootstrap` skill writes `[project.optional-dependencies]
> docs`. That keeps working (`uv sync --extra docs`); it is not worth a
> migration unless you are publishing the package.

## Lockfile policy

Commit `uv.lock`. For applications and CLIs this is obvious. For libraries it
is also right, and the usual objection is based on a misunderstanding:

**`uv.lock` never constrains your users.** When someone installs your package
as a dependency, their resolver reads `[project.dependencies]` and ignores your
lock entirely. The lock pins *your* development and CI environment, which is
exactly what you want reproducible.

What the lock does not do is prove your declared ranges are honest. If you
support `>=3.11` and a floor of `httpx>=0.28`, add a CI job that resolves
against the lowest versions (`uv sync --resolution lowest-direct`), otherwise
your floors are aspirational.

## Interpreter pinning

`.python-version` holds the development interpreter. `uv python pin 3.13`
writes it, and `uv sync` downloads that interpreter if it is missing — no
system Python of that version required.

`requires-python` in `[project]` is a different thing: the *range you support*.
Keep the floor lower than the pin, and put both ends in the CI matrix. The two
drift apart silently otherwise.

`.python-version` is also read by pyenv. On a machine with both, a stale value
changes which interpreter builds the venv, with no warning.

## Build backends

| Backend | When |
|---|---|
| `hatchling` | default. Plugin ecosystem (`hatch-vcs` for git-tag versions) |
| `uv_build` | lean, fast, no plugins. Fine for a pure-Python package |
| `maturin` | any Rust/PyO3 extension |
| `scikit-build-core` | C/C++/CMake extensions |

With a src layout and a hyphenated project name, name the package directory
explicitly so the backend does not have to guess:

```toml
[tool.hatch.build.targets.wheel]
packages = ["src/my_tool"]
```

## Distribution

Tier 0, and enough for most internal tools — no PyPI account needed:

```bash
uv tool install git+https://github.com/owner/repo@v0.1.0
uvx --from git+https://github.com/owner/repo my-tool --help   # run once
```

Both require `[project.scripts]`. A package that can only be run as
`python -m pkg` gives the installer no command on `PATH`.

For PyPI, use Trusted Publishing (OIDC): configure the publisher on PyPI for
`owner/repo` + workflow filename, then give the job `id-token: write`. No API
token in Actions secrets, nothing to rotate or leak.

```yaml
permissions:
  id-token: write
steps:
  - run: uv build
  - run: uv publish        # picks up the OIDC token automatically
```

## Workspaces

For a monorepo of related packages, one lockfile and one venv for all of them:

```toml
[tool.uv.workspace]
members = ["packages/*"]

[tool.uv.sources]
my-core = { workspace = true }
```

Members share the resolution, so a version conflict between two members is a
hard error rather than two silently different environments. If the packages
genuinely need different dependency versions, they are not a workspace.
