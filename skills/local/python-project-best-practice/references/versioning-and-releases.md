# Versioning and releases

## Single source

Default to static `[project].version` in `pyproject.toml` (initially `0.1.0`).
Runtime `__version__` reads `importlib.metadata.version(distribution_name)`;
CLI and API surfaces reuse it. The fallback `0.0.0+unknown` means the package
is not installed and must never pass release verification. Run `uv sync`
after version changes; installed metadata can otherwise be stale.

A source constant plus Hatch dynamic version extraction is valid for projects
that need a version before installation. Keep that existing scheme when it
works, but do not also maintain a static project version. VCS-derived versions
are an alternative for established tag-driven release pipelines; account for
shallow clones and source archives. Do not combine competing version sources.

## Compatibility contract

Document the public surface: Python API, CLI flags/output, configuration keys,
and persisted formats consumers rely on. Classify changes against that surface.

| Stage | Incompatible change | Compatible feature | Compatible fix |
|---|---|---|---|
| `0.y.z`, y >= 1 | minor, reset patch | patch | patch |
| `1.0.0` onward | major, reset minor/patch | minor, reset patch | patch |

The pre-1.0 row is this scaffold's explicit convention, not a guarantee made
by SemVer itself. `0.1.0` is an initial release, not a stable API promise.
Move to `1.0.0` when the public API and compatibility commitment are ready.
Use Python-compatible prerelease spelling such as `1.0.0rc1`.

## Change and release workflow

1. Record user-visible changes under `CHANGELOG.md` → `Unreleased` in the
   change's commit, including migration steps for breaking changes. Docs,
   tests, and internal refactors alone need no version bump; record them only
   when useful to consumers.
2. At a release boundary, choose the bump from all accumulated changes.
   Update the static version (for example `uv version --bump patch`), refresh
   `uv.lock` with `uv lock`, and move released notes under `X.Y.Z - YYYY-MM-DD`.
   Leave a fresh `Unreleased` section. The initial release may retain `0.1.0`.
3. Run `uv sync`, `just check`, and `uv build`. Install the built wheel in a
   fresh environment outside the source tree. Assert its distribution metadata
   and imported `__version__` both equal the intended version; check any exposed
   CLI/API version too. For Rust profiles, Cargo's crate version is separate
   metadata: explicitly document whether it is independent or synchronized.
4. Commit the version, lockfile, and changelog together. After the release
   commit lands on the release branch, tag that exact commit `vX.Y.Z` and
   publish the verified artifact through the project's release workflow.
   Never move a published tag or replace an already published version.

A normal feature commit does not automatically constitute a release. Tag only
release commits; recording a changelog entry does not authorize publishing.
Persisted data formats may need a separate `format_version` and migration
policy: a package version alone does not establish storage compatibility.

## Downstream consumption

An application consuming a package with the documented pre-1.0 contract may
use `example>=0.1,<0.2` and commit its lockfile for reproducibility. This is a
compatibility range, not an exact pin. An exact `==0.1.2` or git commit pins
one revision; a release tag is a readable selection under an immutable-tag
policy. Review migration notes before widening the range.

Reusable libraries should retain broad dependency floors by default (see
`uv-and-pyproject.md`); justify an upper bound with the dependency's explicit
compatibility contract or a known incompatibility, rather than applying caps
to every dependency automatically.

Sources: [PyPA single-sourcing](https://packaging.python.org/en/latest/discussions/single-source-version/),
[SemVer](https://semver.org/).
