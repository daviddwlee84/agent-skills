---
name: git-workflow
description: Opinionated, scale-aware git workflow — English Conventional Commits, cross-harness AI provenance (`AI-Assisted-By` + transcript/plan trailers), linear history, main-vs-PR tiers, worktrees for parallel agents, SemVer releases, and pre-merge hygiene. Use when committing, writing commit bodies, recording Claude/Codex/Cursor attribution, signing commits, branching, merging, opening a PR, tagging a release, or cleaning stale branches — incl. "幫我 commit / 整理 git" and "git 工作流".
---

# git-workflow

One consistent, opinionated git workflow that scales from a solo weekend
project to a multi-person, multi-month repo — so you (and your agents) stop
improvising commit messages, branch names, and release habits per project.
The defaults here favor a **clean, linear, reviewable history**.

Surfaces, separated by the question they answer:

| Surface | Question it answers |
|---|---|
| `references/project-tiers.md` | "Do I commit to `main`, use a `dev` branch, or open PRs?" |
| `references/conventional-commits.md` | "What exactly goes in the commit message, including AI provenance?" |
| `references/worktrees-parallel-agents.md` | "How do I run parallel agents without collisions?" |
| `references/versioning-and-releases.md` | "When and how do I tag a version?" |
| `references/branch-hygiene.md` | "Which local branches are done vs still in-dev?" |
| `scripts/branch-status.sh` | Same, as data — classify every local branch. |
| `scripts/check-commit-msg.sh` | "Is this commit message valid?" |
| `references/lazygit-cheatsheet.md` | "How do I do this in lazygit?" (learning aid) |

## Core principles

1. **Commit messages are English and follow Conventional Commits**, even when
   the prompt/conversation is in Chinese. Code history is read by tooling
   (changelogs, SemVer bumps) and future collaborators; a mixed-language log
   is harder to grep and automate. Prompts stay whatever language you like.
2. **Prefer a linear history.** Default to `pull --rebase` and fast-forward
   merges; reserve merge commits and squashes for PR integration points. A
   linear log makes `git bisect`, `git revert`, and blame legible.
3. **One logical change = one commit; one workflow phase = one commit.** For
   multi-phase / `/workflows` work, commit at each phase boundary so you can
   roll back or resume cleanly if interrupted. Don't batch unrelated changes.
4. **Never leak secrets into history.** Secret scanning + agent-transcript
   handling is owned by the [`agent-history-hygiene`](../agent-history-hygiene/SKILL.md)
   skill — this skill *defers* to it at commit/merge time rather than
   reimplementing it.
5. **Keep authorship, AI provenance, and cryptographic signing separate.** The
   human remains Git author/committer; agent harness + model live in canonical
   trailers; SSH/GPG signing proves key possession, not who wrote each line.

## Pick your tier first

Match the workflow to the project's real collaboration needs, not its
ambitions. Promote a tier only when the **signal** actually appears.

| Tier | Shape | Branching | Integration | Promote when… |
|---|---|---|---|---|
| **1 — Solo / early** | one `main` | commit to `main`; short-lived local branches optional | `pull --rebase`, `merge --ff-only` | you need a stable line separate from WIP |
| **2 — prod/dev split** | `main` = released, `dev` = integration | feature branches off `dev` | merge to `dev`; fast-forward `dev`→`main` at release | others rely on a deployed/tagged version |
| **3 — Team / grown vibe-coding** | `main` always deployable | short-lived `feat/…` etc. → PR | PR review/CI → squash-merge | ≥2 contributors, or you want a per-feature ship+review gate |

A **solo vibe-coding** project can jump straight to Tier 3 even with one human:
the PR becomes the "ship a feature" boundary that separates finished work from
in-progress work, and gives CI a place to run. See
`references/project-tiers.md` for per-tier command recipes and the GitHub-Flow
summary. Read it when deciding whether to branch/PR or when a project outgrows
committing straight to `main`.

## Commit messages

Format (full spec + type table in `references/conventional-commits.md` — read
it when writing a non-obvious commit or wiring `check-commit-msg.sh`):

```
<type>(<optional scope>): <subject>

<body — the "why" for non-trivial agent commits, wrapped ~72 cols>

<optional standard/native footers>
<canonical agent trailers — AI-Assisted-By / Agent-Transcript / Agent-Plan>
```

