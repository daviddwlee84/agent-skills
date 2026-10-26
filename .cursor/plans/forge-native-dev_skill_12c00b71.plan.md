---
name: forge-native-dev skill
overview: Create a new local skill `forge-native-dev` that provides a complete issue-driven development workflow backed by GitHub/GitLab, with forge CLI abstraction, worktree-per-issue lifecycle, auto-cleanup, and agent guidance for using Issues as the canonical backlog and PRs as review gates.
todos:
  - id: forge-lib
    content: Write `scripts/forge.sh` -- the sourced library with forge detection (`forge_detect`) and all abstracted functions (issue, PR, label, discussion ops) for both gh and glab CLIs
    status: completed
  - id: forge-init
    content: Write `scripts/forge-init.sh` -- one-shot repo setup (detect forge, create labels, scaffold issue templates, configure git, append AGENTS.md snippet)
    status: completed
  - id: forge-worktree
    content: Write `scripts/forge-worktree.sh` -- the core workflow script (start/finish/list subcommands for issue-to-worktree-to-PR lifecycle)
    status: completed
  - id: forge-cleanup
    content: Write `scripts/forge-cleanup.sh` -- auto-cleanup merged branches + worktrees with confirmation and --dry-run/--force flags
    status: completed
  - id: forge-status
    content: Write `scripts/forge-status.sh` -- alignment dashboard showing issue/branch/worktree/PR state
    status: completed
  - id: forge-issue-pr
    content: Write `scripts/forge-issue.sh` and `scripts/forge-pr.sh` -- standalone issue and PR lifecycle commands wrapping forge.sh
    status: completed
  - id: skill-md
    content: "Write `SKILL.md` with full agent guidance: issue-first workflow, coexistence detection (git-workflow + PKH), platform feature usage, progress reporting patterns"
    status: completed
  - id: references
    content: "Write reference docs: issue-driven-workflow.md, forge-abstraction.md, agent-patterns.md, coexistence.md, github-features.md, gitlab-features.md"
    status: completed
  - id: assets
    content: "Create assets: agent-guidance.md.template, issue templates for .github/ and .gitlab/"
    status: completed
  - id: marketplace
    content: Add forge-native-dev to marketplace.json and create discovery symlinks for this repo
    status: completed
isProject: false
---

# forge-native-dev skill

## Context and Philosophy

The "issue is the new PR" thesis: with AI agents, the cost of creating a PR
is near-zero. Issues become the canonical unit of work (backlog, intent,
discussion), PRs become mechanical review gates. The skill makes the full
lifecycle frictionless: **Issue -> branch -> worktree -> work -> PR -> review
-> merge -> cleanup**.

This is the **hosted-first alternative** to `project-knowledge-harness`
(which is local-first / git-native). One skill per project, not both.
Pitfalls stay in-repo (grep-ability), research goes to Discussions/Wiki
(collaboration).

## Skill Location

[`skills/local/forge-native-dev/`](skills/local/forge-native-dev/)

## Directory Structure

```
skills/local/forge-native-dev/
  SKILL.md
  scripts/
    forge.sh                  # Sourced library: forge detection + abstracted functions
    forge-init.sh             # One-shot repo setup (labels, templates, AGENTS.md, git config)
    forge-issue.sh            # Issue CRUD (create, list, view, assign, close, comment)
    forge-pr.sh               # PR lifecycle (create-from-issue, merge, status)
    forge-worktree.sh         # Worktree lifecycle (create-per-issue, list, cleanup)
    forge-status.sh           # Alignment dashboard: issue/branch/worktree/PR state
    forge-cleanup.sh          # Auto-cleanup merged branches + worktrees (with confirmation)
  references/
    issue-driven-workflow.md  # Philosophy + practical patterns
    forge-abstraction.md      # gh vs glab mapping table, what's supported, gaps
    agent-patterns.md         # How to configure agents for issue/PR workflows
    coexistence.md            # Relationship to git-workflow and project-knowledge-harness
    github-features.md        # Discussions, Projects, Wiki, Actions patterns
    gitlab-features.md        # Boards, Threads, CI/CD, MR patterns
  assets/
    agent-guidance.md.template  # AGENTS.md snippet for forge-native workflow
    issue-templates/            # Default issue templates (.github/ and .gitlab/)
```

