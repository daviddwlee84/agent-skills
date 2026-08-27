# git-workflow

One opinionated, scale-aware git workflow that stays consistent from a solo
weekend repo to a multi-person, multi-month project — so commit messages,
branch names, merge strategy, and release tags stop being improvised per
project. Commits are **English and follow Conventional Commits**, even when the
prompt is in another language.

| Surface | Question it answers |
|---|---|
| `references/project-tiers.md` | "Do I commit to `main`, use a `dev` branch, or open PRs?" |
| `references/conventional-commits.md` | "What goes in the commit message, including AI provenance?" |
| `references/worktrees-parallel-agents.md` | "How do I run parallel agents without collisions?" |
| `references/versioning-and-releases.md` | "When and how do I tag a version?" |
| `references/branch-hygiene.md` | "Which local branches are done vs still in-dev?" |
| `scripts/branch-status.sh` | The same, as data — classify every local branch. |
| `scripts/check-commit-msg.sh` | "Is this commit message valid?" |
| `references/lazygit-cheatsheet.md` | "How do I do this in lazygit?" (learning aid) |

If you want the *why* behind the defaults — the concepts, not the skill
mechanics — read the companion explainer:
[Git workflow best practices](../reference/git-workflow.md).

## When the skill triggers

- "Commit this" / "幫我 commit" / "整理一下 git" / "write a commit message".
- "Should I branch or just commit to main?" / "should I open a PR?".
- "Set up worktrees for parallel agents" / "carry my `.env` into the worktree".
- "How do I tag / release a version?" / "bump the version".
- "My local branches are a mess — which ones are done?" / "clean up branches".
- Starting a new repo and wanting one consistent commit/branch/release
  convention for you and your agents.

## The three tiers

Match ceremony to real collaboration needs; promote only when the signal
appears.

| Tier | Shape | Branching | Integration |
|---|---|---|---|
| **1 — Solo / early** | one `main` | commit to `main`; short local branches optional | `pull --rebase`, `merge --ff-only` |
| **2 — prod/dev split** | `main` = released, `dev` = integration | feature branches off `dev` | merge to `dev`; ff `dev`→`main` at release |
| **3 — Team / grown vibe-coding** | `main` always deployable | short `feat/…` → PR | PR review/CI → squash-merge |

A solo vibe-coding project can jump straight to Tier 3: the PR becomes the
"ship a feature" boundary and a place for CI to run, even with one human.

## Defaults at a glance

- **Commits**: English `type(scope): subject`; non-trivial agent commits add a
  why/outcome body plus `AI-Assisted-By`, `Agent-Transcript`, and conditional
  `Agent-Plan` trailers. `feat!`/`BREAKING CHANGE:` drives a major bump.
- **History**: linear — `pull.rebase=true`, `merge.ff=only`; squash-merge noisy
  vibe-coding PRs, rebase-merge curated ones.
- **Branches**: `feat/ fix/ chore/ docs/ refactor/ exp/` for human intent,
  `agent/…` for agent/vibe work, `worktree-*` for Claude worktrees.
- **Worktrees**: `claude --worktree <name>`; `.worktreeinclude` (gitignored
  files only) to carry `.env` in; gitignore `.claude/worktrees/`.
- **Releases**: SemVer, annotated `v`-prefixed tags; for a Python package let
  the git tag drive the version (setuptools-scm / hatch-vcs).
- **Forge CLIs**: `gh` (GitHub) / `glab` (GitLab) for PRs from the terminal —
  recommended, never hard-required.

## Structure

```
skills/local/git-workflow/
├── SKILL.md
├── scripts/
│   ├── branch-status.sh        # classify branches: active/merged/gone/stale
│   └── check-commit-msg.sh     # validate header + optional agentic contract
├── tests/
│   └── test_check_commit_msg.sh
├── references/
│   ├── project-tiers.md        # main vs dev vs PR + GitHub Flow
│   ├── conventional-commits.md # the commit message spec, condensed
│   ├── worktrees-parallel-agents.md
│   ├── versioning-and-releases.md
│   ├── branch-hygiene.md
│   └── lazygit-cheatsheet.md   # learning aid
└── assets/
    ├── commit-template.txt      # git config commit.template
    └── worktreeinclude.template # example .worktreeinclude
```

## Relationship to secret hygiene

This skill **defers** all secret scanning and agent-transcript handling to
[`agent-history-hygiene`](agent-history-hygiene.md). At commit/merge time it
calls that skill's `scan-staged.sh` (exit `0` clean / `10` redacted / `20`
leaks) and points at its rotate-first remediation runbook rather than
reimplementing any of it. When a project doesn't check agent transcripts in,
drop them before a squash-merge; when it does, stage them with that skill.

## Cross-harness agentic commits

Keep the human as Git author/committer and use one portable final trailer block:

```text
feat(scope): add concise imperative summary

Explain why the change was needed, its outcome, and meaningful validation.

AI-Assisted-By: Codex CLI (gpt-5.6-sol)
Agent-Transcript: .specstory/history/session.md
Agent-Plan: .claude/plans/plan.md
```

Native Claude/Cursor attribution or signing remains additive. The companion
`agent-history-hygiene/scripts/agent-commit-metadata.sh` derives this block from
staged artifacts; `check-commit-msg.sh --agentic --staged` validates the full
message. Signing is separate and opt-in—this skill never changes Git or harness
configuration unless the user explicitly asks.

The dated behavior matrix and the distinction between co-author trailers,
Cursor line tracking/cloud signatures, and Codex's currently undocumented
attribution setting are in
[Git workflow best practices](../reference/git-workflow.md#agentic-commit-provenance).

## Gotchas

- `merge.ff only` refuses a diverged pull on purpose — resolve with
  `git pull --rebase`.
- A squash-merged branch never shows under `git branch --merged`; it shows as
  `gone` upstream. `branch-status.sh` classifies this correctly (delete with
  `-D`, after confirming no unpushed work).
- Tracked files in `.worktreeinclude` do nothing — it copies **only gitignored**
  matches; a committed `.vscode/settings.json` is already in the worktree.
- The English-commit rule holds under Chinese prompts — translate the intent,
  don't mirror the prompt language into the log.
- Commit templates do not affect `git commit -m`, which agent harnesses commonly
  use; validate with `check-commit-msg.sh --agentic` instead.
- Squash/amend creates a new commit object, so copy canonical trailers into the
  squash message and do not amend a vendor-signed commit solely for metadata.

## See also

- [Source](https://github.com/daviddwlee84/agent-skills/tree/main/skills/local/git-workflow)
- [Git workflow best practices](../reference/git-workflow.md) — the concepts
  explainer (Conventional Commits, SemVer, GitHub Flow, worktrees).
- [`agent-history-hygiene`](agent-history-hygiene.md) — secret + transcript
  hygiene this skill defers to at commit/merge time.