- **Types**: `feat`, `fix`, `docs`, `style`, `refactor`, `perf`, `test`,
  `build`, `ci`, `chore`, `revert`.
- **Subject**: imperative mood, lowercase start, no trailing period, keep the
  header ≤ ~72 chars. "add retry to client", not "Added retry." / "Adds…".
- **Breaking change**: `feat!:` / `refactor(api)!:` or a `BREAKING CHANGE:`
  footer → drives a **major** SemVer bump.
- Validate before committing when unsure:

```bash
printf 'feat(auth): add token refresh\n' | \
  bash skills/local/git-workflow/scripts/check-commit-msg.sh
```

- Install the message template so the shape is always in front of you:

```bash
git config commit.template skills/local/git-workflow/assets/commit-template.txt
```

### Agentic commit contract

Use this portable minimum for commits produced with Claude Code, Codex,
Cursor, OpenCode, or another coding-agent harness:

```text
feat(scope): add concise imperative summary

Explain why the change was needed, the resulting behavior, and meaningful
validation. Keep this in English even when the prompt was not English.

AI-Assisted-By: Codex CLI (gpt-5.6-sol)
Agent-Transcript: .specstory/history/session.md
Agent-Plan: .claude/plans/plan.md
```

- A non-trivial agent commit requires a body. Use the validator's
  `--allow-no-body` only for a genuinely self-explanatory change such as a typo.
- Repeat `AI-Assisted-By` for every distinct harness/model that materially
  contributed. Never invent a vendor email merely to make GitHub show an AI as
  a co-author.
- Repeat transcript/plan trailers for every staged artifact, using repo-relative
  paths. Omit `Agent-Plan` when no plan file is in the commit.
