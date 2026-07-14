# Plan: author the `git-workflow` local skill

## Context

The user works mostly **solo**, has done little team development, and has run
past projects with ad-hoc git habits (manual `Add`/`Update`-style capitalized
commit subjects, no unified branching or release convention). They want a
single **opinionated, scale-aware git workflow skill** that aligns both
themselves and their coding agents on modern best practice, spanning three
project scales:

- **Tier 1** — small/early solo project: develop on `main`, linear history.
- **Tier 2** — mid project with a prod/dev split.
- **Tier 3** — multi-person / multi-month, or a grown solo "vibe-coding"
  project where PRs become the natural feature-ship boundary.

The skill must encode: Conventional Commits (**English commits even for
Chinese prompts**), fast-forward + `pull --rebase` linear history, branch
naming that separates agent/vibe branches from human ones, git **worktrees**
for parallel agents, **SemVer** release tagging (incl. Python PyPI
tag-driven versioning), phase-per-commit discipline, and **pre-merge secret
hygiene** that *defers to the existing `agent-history-hygiene` skill* rather
than reimplementing secret scanning. It also ships a bilingual educational
("科普") docs page, since no git best-practice doc exists in the repo yet.

This is greenfield — no existing local skill owns commit/branch/worktree/tag
workflow; `agent-history-hygiene` only owns committing agent artifacts without
leaking secrets, and is the integration target.

## Decisions (locked with the user)

| Decision | Choice |
|---|---|
| Helper scripts | Bundle **`branch-status.sh` + `check-commit-msg.sh`** |
| In-repo activation | **Downstream-only** — scaffold with `--no-symlinks`, no `.agents/`/`.claude/` symlinks |
| Marketplace placement | **New `version-control` plugin group** (category `Engineering`) |
| Docs-site treatment | **Full bilingual now** — EN + `.zh-TW.md` for reference + skill pages, nav + index rows |

## Verified facts to encode (don't get these wrong)

- **`.worktreeinclude`** is real, lives at project root, uses `.gitignore`
  syntax, and **only copies files that are *gitignored*** — tracked files
  (e.g. a committed `.vscode/settings.json`) are already present in the fresh
  worktree checkout and must **not** be listed there. Correct use: `.env`,
  `.env.local`, `config/secrets.json`. Not processed when a custom
  `WorktreeCreate` hook is used (non-git VCS). Source: code.claude.com/docs/en/worktrees.
- Claude Code worktrees: `claude --worktree <name>` → `.claude/worktrees/worktree-<name>/`,
  branches from `origin/HEAD` by default (`worktree.baseRef:"head"` for local HEAD);
  subagent `isolation: worktree` frontmatter; **gitignore `.claude/worktrees/`**.
  SpecStory tracks by *directory*, so a worktree's fresh dir cleanly separates
  parallel-agent transcript history — a real benefit to call out.
- Python tag-driven versioning: **setuptools-scm** (setuptools backend) or
  **hatch-vcs** (hatchling) make the git tag the single source of truth;
  tags `vX.Y.Z`, PEP 440-compatible. Source: packaging.python.org single-source-version.

## Files to create

Scaffold first (downstream-only):

```bash
bash skills/local/skill-author/scripts/new-skill.sh --local --no-symlinks git-workflow
```

### Skill: `skills/local/git-workflow/`

**`SKILL.md`** (< 500 lines, house style modeled on `agent-history-hygiene`):
- Frontmatter: `name: git-workflow` + a pushy, bilingual `description`
  (~450 chars, ≤500 preferred). Draft:
  > Opinionated, scale-aware git workflow: Conventional Commits (English-only),
  > linear history via fast-forward + `pull --rebase`, when to commit straight
  > to `main` vs branch, PR/GitHub-Flow as projects grow, worktrees for parallel
  > agents, SemVer release tags, and pre-merge secret hygiene. Use when
  > committing, branching, merging, opening a PR, tagging a version, setting up
  > worktrees, or cleaning up stale branches — incl. "幫我 commit / 整理 git",
  > "should I branch or PR", "git 工作流", "how do I tag a release".
