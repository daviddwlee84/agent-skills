# Conventional Commits

Read this when writing a non-trivial commit message, wiring
`scripts/check-commit-msg.sh`, or deciding how a change should bump the
version. This condenses the [Conventional Commits v1.0.0](https://www.conventionalcommits.org/en/v1.0.0/)
spec and the house rules for this workflow.

## Table of contents

1. [Format](#format)
2. [Types](#types)
3. [Scope](#scope)
4. [Subject line rules](#subject-line-rules)
5. [Body and footers](#body-and-footers)
6. [Breaking changes](#breaking-changes)
7. [SemVer mapping](#semver-mapping)
8. [Examples](#examples)
9. [The English rule](#the-english-rule)
10. [Tooling](#tooling)

---

## Format

```
<type>[(scope)][!]: <subject>

[body]

[footer(s)]
```

Only the first line (`<type>: <subject>`) is mandatory. A blank line separates
header, body, and footers.

## Types

| Type | Use for | SemVer |
|---|---|---|
| `feat` | a new user-facing feature | MINOR |
| `fix` | a bug fix | PATCH |
| `docs` | documentation only | — |
| `style` | formatting/whitespace, no code-behavior change | — |
| `refactor` | code change that neither fixes a bug nor adds a feature | — |
| `perf` | a performance improvement | PATCH |
| `test` | adding or fixing tests | — |
| `build` | build system, dependencies, packaging | — |
| `ci` | CI configuration and scripts | — |
| `chore` | maintenance that doesn't touch src/test (e.g. `.gitignore`) | — |
| `revert` | reverts a previous commit | — |

Keep to this set; consistency is the point. `perf` bumps PATCH because it
changes runtime behavior; `refactor` does not.

## Scope

Optional noun in parentheses naming the area touched: `feat(auth):`,
`fix(parser):`, `docs(readme):`. Use a short, stable vocabulary per repo
(module names, subsystems). Omit it when a change is broad or the repo is small.

## Subject line rules

- **Imperative mood**: "add", "fix", "remove" — as if completing *"This commit
  will …"*. Not "added"/"adds"/"adding".
- **Lowercase** first word; **no trailing period**.
- Keep the whole header **≤ ~72 characters** (50 is a good aim).
- Describe *what/why*, not *how*: `fix(client): retry on 429` beats
  `fix: change the loop`.

## Body and footers

- **Body** (optional): the *why* and any context that won't be obvious from the
  diff. Wrap at ~72 columns. Bullet lists are fine.
- **Footers** (optional), one per line, `Key: value`:
  - `Refs: #123` / `Closes: #123` — issue linkage.
  - `Co-Authored-By: Name <email>` — attribution.
  - `BREAKING CHANGE: <description>` — see below.

## Breaking changes

Two equivalent ways to mark an incompatible change (→ **MAJOR** bump):

```
feat(api)!: drop v1 auth endpoints

BREAKING CHANGE: /v1/auth is removed; migrate to /v2/token.
```

The `!` after the type/scope is the quick signal; the `BREAKING CHANGE:`
footer carries the migration note. Either alone is valid; use both for clarity.

## SemVer mapping

The commit log becomes a changelog and a version driver (see
[`versioning-and-releases.md`](versioning-and-releases.md)):

- `fix:` / `perf:` → **PATCH** (`1.2.3 → 1.2.4`)
- `feat:` → **MINOR** (`1.2.3 → 1.3.0`)
- any `!` / `BREAKING CHANGE:` → **MAJOR** (`1.2.3 → 2.0.0`)
- `docs`/`style`/`test`/`chore`/`ci`/`build`/`refactor` → no release on their own

## Examples

```
feat(worktree): copy gitignored env files via .worktreeinclude
fix(branch-status): treat squash-merged branches as gone, not active
docs(readme): add install one-liner
refactor(cli)!: rename --out to --output

BREAKING CHANGE: the --out flag is removed; use --output.
revert: feat(auth): add token refresh

This reverts commit 9fceb02.
```

## The English rule

Commit messages, branch names, and tags are **English**, even when the prompt
or conversation is Chinese. Rationale: history is consumed by changelog/SemVer
tooling and future collaborators, and a mixed-language log is hard to grep and
automate. Translate the *intent* — don't transliterate the prompt. (Your PR
description or issue comments can be bilingual; the git object graph stays EN.)

## Tooling

- **This skill**: `scripts/check-commit-msg.sh` validates the header shape
  (type + optional scope/`!` + subject) with agent-friendly exit codes.
- **Escape hatch — enforce in-repo**: [`commitlint`](https://commitlint.js.org/)
  via a `commit-msg` hook, or [`commitizen`](https://commitizen-tools.github.io/commitizen/)
  for guided prompts + automated version bumps. Adopt these when a team needs
  hard enforcement; for solo work the template + validator are enough.
- **Template**: `assets/commit-template.txt` →
  `git config commit.template skills/local/git-workflow/assets/commit-template.txt`.
