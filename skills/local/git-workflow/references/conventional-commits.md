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
6. [Agentic provenance](#agentic-provenance)
7. [Breaking changes](#breaking-changes)
8. [SemVer mapping](#semver-mapping)
9. [Examples](#examples)
10. [The English rule](#the-english-rule)
11. [Tooling](#tooling)

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
  diff. Wrap at ~72 columns. Bullet lists are fine. For non-trivial commits
  produced with an agent harness, the body is required; include the outcome and
  meaningful validation, not a line-by-line diff recital.
- **Footers** (optional), one per line, `Key: value`:
  - `Refs: #123` / `Closes: #123` — issue linkage.
  - `Co-Authored-By: Name <email>` — native/human co-author attribution.
  - `BREAKING CHANGE: <description>` — see below.

## Agentic provenance

Keep the human as Git author/committer and add a portable final trailer block:

```text
AI-Assisted-By: Claude Code (Claude Fable 5)
Agent-Transcript: .specstory/history/2026-08-27_session.md
Agent-Plan: .claude/plans/session.md
```

- `AI-Assisted-By` always names both harness and model. Repeat it for distinct
  contributors; never use `unknown` or manufacture an AI email address.
- Artifact paths are repo-relative and must name files in the same commit.
- Native metadata such as Claude Code's `Co-Authored-By` is preserved. Put any
  Generated-with prose before the trailer block, and keep the canonical fields
  in the final block so `git interpret-trailers --parse` sees them.
- Message attribution and SSH/GPG signing are independent. A signature proves
  control of a key over the exact commit object; amending or squash-merging
  creates a different object and discards the original signature.

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

feat(agent-history): emit staged provenance trailers

Derive harness, model, transcript, and plan metadata from the staged snapshot
so different coding-agent harnesses produce the same reviewable history.

AI-Assisted-By: Codex CLI (gpt-5.6-sol)
Agent-Transcript: .specstory/history/session.md
```

## The English rule

Commit messages, branch names, and tags are **English**, even when the prompt
or conversation is Chinese. Rationale: history is consumed by changelog/SemVer
tooling and future collaborators, and a mixed-language log is hard to grep and
automate. Translate the *intent* — don't transliterate the prompt. (Your PR
description or issue comments can be bilingual; the git object graph stays EN.)

## Tooling

- **This skill**: `scripts/check-commit-msg.sh` keeps its header-only default;
  `--agentic --staged` validates the English description, canonical trailers,
  and artifact paths with agent-friendly exit codes.
- **Companion**: `agent-history-hygiene/scripts/agent-commit-metadata.sh`
  derives the canonical trailer block from staged artifacts.
- **Escape hatch — enforce in-repo**: [`commitlint`](https://commitlint.js.org/)
  via a `commit-msg` hook, or [`commitizen`](https://commitizen-tools.github.io/commitizen/)
  for guided prompts + automated version bumps. Adopt these when a team needs
  hard enforcement; for solo work the template + validator are enough.
- **Template**: `assets/commit-template.txt` →
  `git config commit.template skills/local/git-workflow/assets/commit-template.txt`.