- Preserve tool-native metadata (for example Claude's `Co-Authored-By`) as
  additive evidence. Put the canonical fields in the **final Git trailer
  block** so `git interpret-trailers --parse` can query them.
- When `agent-history-hygiene` is installed, generate the block from the staged
  snapshot instead of copying paths/model names by hand:

```bash
bash skills/local/agent-history-hygiene/scripts/agent-commit-metadata.sh
```

Validate the complete message before committing:

```bash
bash skills/local/git-workflow/scripts/check-commit-msg.sh \
  --agentic --staged --file /path/to/commit-message.txt
```

Cryptographic signing is opt-in and user-owned. Configure SSH/GPG signing only
when the user explicitly asks; never silently change global Git or harness
settings. A vendor-signed cloud-agent commit must not be amended solely to add
metadata, because amending replaces the signed commit object.

## Branch naming

Use a `<prefix>/<kebab-desc>` namespace so branches sort and clean up by
intent, and so agent-generated branches are visually distinct from yours:

- **Human intent**: `feat/…`, `fix/…`, `chore/…`, `docs/…`, `refactor/…`,
  `exp/…` (throwaway experiments). Optionally embed an issue: `feat/123-oauth`.
- **Agent / vibe-coding**: `agent/<desc>` — a dedicated namespace you can bulk-
  triage or delete separately from hand-authored branches.
- **Claude worktrees**: `worktree-<name>` (auto-created by `claude --worktree`)
  is a third namespace — see below.

Keeping these separate is what makes `branch-status.sh` and
`git branch --list 'agent/*'` cleanup targeted rather than risky.

## Merge & sync

Set linear-history defaults (per-repo, or `--global` to your taste):

```bash
git config pull.rebase true      # rebase local work onto upstream on pull
git config merge.ff only         # refuse merges that can't fast-forward
```

- **Solo/local**: `git pull --rebase`, then `git merge --ff-only <branch>` to
  land a short-lived branch with no merge commit.
- **PRs (Tier 3)**: prefer **squash-merge** for vibe-coding branches (collapses
  noisy WIP into one clean `feat: …` commit on `main`); use **rebase-merge**
  when every commit is already meaningful and you want them preserved.
- Drive PRs from the terminal with the **forge CLI** — `gh` (GitHub) or `glab`
  (GitLab). These are strongly recommended (not required — the scripts here
  degrade to plain git if absent):

```bash
gh pr create --fill            # or: glab mr create --fill
gh pr checks                   # watch CI
gh pr merge --squash --delete-branch   # glab mr merge --squash --remove-source-branch
```

  The vendored `create-pull-request` skill (github-workflow group) is a
  companion for richer PR bodies.

## Worktrees for parallel agents

Run each parallel agent/session in its own git worktree so file edits never
collide. Full mechanics + caveats in `references/worktrees-parallel-agents.md`
— read it before setting up parallel agents or debugging a missing `.env` in
a worktree.

Essentials:

```bash
claude --worktree feature-auth   # → .claude/worktrees/worktree-feature-auth/
```

- Worktrees branch from `origin/HEAD` by default; set `worktree.baseRef: "head"`
  in settings to branch from your local HEAD (unpushed work).
- Subagents: add `isolation: worktree` frontmatter, or ask Claude to "use
  worktrees for your agents".
- **Gitignore `.claude/worktrees/`** so worktree contents don't show as
  untracked files in the main checkout.
- Bring **gitignored** files (e.g. `.env`) into new worktrees with a
  `.worktreeinclude` at the repo root (see `assets/worktreeinclude.template`).
  It uses `.gitignore` syntax and copies **only gitignored** matches — already-
  tracked files are in the checkout already, so don't list them.
- Bonus: because SpecStory tracks transcripts by *directory*, a worktree's
  fresh dir cleanly separates each parallel agent's chat history.

## Versioning & releases

Use **SemVer** (`MAJOR.MINOR.PATCH`) and let commit types imply the bump:
`fix:` → PATCH, `feat:` → MINOR, `!`/`BREAKING CHANGE:` → MAJOR. Tag releases
with an **annotated, `v`-prefixed** tag on the release commit:

```bash
git tag -a v1.4.0 -m "release: v1.4.0" && git push origin v1.4.0
```

When the whole project **is** a Python package, make the git tag the single
source of truth (setuptools-scm or hatch-vcs) instead of hand-editing a
version string. Details + config in `references/versioning-and-releases.md` —
read it when cutting a release or wiring package versioning.

## Before you merge / ship

1. **Phase commits**: ensure each phase of the work is its own commit (easy
   rollback / resume).
2. **Dev-env reproducibility (optional, recommended)**: commit
   `.vscode/settings.json` + `.vscode/extensions.json` so a fresh clone gets
   the same editor setup. (These are *tracked*, so they don't belong in
   `.worktreeinclude`.)
3. **Secret + agent-artifact hygiene** — defer to
   [`agent-history-hygiene`](../agent-history-hygiene/SKILL.md):

```bash
# clean = exit 0; redacted = 10; leaks = 20 → stop and remediate
bash skills/local/agent-history-hygiene/scripts/scan-staged.sh
```

   If the project **doesn't** check in agent transcripts/plans, drop them
   before a squash-merge; if it does, stage them with that skill's
   `stage-agent-artifacts.sh`. Either way, a leaked secret is remediated via
   its `references/remediation.md` (rotate first — never reflexive
   `git push --force`).
4. **Agentic squash metadata**: a squash merge creates a new commit, so copy the
   canonical `AI-Assisted-By` / artifact trailers into the squash message. The
   source commit's cryptographic signature cannot survive object replacement.
5. **Branch cleanup** after the PR merges:

```bash
git fetch --prune
bash skills/local/git-workflow/scripts/branch-status.sh   # find gone/merged/stale
```

## When to use this skill

- "Commit this" / "幫我 commit" / "整理一下 git" / "write a commit message".
- "Should I branch or just commit to main?" / "should I open a PR?".
- "Set up worktrees for parallel agents" / "carry my `.env` into the worktree".
- "How do I tag / release a version?" / "bump the version".
- "My local branches are a mess — which are done?" / "clean up branches".
- Starting a new repo and wanting a consistent commit/branch/release convention.

## When NOT to use

- **Secret leaked / scrubbing transcripts / committing chat history** — that's
  [`agent-history-hygiene`](../agent-history-hygiene/SKILL.md); come back here
  only for the surrounding commit/merge flow.
- **GitHub platform automation** (CI diagnosis, issue triage, rich PR bodies)
  — the vendored `github-workflow` group skills own that.
- A single trivial `git add` + `git commit` the agent already does correctly —
  no skill needed.

## Available scripts

- **`scripts/branch-status.sh [--json] [--stale-days N] [--help]`** — classify
  every local branch as `active` / `merged` / `gone` (upstream deleted, e.g.
  after a squash-merge) / `stale` (no commits in N days, default 30). TSV on
  stdout by default, `--json` for callers, prose on stderr. Always exits 0
  (state is data). Enriches `merged`/`gone` with `gh`/`glab` when available,
  falling back to pure git otherwise.
- **`scripts/check-commit-msg.sh [--file PATH] [--agentic] [--staged] [--allow-no-body] [--types]`**
  — default mode validates a Conventional Commits header. `--agentic` also
  requires an English body + canonical harness/model trailers; `--staged`
  cross-checks transcript/plan paths against the index. Exit **0** valid /
  **1** invalid / **2** bad args or repository context.

## Bundled assets

- `assets/commit-template.txt` — commit message skeleton for
  `git config commit.template`.
- `assets/worktreeinclude.template` — example `.worktreeinclude` (gitignored
  env files only; annotated so tracked files aren't added by mistake).

## Reference files

- `references/project-tiers.md` — read when deciding main-vs-dev-vs-PR or when
  a project outgrows its current tier. Per-tier recipes + GitHub-Flow summary.
- `references/conventional-commits.md` — read when writing a non-trivial commit
  or wiring the validator. Full type table, footers, examples.
- `references/worktrees-parallel-agents.md` — read before setting up parallel
  agents or debugging worktree file-copy / cleanup issues.
- `references/versioning-and-releases.md` — read when cutting a release or
  wiring Python tag-driven versioning (setuptools-scm / hatch-vcs).
- `references/branch-hygiene.md` — read when local branches are confusing
  (PR merged but branch lingers; work continued after merge).
- `references/lazygit-cheatsheet.md` — read when you'd rather drive git through
  lazygit; a learning aid, safe to ignore once the CLI is second nature.

## Gotchas

- **`merge.ff only` refuses a diverged pull.** If upstream moved and you have
  local commits, a plain `git pull`/`merge` errors instead of making a merge
  commit — that's intended. Resolve with `git pull --rebase` (or an explicit
  `git merge --no-ff` when you truly want the merge commit).
- **Squash-merge orphans the source branch.** After a squashed PR, the branch's
  commits never appear on `main`, so `git branch --merged` won't list it; it
  shows up as `gone` upstream (`git branch -vv`). `branch-status.sh` classifies
  this correctly — delete with `git branch -D`, not `-d`.
- **A PR can merge and work still continue on the branch.** "Merged" is not
  always "done". `branch-status.sh` flags `gone` upstream but won't delete —
  confirm the branch has no un-pushed commits before removing it.
- **Tracked files in `.worktreeinclude` do nothing.** It copies only gitignored
  matches. A committed `.vscode/settings.json` is already in the worktree; put
  only truly-ignored files (`.env`, `.env.local`, `config/secrets.json`) there.
- **`.worktreeinclude` is skipped with a custom `WorktreeCreate` hook.** For
  non-git VCS (SVN/Perforce/hg) the hook replaces default logic — copy local
  files inside the hook script instead.
- **English-commit rule holds under Chinese prompts.** Don't mirror the
  prompt's language into the commit subject; translate the intent to English.
- **A commit template does not affect `git commit -m`.** Agent harnesses usually
  pass `-m` directly, so the template is guidance, not enforcement. Use
  `check-commit-msg.sh --agentic` for the actual contract.
- **Native attribution is not cryptographic signing.** `Co-Authored-By` and
  `AI-Assisted-By` are message metadata; a Verified badge comes from a signed
  commit object. Preserve both when present, but do not describe them as the
  same guarantee.
- **Don't tag before the release commit exists.** An annotated tag points at a
  commit — create/land the release commit first, then `git tag -a`, then push
  the tag. A tag on the wrong commit means re-tagging (`-f`) and a force-push.
- **`gh`/`glab` are optional.** Recommend them, but never make a workflow step
  hard-depend on a forge CLI being installed or authenticated.