- Body sections:
  1. Intro + **surface table** (scenario → what to do → which reference/script).
  2. **Core principles** (commits are English + Conventional; prefer linear
     history / `--ff-only` + `pull --rebase`; one phase = one commit;
     never leak secrets — defer to `agent-history-hygiene`).
  3. **Pick your tier** — a decision table (Tier 1 solo-on-main / Tier 2
     dev+main / Tier 3 PR + GitHub Flow) with the signal that promotes you.
  4. **Commit messages** — the `type(scope): subject` shape, allowed types,
     `!`/`BREAKING CHANGE` → major; imperative, lowercase, ≤72-char header;
     English rule; `git config commit.template`. Defer full spec to reference.
  5. **Branch naming** — `feat/ fix/ chore/ docs/ refactor/ exp/` for
     human-intent branches; `agent/<desc>` namespace for agent/vibe branches;
     Claude's `worktree-*` is a third namespace. Enables targeted cleanup.
  6. **Merge & sync** — `pull.rebase=true`, `merge.ff=only`; squash-merge PRs
     for vibe-coding (collapses WIP), rebase-merge to keep per-commit history.
     Recommend the **forge CLIs**: `gh` (GitHub) / `glab` (GitLab) as the
     default way to open/inspect/merge PRs from the terminal
     (`gh pr create`, `gh pr view --web`, `gh pr checks`, `gh pr merge --squash`;
     `glab mr create/view/merge` equivalents). Note the vendored
     `create-pull-request` skill (github-workflow group) as a companion.
  7. **Worktrees for parallel agents** — the verified facts above (brief),
     defer detail to reference.
  8. **Versioning & releases** — SemVer ↔ Conventional Commits mapping,
     annotated `v`-prefixed tags, Python tag-driven note; defer to reference.
  9. **Before you merge/ship** — phase-per-commit; `.vscode/{settings,extensions}.json`
     commit habit (reproducible env, optional); **secret + artifact hygiene →
     cross-link `agent-history-hygiene` `scan-staged.sh` (exit 0/10/20) and the
     `redact-agent-secrets` pinned hook**; branch cleanup via `branch-status.sh`.
  10. **When to use / When NOT to use** (bilingual triggers).
  11. **Available scripts / Bundled assets / Reference files** (each cited with
     a "Read when…" load condition).
  12. **Gotchas** (bolded-claim bullets) — e.g. tracked files don't belong in
     `.worktreeinclude`; `merge.ff=only` will refuse a diverged pull (use
     `--rebase`); squash-merge orphans the branch → shows as `gone` upstream;
     don't tag before the release commit; English-commit rule holds under
     Chinese prompts; secret scrubbing is `agent-history-hygiene`'s job;
     `gh`/`glab` are recommended but optional — scripts must degrade to plain
     git, never hard-require a forge CLI.

**`references/`** (no frontmatter; H1 + "Read this when…" + TOC + sections):
- `conventional-commits.md` — condensed spec: type list (feat, fix, docs,
  style, refactor, perf, test, build, ci, chore, revert), scope, body/footers
  (`Refs:`, `Co-Authored-By:`, `BREAKING CHANGE:`), examples, English rule.
- `project-tiers.md` — the 3-tier framework in depth, per-tier branching +
  merge strategy + promotion signals; GitHub Flow summary.
- `worktrees-parallel-agents.md` — Claude Code worktree mechanics,
  `.worktreeinclude`, subagent isolation, SpecStory per-dir separation,
  cleanup/gitignore caveats.
- `versioning-and-releases.md` — SemVer, annotated tags, when to tag, Python
  setuptools-scm / hatch-vcs single-source-of-truth, changelog note.
- `branch-hygiene.md` — triaging local branches (merged / gone-upstream /
  stale), `git fetch --prune`, `git branch -vv` → `: gone]`, safe delete,
  the "PR merged but work continues on branch" case; `gh pr status` /
  `glab mr list` to reconcile local branches against remote PR/MR state.
- `lazygit-cheatsheet.md` — learning-aid keybindings (stage/commit/amend/
  interactive-rebase/push/branch), explicitly flagged as removable later.

**`scripts/`** (bash 3.2, `--help`, data→stdout / prose→stderr):
- `branch-status.sh [--json] [--stale-days N] [--help]` — classify every
  local branch as `active` / `merged` / `gone` (upstream deleted, e.g. PR
  squash-merged) / `stale` (no commits in N days). TSV default, `--json` for
  callers. Exit 0 always (state is data, not error). Answers "which branches
  are done vs still in-dev". If `gh`/`glab` is on `PATH` and the remote is a
  GitHub/GitLab repo, enrich `gone`/`merged` detection with `gh pr list
  --state merged` (graceful fallback to pure-git `git branch -vv` gone-upstream
  detection when absent or non-forge remote — never hard-fail on missing CLI).