## Core Components

### 1. `scripts/forge.sh` -- Forge Abstraction Library

Sourced by all other scripts. Key exports:

- **Detection**: `forge_detect` -- parses `git remote get-url origin` to
  determine `github` | `gitlab` | `unknown`. Caches result in a shell var.
  Also checks CLI availability (`gh --version` / `glab --version`).
- **Issue ops**: `forge_issue_create`, `forge_issue_list`,
  `forge_issue_view`, `forge_issue_close`, `forge_issue_comment`,
  `forge_issue_assign`, `forge_issue_label`
- **PR/MR ops**: `forge_pr_create`, `forge_pr_list`, `forge_pr_view`,
  `forge_pr_merge`, `forge_pr_status`, `forge_pr_link_issue`
- **Discussion ops**: `forge_discussion_create` (GitHub Discussions API
  via `gh api`; GitLab: issue thread as fallback, documented in
  `references/gitlab-features.md`)
- **Project ops**: `forge_project_view` (GitHub Projects / GitLab Boards --
  read-only initially, document how to create/configure manually)
- **Labels**: `forge_label_ensure` -- idempotently create a label if missing

Each function: detects forge, maps to the right CLI invocation, returns
structured output (JSON where possible via `--json` flags). Unknown forge =
error with actionable message.

### 2. `scripts/forge-init.sh` -- One-Shot Setup

```bash
scripts/forge-init.sh \
  --target /path/to/project \
  --project-name "My Project"
```

Does:
1. Detect forge and CLI (`forge_detect`)
2. Create standard labels: `priority/P1`, `priority/P2`, `priority/P3`,
   `type/bug`, `type/feature`, `type/chore`, `agent-task`, `backlog`
3. Optionally scaffold issue templates in `.github/ISSUE_TEMPLATE/` or
   `.gitlab/issue_templates/`
