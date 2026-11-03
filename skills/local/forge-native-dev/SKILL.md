---
name: forge-native-dev
description: 'Right-sized GitHub/GitLab workflow for durable backlog, collaboration, PR review, and issue-linked worktrees. Use when the user explicitly asks to open or manage Issues, Discussions, PRs, or project boards, needs deferred work tracked or coordinated across contributors, or says "開 issue", "幫我開 PR", "清理 branch". Keep bounded experiments, small fixes, and local research local unless external tracking has a concrete purpose.'
---

# forge-native-dev

Use GitHub/GitLab as the canonical **shared backlog**, not a mandatory record
of every action an agent takes. Creating a ticket is cheap; maintaining,
reading, and receiving notifications from unnecessary tickets is not.

**Core thesis**: Right-size tracking before choosing a forge surface. Issues
hold durable work commitments; PRs are review gates. A small experiment can
finish in the conversation and diff without either an Issue or a Discussion.

Lightweight lifecycle: **work -> validate -> report**, with an optional local
note and the repository's normal commit/review policy.
Tracked lifecycle: **Issue -> branch/worktree -> work -> PR -> review -> merge
-> cleanup**. A Discussion is optional, not a prerequisite to either lifecycle.

Surfaces, separated by the question they answer:

| Surface | Question it answers |
|---|---|
| `references/issue-driven-workflow.md` | "Why issues over local TODO.md?" |
| `references/forge-abstraction.md` | "What `gh` command maps to what `glab` command?" |
| `references/agent-patterns.md` | "How do I wire agents to work from issues?" |
| `references/coexistence.md` | "I have git-workflow / PKH installed too — which wins?" |
| `references/github-features.md` | "How do I use Discussions, Projects, Wiki?" |
| `references/gitlab-features.md` | "How do I use Boards, Threads, CI/CD?" |
| `references/conventions.md` | "What commit/branch/merge conventions should I follow?" |
| `scripts/forge.sh` | The sourced library — all other scripts depend on it. |
| `scripts/forge-init.sh` | One-shot repo setup. |
| `scripts/forge-worktree.sh` | Issue-to-worktree-to-PR lifecycle. |
| `scripts/forge-cleanup.sh` | Auto-cleanup merged branches + worktrees. |
| `scripts/forge-status.sh` | Alignment dashboard. |
| `scripts/forge-issue.sh` | Standalone issue operations. |
| `scripts/forge-pr.sh` | Standalone PR/MR operations. |

## When to use this skill

- The user explicitly requests an Issue, Discussion, or shared backlog item.
- Actionable work will remain deferred or blocked, needs ownership/dependency
  tracking, or benefits from asynchronous coordination. Apply the scope gate below;
  "maybe later", "先記下來", or "research" alone does not select an external surface.
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
- Bounded experiments, quick fixes, or same-session research with no remaining
  coordination need — work locally; an online remote does not change this.
- Git-only operations with no requested forge interaction.
- Secret scanning or agent transcript hygiene — use `agent-history-hygiene`.

## Scope gate — before any external creation

1. **Check intent and repository policy.** Honor explicit requests and stricter
   project requirements. Installing this skill or asking to investigate something
   is not itself a request to publish a ticket or discussion.
2. **Default to the lightest sufficient record.** Use the conversation/diff for
   bounded work; add a local research note for reusable conclusions, or the
   project's local task tool for execution handoff. Needing another session or
   a long document alone does not require a forge record.
3. **Use external tracking when it has a concrete purpose:** an explicitly
   requested record, committed future work that would otherwise be lost, a blocker
   or dependency to track, an owner to assign, or asynchronous collaborator input.
   Follow the repository's publication authorization; when unclear, keep local
   rather than routinely asking "should I create an issue?".
4. **Reuse before creating.** Once external tracking is warranted, look for an
   existing relevant Issue/Discussion. Add a meaningful update or link a local
   note there; do not create a new record for each phase, experiment, or worktree.