- `check-commit-msg.sh [--help] [--types]` — read a commit message from arg,
  `--file PATH`, or stdin; validate the Conventional Commits header. Exit
  **0 valid / 1 invalid / 2 bad-args**; prints the offending rule to stderr.

**`assets/`**:
- `commit-template.txt` — `git config commit.template` body showing the
  `type(scope): subject` skeleton + footer hints.
- `worktreeinclude.template` — example `.worktreeinclude` (gitignored env
  files only, with a comment that tracked files don't belong here).

### Docs site (bilingual)

- `docs/reference/git-workflow.md` + `.zh-TW.md` — the human-facing "科普"
  explainer (Conventional Commits, SemVer, GitHub Flow, rebase vs merge,
  worktrees, tag-driven Python versions, `gh`/`glab` forge CLIs), with
  authoritative source links.
- `docs/skills/git-workflow.md` + `.zh-TW.md` — the "should I use this?" page.
- Add a row to `docs/skills/index.md` (+ `index.zh-TW.md`).
- `mkdocs.yml` — register the two EN pages under `Reference:` and the skills
  nav section (zh-TW siblings auto-resolve via the i18n suffix structure).

### Distribution + repo bookkeeping

- `skills/.claude-plugin/marketplace.json` — add a new group:
  ```json
  {
    "name": "version-control",
    "description": "Scale-aware git workflow discipline: Conventional Commits, linear history, worktrees for parallel agents, SemVer release tagging, and pre-merge hygiene",
    "category": "Engineering",
    "tags": ["git", "commits", "branching", "worktree", "semver", "conventional-commits"],
    "source": "./",
    "strict": false,
    "skills": ["./local/git-workflow"]
  }
  ```
- `README.md` — add a "What's in here" row for `git-workflow`.

## Integration with `agent-history-hygiene` (do NOT reimplement)

The "before you merge/ship" section must **cross-link**, not duplicate:
- Secret scanning → `skills/local/agent-history-hygiene/scripts/scan-staged.sh`
  (exit `0` clean / `10` redacted / `20` leaks) and the `redact-agent-secrets`
  pinned pre-commit hook (`rev: ahh-v*`).
- Committing vs dropping agent transcripts/plans before a squash-merge →
  that skill's `stage-agent-artifacts.sh` and `references/remediation.md`.
- Add both skills to each other's "Related skills" mentally, but only edit
  `git-workflow`'s SKILL.md here (a reciprocal link in agent-history-hygiene
  is optional and out of scope unless trivial).

## Verification

1. **Lint the skill**:
   `bash skills/local/skill-author/scripts/lint-skill.sh skills/local/git-workflow`
   → frontmatter/length, script hygiene (`--help`), reference reachability all pass.
2. **Scripts smoke**:
   - `bash skills/local/git-workflow/scripts/branch-status.sh --help` and a real
     run in this repo; `--json` emits valid JSON lines.
   - `printf 'feat: add x\n' | check-commit-msg.sh` → exit 0;
     `printf 'Added x\n' | check-commit-msg.sh` → exit 1 with a rule message;
     no-arg/no-stdin → exit 2.
3. **Marketplace**: `make marketplace` → new `version-control` group validates,
   `./local/git-workflow` path resolves, no duplicate/reserved-name errors,
   no "unlisted skill" warning for git-workflow.
4. **Docs build**: `make docs-build` (strict) succeeds with the new nav entries
   and bilingual pages; no broken-link failures.
5. Confirm **no** `.agents/skills/git-workflow` / `.claude/skills/git-workflow`
   symlinks exist (downstream-only was requested).

## Out of scope / possible follow-ups

- A commit-message git hook wiring (leave `check-commit-msg.sh` agent-invoked;
  users can wire it into `commit-msg` themselves — mention as an escape hatch).
- Reciprocal "Related skills" edit inside `agent-history-hygiene` (optional).
- `skill-creator` eval loop (offer as a handoff after lint passes).