4. Configure git: `fetch.prune true`, `pull.rebase true`, `merge.ff only`
5. Append agent-guidance snippet to `AGENTS.md` (with sentinel marker,
   idempotent like PKH's init)
6. Print summary of what was set up, what needs manual action (e.g.,
   enabling Discussions on GitHub, creating a Project board)

### 3. `scripts/forge-worktree.sh` -- Worktree-Per-Issue Lifecycle

The central workflow script:

```bash
# Start working on issue #42
forge-worktree.sh start 42
# -> creates branch issue/42-<slug-from-title>
# -> creates worktree at .worktrees/issue-42/ (or configurable path)
# -> assigns issue to current user
# -> adds "in progress" label
# -> prints cd command

# Check what's active
forge-worktree.sh list
# -> shows table: issue# | branch | worktree path | PR# | status

# Finish: create PR and prepare for cleanup
forge-worktree.sh finish 42
# -> pushes branch
# -> creates PR linking to issue (Closes #42)
# -> prints PR URL
```

Branch naming convention: `issue/<number>-<kebab-slug>` (e.g.,
`issue/42-add-oauth-support`). Agent branches get `agent/issue/<number>-<slug>`.

### 4. `scripts/forge-cleanup.sh` -- Auto-Cleanup

```bash
forge-cleanup.sh [--dry-run] [--force]
```

1. Lists all local branches matching `issue/*` and `agent/issue/*`
2. For each, checks if the linked PR is merged (via `forge_pr_status`)
3. If merged: lists the branch + associated worktree
4. Without `--force`: prompts for confirmation per branch (or batch)
5. Deletes local branch (`git branch -D`) + removes worktree
   (`git worktree remove`)
6. Reports what was cleaned

### 5. `scripts/forge-status.sh` -- Alignment Dashboard

```bash
forge-status.sh [--json]
```

Shows the full state at a glance:

```
Issues (open, assigned to you):
  #42  Add OAuth support       branch: issue/42-add-oauth  PR: #55 (open, CI passing)
  #38  Fix login redirect      branch: issue/38-fix-login  PR: none (no PR yet)
  #51  Update docs             branch: none                PR: none (not started)

Orphaned branches (no open issue):
  issue/30-old-feature         PR: #44 (merged) -> ready to cleanup

Worktrees:
  .worktrees/issue-42/  -> issue/42-add-oauth  (active)
  .worktrees/issue-38/  -> issue/38-fix-login  (active)
```

### 6. SKILL.md -- Agent Guidance

Key sections:

- **When to use**: Detected by remote URL pointing to GitHub/GitLab +
  CLI available. If `git-workflow` is also installed, agent asks user
  preference on first ambiguous operation (default: prefer forge-native-dev
  for any operation involving the remote).
- **Coexistence with PKH**: If `TODO.md` with PKH markers exists, warn
  and ask user. One workflow per project.
- **Issue-first workflow**: When user says "maybe later" / "先記下來" /
  describes a bug/idea, create an Issue (not a local file). Apply
  appropriate labels. The agent defaults to creating issues rather than
  asking "should I create an issue?".
- **Working on an issue**: Use `forge-worktree.sh start <number>`.
  Work in the worktree. Commit conventionally. When done, use
  `forge-worktree.sh finish <number>`.
- **Where things go**:
  - Actionable work: Issues (with priority labels)
  - Design discussion / research: Discussions (GitHub) or issue threads (GitLab)
  - Past traps / debugging knowledge: `pitfalls/` in-repo (grep-able)
  - Review: PR comments
  - Visualization: GitHub Projects / GitLab Boards (document, don't automate)
- **PR as review gate**: PRs are created to be reviewed (by humans or
  review agents), not to propose work. The issue already described the
  intent. PR description auto-fills from the issue.
- **Progress reporting**: Agent posts progress comments on the issue
  when working on long tasks. Use `forge_issue_comment`.
- **Agent configuration patterns**: Document how to set up:
  - GitHub: `@copilot` or agent bots in issues
  - Cursor: background agents that check issues
  - Claude Code: `--worktree` + issue-driven sessions

### 7. References

- **`issue-driven-workflow.md`**: The philosophy. Why issues are better
  than PRs as the unit of work. Link to Sindre Sorhus's tweets, the
  lazygit issue, and related thinking. Practical patterns for solo dev
  with agents vs. team collaboration.
- **`forge-abstraction.md`**: Complete mapping table of gh vs glab
  commands. What's fully supported, what's best-effort, what's missing.
  Escape hatches for direct CLI calls when the abstraction doesn't cover
  a case.
- **`agent-patterns.md`**: Concrete recipes for configuring agents to
  work with issues. GitHub Actions triggers, Cursor task patterns,
  Claude Code worktree sessions.
- **`coexistence.md`**: Decision tree for choosing between this skill,
  git-workflow, and PKH. Detection logic. Migration path from PKH
  (TODO.md items -> Issues).
- **`github-features.md`** / **`gitlab-features.md`**: Platform-specific
  feature guides (Discussions, Projects, Wiki, Boards, CI/CD integration).

## Marketplace Integration

Add to [`skills/.claude-plugin/marketplace.json`](skills/.claude-plugin/marketplace.json):
- Either in the existing `version-control` group alongside `git-workflow`,
  or create a new group (e.g., `forge-workflow`).

## Key Design Decisions

- **Branch naming**: `issue/<number>-<slug>` -- ties branch to issue,
  enables cleanup script to find the link
- **Worktree location**: `.worktrees/issue-<number>/` at repo root
  (gitignored). Configurable via env var.
- **forge.sh is a sourced library, not a standalone CLI** -- other scripts
  and the agent can source it. Functions use `forge_` prefix namespace.
- **Confirmation-based cleanup, not fully automatic** -- `forge-cleanup.sh`
  shows what will be deleted and asks. `--force` for CI/scripted use.
- **Pitfalls stay in-repo** -- even in forge-native mode, `pitfalls/` is
  grep-able local knowledge. Research goes to Discussions/Wiki for
  collaboration. The skill does NOT create pitfalls/ (that's PKH's job
  if also installed, or the user's own convention).