5. **Choose one surface.** Actionable follow-up → Issue. A genuinely open question
   needing ongoing shared deliberation → Discussion. Do not create both merely
   because one task includes research and implementation.

| Example | Default |
|---|---|
| "Try this integration and run a small example" | Local experiment + findings; no Issue/Discussion |
| "Keep the benchmark rationale for future reference" | Local research doc; no automatic Discussion |
| "Fix this typo and open a PR" | Direct PR; no prerequisite Issue unless repo policy requires it |
| "Ship this next month; blocked on upstream API" | Reuse/create an Issue for the outstanding commitment |
| "Ask maintainers which API we should support" | Discussion if ongoing deliberation is needed |
| New experiment within an existing Issue | Update that Issue only if the result matters to its readers |

Size and duration are signals, not thresholds: a tiny release blocker can need
an Issue; a long solo investigation can stay local. Saving a result is different
from starting an external discussion.

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

Honor the repository's declared shared-backlog policy. Local research docs,
historical TODO entries, and local task handoffs can coexist with Issues; their
presence alone is not a reason to ask for migration or publish new records.
If two active backlog indexes genuinely conflict and policy is unclear, ask
which is canonical. **One shared backlog, not duplicate trackers.** See
[`references/coexistence.md`](references/coexistence.md).

## Core workflow

### 1. Setup (once per project)

```bash
bash scripts/forge-init.sh --target /path/to/project --project-name "My Project"
```

This detects the forge, creates labels, configures git, and adds agent
guidance to `AGENTS.md`. Read [`references/forge-abstraction.md`](references/forge-abstraction.md)
for the full gh/glab mapping.

### 2. Capture durable work as Issues (when warranted)

Apply the scope gate first. For a requested or justified shared backlog item,
reuse an existing Issue or create one with concise acceptance criteria and
appropriate labels. Do not retrospectively create tickets for a small change
already completed in this session merely to fill out the lifecycle.

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

These helpers are for work already tied to an Issue. For a lightweight change,
use a normal branch/worktree if isolation is useful; do not manufacture an Issue
just to use `forge-worktree.sh`. A directly requested PR can use `forge-pr.sh`
without an issue-linked worktree. `finish` publishes a branch and PR, so invoke
it only when that publication is authorized, not merely because work is done.

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

## Merge strategy

**Default: squash and merge.** One logical change = one PR = one commit on
`main`; link an Issue when the change has one, not as a universal prerequisite.

| Strategy | When to use |
|---|---|
| **Squash and merge** | Default. Agent/vibe-coding PRs with WIP commits. Gives the cleanest `git log`. |
| **Rebase and merge** | Every commit in the PR is a meaningful, curated logical change worth preserving. |
| **Create a merge commit** | Almost never in this workflow. Only if you need branch topology in history. |

Why squash is the default:
- Agent work produces noisy WIP commits — squash collapses them into one clean commit.
- One commit per issue on `main` makes `git log --oneline` a readable changelog.
- The squash commit message carries `Closes #N`, auto-closing the issue.
- `git bisect` and `git revert` operate on meaningful units (one feature/fix).

`forge-pr.sh merge` defaults to `--squash`. Override with `--rebase` when
commits are curated, or `--merge` when you need the topology (rare).

## Role awareness

The skill detects your access level to decide what operations are available:

| Role | Detection | Behavior |
|---|---|---|
| **Maintainer** | Has push/write access (owner, org dev with write, collaborator) | Creates labels, assigns issues, sets priority, merges PRs |
| **Contributor** | Read-only or fork-based | Opens issues/PRs, describes priority in body text, leaves labeling to maintainers |

Detection is automatic via `forge_detect_role` (queries repo permissions API).
Override with `--role maintainer` or `--role contributor` in `forge-init.sh`,
or set `FORGE_ROLE_OVERRIDE=maintainer` / `FORGE_ROLE_OVERRIDE=contributor`
in your shell.

### Maintainer behavior

