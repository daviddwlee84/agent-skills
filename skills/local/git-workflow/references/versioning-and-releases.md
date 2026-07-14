# Versioning & releases

Read this when cutting a release, tagging a version, or wiring a Python package
so its version comes from the git tag. Covers [SemVer](https://semver.org/),
annotated tags, and tag-driven Python versioning.

## Table of contents

1. [SemVer in one paragraph](#semver-in-one-paragraph)
2. [Mapping commits to bumps](#mapping-commits-to-bumps)
3. [Tagging a release](#tagging-a-release)
4. [When to tag](#when-to-tag)
5. [Python: git tag as single source of truth](#python-git-tag-as-single-source-of-truth)
6. [Changelog](#changelog)

---

## SemVer in one paragraph

`MAJOR.MINOR.PATCH`. Bump **MAJOR** for incompatible API changes, **MINOR** for
backward-compatible features, **PATCH** for backward-compatible fixes.
Pre-release and build metadata append as `-rc.1` / `+build.5`
(e.g. `2.0.0-rc.1`). Below `1.0.0` anything may change; `1.0.0` is the
commitment to a stable public API.

## Mapping commits to bumps

If commits follow [Conventional Commits](conventional-commits.md), the bump is
mechanical:

- `fix:` / `perf:` → PATCH
- `feat:` → MINOR
- `!` or `BREAKING CHANGE:` → MAJOR

Tools like [`commitizen`](https://commitizen-tools.github.io/commitizen/) or
`semantic-release` can compute the next version and changelog from the log.

## Tagging a release

Use an **annotated**, `v`-prefixed tag on the release commit:

```bash
git tag -a v1.4.0 -m "release: v1.4.0"
git push origin v1.4.0
# or push commits + their tags together:
git commit ... && git push --follow-tags
```

- **Annotated** (`-a`) tags store tagger, date, and message and are the right
  choice for releases (lightweight tags are just a moving label).
- Create the tag **on the commit that is the release** — don't tag ahead of it.
  Fixing a mis-placed tag means `git tag -f` + a force-push of the tag, which
  is disruptive if others already fetched it.
- List/inspect: `git tag --list 'v1.*'`, `git show v1.4.0`.

## When to tag

- **Applications/services**: at each deploy boundary worth returning to, or per
  release train (`v2025.07.0`-style calendar versions are also fine if that's
  your convention).
- **Libraries/packages**: at every published version — the tag *is* the release
  users depend on.
- Tag from `main` (Tier 3) or the promoted release commit (Tier 2). Don't tag
  arbitrary WIP commits.

## Python: git tag as single source of truth

When the whole repo **is** a Python package, don't hand-maintain a version
string in `__init__.py` *and* `pyproject.toml` *and* a git tag — derive it from
the tag. See the [Python Packaging guide on single-sourcing the version](https://packaging.python.org/en/latest/discussions/single-source-version/).

**setuptools backend** — [setuptools-scm](https://setuptools-scm.readthedocs.io/):

```toml
[build-system]
requires = ["setuptools>=64", "setuptools-scm>=8"]
build-backend = "setuptools.build_meta"

[project]
name = "yourpkg"
dynamic = ["version"]

[tool.setuptools_scm]
# version comes from the latest git tag; a dev suffix is added between tags
```

**Hatch backend** — [hatch-vcs](https://pypi.org/project/hatch-vcs/):

```toml
[build-system]
requires = ["hatchling", "hatch-vcs"]
build-backend = "hatchling.build"

[project]
name = "yourpkg"
dynamic = ["version"]

[tool.hatch.version]
source = "vcs"
```

Notes:
- Tags must be **PEP 440-compatible** once parsed. `vX.Y.Z` works (the `v` is
  stripped); avoid tags that don't map to PEP 440.
- Version is resolved at **build/install time**. Editable/dev installs can show
  a stale value until rebuilt — expected behavior, not a bug.
- In CI, cut the release by pushing the tag; the build then stamps the matching
  version. Verify the tag produces the expected version in CI before publishing.

## Changelog

Keep a human-readable `CHANGELOG.md` (the
[Keep a Changelog](https://keepachangelog.com/) format is a good default), or
generate it from Conventional Commits with `commitizen`/`semantic-release`.
Either way, the changelog entry and the tag should agree on the version.
