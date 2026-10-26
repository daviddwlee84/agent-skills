---
name: forge-native-dev
description: Issue-driven development workflow backed by GitHub/GitLab — uses Issues as the canonical backlog, PRs as review gates, and worktrees for per-issue isolation with auto-cleanup. The hosted-first alternative to project-knowledge-harness. Use when committing to an issue-first workflow, creating backlog items as Issues, managing worktree-per-issue lifecycles, or cleaning up merged branches — incl. "開 issue", "maybe later", "幫我開 PR", "清理 branch".
---

# forge-native-dev

An opinionated, issue-driven development workflow that treats GitHub/GitLab as
the single source of truth for intent, backlog, and collaboration — not just
code hosting.

**Core thesis**: Issues are the unit of work. PRs are review gates. With AI
agents, creating a PR is near-zero cost — the human's job shifts from
*proposing* changes (PR-first) to *describing intent* (issue-first) and
*reviewing* results (PR-as-gate).

Lifecycle: **Issue -> branch -> worktree -> work -> PR -> review -> merge -> cleanup**.

Surfaces, separated by the question they answer:

| Surface | Question it answers |
|---|---|
| `references/issue-driven-workflow.md` | "Why issues over local TODO.md?" |
| `references/forge-abstraction.md` | "What `gh` command maps to what `glab` command?" |
| `references/agent-patterns.md` | "How do I wire agents to work from issues?" |
| `references/coexistence.md` | "I have git-workflow / PKH installed too — which wins?" |
| `references/github-features.md` | "How do I use Discussions, Projects, Wiki?" |
| `references/gitlab-features.md` | "How do I use Boards, Threads, CI/CD?" |
| `scripts/forge.sh` | The sourced library — all other scripts depend on it. |
| `scripts/forge-init.sh` | One-shot repo setup. |
| `scripts/forge-worktree.sh` | Issue-to-worktree-to-PR lifecycle. |
| `scripts/forge-cleanup.sh` | Auto-cleanup merged branches + worktrees. |
| `scripts/forge-status.sh` | Alignment dashboard. |
| `scripts/forge-issue.sh` | Standalone issue operations. |
| `scripts/forge-pr.sh` | Standalone PR/MR operations. |

## When to use this skill

- The user says "open an issue", "create a backlog item", "開 issue",
  "maybe later", "先記下來", or describes a bug/idea worth tracking.
- The user asks "should I open a PR?", "幫我開 PR", or finishes work on
  a branch and needs to ship it.
- The user says "clean up branches", "清理 branch", "which branches are
  done?", or has stale worktrees.
- The user wants to see the state of their issues/branches/PRs at a glance.
- A new project needs to be set up for issue-driven development.
- The user asks about configuring agents to work from GitHub/GitLab issues.

## When NOT to use this skill

- The project has no GitHub/GitLab remote — use `git-workflow` instead.
- The user explicitly prefers `project-knowledge-harness` (local TODO.md).
- Purely offline git operations with no forge interaction.
- Secret scanning or agent transcript hygiene — use `agent-history-hygiene`.

## Coexistence with other skills

### If `git-workflow` is also installed

Both skills cover branching, PRs, and worktrees. On first ambiguous
operation (e.g., "should I branch?", "open a PR"), ask the user:

> I see both `git-workflow` (git-native) and `forge-native-dev`
> (GitHub/GitLab-native) are available. Which workflow do you prefer for
> this project? Default: `forge-native-dev` for any operation involving
> the remote forge.

Once decided, remember the preference for the session. `forge-native-dev`
is the upgrade path — it covers everything `git-workflow` does plus the
forge layer.

### If `project-knowledge-harness` is also installed

PKH uses `TODO.md` + `backlog/` + `pitfalls/` as file-based project memory.
`forge-native-dev` uses Issues + Discussions + in-repo `pitfalls/`.

If `TODO.md` exists with PKH markers (`## P1` / `## P2` etc.), warn:

> This project uses `project-knowledge-harness` (local TODO.md) for backlog.
> `forge-native-dev` uses Issues instead. Using both creates duplicate
> sources of truth. Which do you prefer for this project?

**One workflow per project, not both.** The migration path is documented in
[`references/coexistence.md`](references/coexistence.md).

## Core workflow

### 1. Setup (once per project)

```bash
bash scripts/forge-init.sh --target /path/to/project --project-name "My Project"
```

This detects the forge, creates labels, configures git, and adds agent
guidance to `AGENTS.md`. Read [`references/forge-abstraction.md`](references/forge-abstraction.md)
for the full gh/glab mapping.

### 2. Capture intent as Issues

When the user surfaces a "maybe later" idea, a bug, or a feature request:

**Default to creating an Issue.** Do not ask "should I create an issue?" —
just create it with appropriate labels.

```bash
# Quick backlog item
bash scripts/forge-issue.sh backlog \
  --title "Add pagination to search" \
  --body "Results page loads all items; should paginate at 50." \
  --priority P3 --effort M

# Bug report
bash scripts/forge-issue.sh create \
  --title "Login redirect fails on Safari" \
  --body "Steps to reproduce: ..." \
  --label "type/bug" --label "priority/P2"

# Feature request
bash scripts/forge-issue.sh create \
  --title "Add dark mode toggle" \
  --body "User preference, persist in localStorage." \
  --label "type/feature" --label "backlog"
```

### 3. Work on an issue

```bash
# Start: creates branch + worktree, assigns issue, adds "in-progress" label
bash scripts/forge-worktree.sh start 42

# Agent variant (uses agent/ branch prefix)
bash scripts/forge-worktree.sh --agent start 42

# Work in the worktree
cd .worktrees/issue-42/
# ... make changes, commit conventionally ...

# Finish: pushes branch, creates PR linking to issue
bash scripts/forge-worktree.sh finish 42
```

### 4. Review and merge

The PR is a review artifact. The issue already described the intent.
PR description auto-fills with `Closes #42`.

Review happens on the PR — by humans, review agents, or both.

```bash
# Check PR status
bash scripts/forge-pr.sh status

# Merge (default: squash, delete branch)
bash scripts/forge-pr.sh merge 55
```

### 5. Clean up

After PRs merge, clean up stale branches and worktrees:

```bash
# See what's ready to clean
bash scripts/forge-cleanup.sh --dry-run

# Clean with confirmation
bash scripts/forge-cleanup.sh

# Force (no confirmation, for scripted use)
bash scripts/forge-cleanup.sh --force
```

### 6. Dashboard

See the full state at a glance:

```bash
bash scripts/forge-status.sh          # your assigned issues
bash scripts/forge-status.sh --all    # all open issues
```

## Where things go

| Kind of information | Where it lives | Why |
|---|---|---|
| Actionable work (bugs, features, chores) | Issues (with priority labels) | Searchable, assignable, linkable |
| Design discussion, research, trade-offs | GitHub Discussions / GitLab issue threads | Collaborative, threaded |
| Past traps, debugging knowledge | `pitfalls/` in-repo | Grep-able by symptom, portable |
| Code review | PR/MR comments | Tied to the diff |
| Backlog visualization | GitHub Projects / GitLab Boards | Built-in to the forge |
| Release notes | Tags + auto-generated release notes | Derived from PRs |

**Pitfalls stay in-repo** even in forge-native mode. They need to be
grep-able by error message from any clone. Research and discussion go to
the forge because they benefit from collaboration features.

## Issue-as-backlog conventions

Use labels to mirror priority and type:

- `priority/P1`, `priority/P2`, `priority/P3` — priority lanes
- `type/bug`, `type/feature`, `type/chore` — work type
- `backlog` — deferred work (equivalent to PKH's `## P?`)
- `agent-task` — explicitly flagged for agent implementation
- `in-progress` — currently being worked on
- `discussion` — not actionable work, just a topic

## Agent guidance for issue-driven work

### Checking for work

When the user asks "what should I work on?" or "有什麼可以做的?":

```bash
bash scripts/forge-issue.sh list --assignee @me
```

### Progress reporting

When working on a long task, post progress comments on the issue:

```bash
bash scripts/forge-issue.sh comment 42 \
  --body "Progress: implemented the API endpoint, working on tests next."
```

### Multi-session / multi-agent work

Each agent session should work in its own worktree. Use `--agent` prefix
to distinguish agent branches from human branches:

```bash
# Agent 1 works on issue 42
bash scripts/forge-worktree.sh --agent start 42

# Agent 2 works on issue 38
bash scripts/forge-worktree.sh --agent start 38
```

### Agent configuration patterns

See [`references/agent-patterns.md`](references/agent-patterns.md) for
concrete recipes:

- GitHub: Copilot coding agent in issues, GitHub Actions triggers
- Cursor: background agents, worktree-per-issue sessions
- Claude Code: `--worktree` flag, issue-driven sessions

## Branch naming

| Who | Pattern | Example |
|---|---|---|
| Human | `issue/<number>-<slug>` | `issue/42-add-oauth` |
| Agent | `agent/issue/<number>-<slug>` | `agent/issue/42-add-oauth` |

Both patterns are recognized by `forge-cleanup.sh` and `forge-status.sh`.

## Available scripts

- **`scripts/forge.sh`** — sourced library, not run directly. All other
  scripts depend on it. Exports `forge_detect`, `forge_issue_*`,
  `forge_pr_*`, `forge_label_ensure`, `forge_slugify`, `forge_whoami`,
  `forge_default_branch`.
- **`scripts/forge-init.sh [--target DIR] [--project-name NAME] [--skip-labels] [--skip-templates] [--skip-git-config] [--force] [--help]`**
  — one-shot setup: labels, issue templates, git config, AGENTS.md snippet.
- **`scripts/forge-worktree.sh <start|finish|list> [ISSUE_NUM] [--agent] [--base BRANCH] [--draft] [--help]`**
  — the core lifecycle script.
- **`scripts/forge-cleanup.sh [--dry-run] [--force] [--all] [--help]`**
  — auto-cleanup merged branches + worktrees.
- **`scripts/forge-status.sh [--json] [--assigned] [--all] [--help]`**
  — alignment dashboard.
- **`scripts/forge-issue.sh <create|list|view|close|comment|assign|label|backlog> [--help]`**
  — standalone issue operations.
- **`scripts/forge-pr.sh <create|list|view|status|merge|link> [--help]`**
  — standalone PR/MR operations.

## Gotchas

- **`gh` / `glab` must be installed and authenticated.** The skill degrades
  to error messages without them — it does not fall back to raw git for
  forge operations. Run `gh auth status` or `glab auth status` to verify.
- **Squash-merge orphans the source branch.** After a squashed PR, the
  branch's commits never appear on the base, so `git branch --merged`
  won't list it. `forge-cleanup.sh` handles this by checking PR status
  directly instead of relying on git merge state.
- **Worktree path is relative to repo root.** `FORGE_WORKTREE_ROOT`
  defaults to `.worktrees`. It should be gitignored (the init script does
  this). Gitignored files (`.env`, etc.) are NOT auto-copied into
  worktrees — use a `.worktreeinclude` file (see `git-workflow`'s
  `references/worktrees-parallel-agents.md`).
- **One branch per issue.** If multiple branches match `issue/42-*`, the
  scripts error. Resolve manually or use `--agent` for agent branches.
- **GitHub Discussions API requires GraphQL.** The `forge_discussion_create`
  function falls back to creating a labeled issue. Use the web UI for full
  Discussion features until the CLI catches up.
- **Label creation is idempotent but case-sensitive.** `priority/P1` and
  `Priority/P1` are treated as different labels. Stick with lowercase.
- **Issue templates are scaffolded, not enforced.** The init script copies
  templates into `.github/ISSUE_TEMPLATE/` or `.gitlab/issue_templates/`.
  Users can modify or remove them.
- **The `@me` assignee shortcut** works in `gh` but may need the actual
  username in older `glab` versions.