- `forge-init.sh` creates labels, scaffolds issue templates
- `forge-issue.sh backlog` applies `priority/*` and `backlog` labels directly
- `forge-worktree.sh start` assigns the issue and adds `in-progress` label
- Full access to merge, close, and triage

### Contributor behavior

- `forge-init.sh` skips label creation (labels are managed by maintainers)
- `forge-issue.sh backlog` notes priority in the issue body as a suggestion,
  does not apply labels (maintainer will triage)
- Issue templates are still scaffolded (they're just files in the repo)
- PRs can be opened; merging is up to maintainers

**Note**: "maintainer" here means anyone with write access — this includes
org members, collaborators, and core contributors, not just the repo owner.
If you can push to the repo, you're a maintainer in this skill's model.

## Issue vs Discussion: content boundary

Choose between these **only after** external tracking passes the scope gate.
Neither is required for a self-contained evaluation.

| | Issue | Discussion |
|---|---|---|
| **Purpose** | Track an outstanding action, owner, blocker, or deliverable | Resolve an open question through ongoing shared deliberation |
| **Body** | Concise scope and acceptance criteria; link supporting research | The decision/question and why asynchronous input is needed |
| **Closing** | Done when its acceptance criteria are met | Answered or retained while deliberation remains useful |

**Promotion is conditional:** when an existing Discussion produces work that
needs its own tracking, reuse/create an Issue and link back. If a small change
can be completed directly, its PR/diff can link the discussion instead. Do not
backfill a Discussion for a decision already settled in chat.

**Keep one primary record.** Research can stay in `backlog/` even in a hosted-first
project. Link it from an existing Issue/PR when useful; do not mirror every
research document to Discussions or publish duplicate status threads.

## Where things go

| Kind of information | Where it lives | Why |
|---|---|---|
| Bounded experiment or small change | Conversation + diff | No separate tracking lifecycle |
| Reusable research and trade-offs | In-repo research docs (e.g. `backlog/`) | Durable without an external discussion |
| Durable actionable backlog / coordination | Issues (with priority labels) | Searchable, assignable, linkable |
| Ongoing shared design deliberation | GitHub Discussions / existing GitLab issue threads | Asynchronous input, not document storage |
| Past traps, debugging knowledge | `pitfalls/` in-repo | Grep-able by symptom, portable |
| Code review | PR/MR comments | Tied to the diff |
| Backlog visualization | GitHub Projects / GitLab Boards | Built-in to the forge |
| Release notes | Tags + auto-generated release notes | Derived from PRs |

**Pitfalls and reusable research can stay in-repo** even in forge-native mode.
The forge is the shared backlog, not a requirement to publish all project memory.

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

Update an existing Issue for meaningful milestones, blockers, or changed
decisions that matter to its readers. Do not publish every internal experiment
or status check merely because a task takes time:

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
- **`scripts/forge-init.sh [--target DIR] [--project-name NAME] [--role auto|maintainer|contributor] [--skip-labels] [--skip-templates] [--skip-git-config] [--force] [--help]`**
  — one-shot setup: labels (maintainer only), issue templates, git config,
  AGENTS.md snippet. Role auto-detected from API permissions.
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
- **After a PR merges, always create a new branch from updated main.**
  Do not reuse the merged branch (squash-merge makes its history diverge
  from main). Do not try to reopen a merged PR (GitHub does not allow it).
  Each PR is one logical change; follow-ups are new branches and new PRs.
  See [`references/conventions.md`](references/conventions.md) for details.
- **GitHub Discussion categories cannot be created via API.** The GraphQL
  API has no `createDiscussionCategory` mutation. Default categories
  (General, Ideas, Q&A, Announcements, Polls, Show and tell) are created
  automatically when Discussions is enabled. Custom categories (e.g.
  "Design", "Research") must be created via the web UI:
  Settings → Discussions → New category.
- **`gh project link --owner @me` fails for personal repos.** Use the
  actual username (e.g. `--owner myuser`) extracted from the remote URL.
  The `forge_project_create` function handles this automatically.
