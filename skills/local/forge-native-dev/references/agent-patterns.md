# Agent Configuration Patterns

Recipes for wiring AI coding agents into the issue-driven workflow.

## Pattern 1: Cursor Agent with worktree-per-issue

For work already tied to an Issue, an agent can use an isolated issue worktree.
This pattern does not require a new Issue for every agent session or experiment.

### Setup

1. Run `forge-init.sh` on the project
2. Install this skill in the project (via `npx skills add` or symlinks)

### Workflow

```
Human: "Work on issue #42"
Agent:
  1. bash scripts/forge-worktree.sh start 42
  2. cd .worktrees/issue-42/
  3. (implement the feature)
  4. git add -A && git commit -m "feat: add OAuth support"
  5. bash scripts/forge-worktree.sh finish 42
```

The agent creates the branch, works in isolation, and opens the PR — all
from a single prompt.

### Parallel agents

Launch multiple Cursor agent sessions (or background agents), each
targeting a different issue:

```
Session 1: "Work on issue #42 using a worktree"
Session 2: "Work on issue #38 using a worktree"
```

Each gets its own worktree and branch. No file conflicts.

## Pattern 2: Claude Code with --worktree

Claude Code's native `--worktree` flag creates worktrees automatically.
Combine with issue-driven naming:

```bash
# Start a Claude Code session for issue #42
claude --worktree issue-42-add-oauth
```

Then inside the session:

```
Human: "Implement issue #42. Use forge-worktree.sh finish 42 when done."
```

The worktree is at `.claude/worktrees/worktree-issue-42-add-oauth/`.
Note this is a different path from `forge-worktree.sh`'s `.worktrees/`
default — both work, but be consistent within a project.

## Pattern 3: GitHub Copilot Coding Agent (Issues)

GitHub's Copilot coding agent can be triggered by assigning Copilot to an
issue. The agent creates a PR automatically.

### Setup

1. Enable Copilot coding agent in repo settings
2. Use the `agent-task` label to flag issues for Copilot

### Workflow

```bash
# Create an issue tagged for agent work
bash scripts/forge-issue.sh create \
  --title "Add input validation to /api/users" \
  --body "Validate email format and password length..." \
  --label "agent-task" --assignee "@copilot"
```

Copilot picks up the issue and opens a PR. You review the PR.

### Combining with local agents

Use Copilot for straightforward issues and local agents (Cursor, Claude
Code) for complex ones that need iterative work:

- `agent-task` label → Copilot handles it
- No `agent-task` label → human or local agent handles it

## Pattern 4: GitHub Actions trigger on issue events

Create a workflow that runs when issues are labeled:

```yaml
# .github/workflows/agent-dispatch.yml
name: Agent Dispatch
on:
  issues:
    types: [labeled]

jobs:
  dispatch:
    if: github.event.label.name == 'agent-task'
    runs-on: ubuntu-latest
    steps:
      - name: Notify
        run: |
          echo "Issue #${{ github.event.issue.number }}: ${{ github.event.issue.title }}"
          echo "Ready for agent implementation"
          # Add your agent trigger here (webhook, API call, etc.)
```

This is a hook point — the actual agent invocation depends on your setup
(self-hosted runner with Claude Code, API call to a cloud agent, etc.).

## Pattern 5: Progress reporting in issue comments

For long-running agent tasks, post progress updates to the issue:

```bash
# At the start of work
bash scripts/forge-issue.sh comment 42 \
  --body "🤖 Agent started working on this issue.

**Plan:**
1. Add API endpoint for OAuth callback
2. Implement token refresh logic
3. Add integration tests
4. Update API documentation"

# Mid-way progress
bash scripts/forge-issue.sh comment 42 \
  --body "🤖 Progress update:
- [x] API endpoint added
- [x] Token refresh implemented
- [ ] Integration tests (in progress)
- [ ] API docs"

# On completion
bash scripts/forge-issue.sh comment 42 \
  --body "🤖 Implementation complete. PR #55 is ready for review."
```

This creates a visible trail on the issue, useful for async collaboration.

## Pattern 6: Agent checks issues for work

Teach the agent to proactively check for assigned issues:

```
Human: "What should I work on?"
Agent:
  1. bash scripts/forge-issue.sh list --assignee @me --json
  2. (parse results, present prioritized list)
  3. "You have 3 open issues assigned to you:
     - #42 [P1] Fix login redirect (type/bug)
     - #38 [P2] Add pagination (type/feature)
     - #51 [P3] Update docs (type/chore)
     Shall I start on #42?"
```

## Recommended agent contract snippet

The `forge-init.sh` script appends this to `AGENTS.md`. If you need to
add it manually:

```markdown
<!-- forge-native-dev:guidance -->
### Issue-driven workflow

This project uses GitHub/GitLab Issues as the canonical backlog.

- Default to local conversation/diff for bounded work; preserve reusable
  findings in local notes. Research or another session alone does not need a ticket.
- Reuse/create an Issue only for an explicit request or outstanding work needing
  durable backlog, ownership, blocker, or dependency tracking.
- Use Discussions only for open questions needing ongoing shared input. Do not
  automatically create both surfaces, or backfill tickets for completed small work.
- To work on an existing issue: `bash scripts/forge-worktree.sh start <number>`
- For lightweight work, a normal branch/worktree and direct PR need no Issue.
- To publish issue work when authorized: `bash scripts/forge-worktree.sh finish <number>`
- To clean up: `bash scripts/forge-cleanup.sh`
- To check what's assigned: `bash scripts/forge-issue.sh list --assignee @me`
- Post meaningful milestones/blockers to the existing issue, not every experiment.
- PRs are review gates; link an Issue when there is one.
<!-- forge-native-dev:guidance (end) -->
```

## Anti-patterns

- **Don't create issues AND TODO.md entries for the same item.** Pick one
  system per project.
- **Keep required review gates.** Follow the repository's review policy; a
  lightweight tracking path does not waive required PR review. Conversely, a
  directly requested PR does not need a prerequisite Issue.
- **Don't create one record per agent or phase.** A small experiment or local
  subtask can stay under an existing Issue without another Issue/Discussion.
- **Don't assign all issues to the agent at once.** Work in small batches
  to maintain review quality.
- **Don't let agent branches accumulate.** Run `forge-cleanup.sh`
  regularly (or after each merge).
