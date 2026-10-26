# Issue-Driven Workflow

## The thesis: "Issue is the new PR"

In traditional development, a PR is the unit of work: you write code, open a
PR, describe what you did, request review, and merge. The issue (if one
exists) is an afterthought — a cross-reference at best.

With AI coding agents, this inverts. Creating a PR is near-zero cost — an
agent can implement an issue and open a PR in minutes. The human's job
shifts from *writing code and describing it in a PR* to:

1. **Describing intent** clearly in an issue
2. **Reviewing** the agent's work in the PR

The issue becomes the primary artifact — where intent is recorded,
discussed, refined, and referenced. The PR becomes a mechanical review
gate: a diff to approve or reject.

### References

- [Sindre Sorhus on "issue is the new PR"](https://x.com/sindresorhus/status/2105693826690298314)
  and [follow-up](https://x.com/sindresorhus/status/2105720399266984369)
- [lazygit #1147 — Show which branches have unmerged changes](https://github.com/jesseduffield/lazygit/issues/1147)
  (the branch-cleanup visibility problem this workflow solves)

## Why Issues over local files?

| Dimension | Local files (TODO.md) | Forge Issues |
|---|---|---|
| Portability | Any clone has the backlog | Requires forge access |
| Collaboration | Edit conflicts on shared TODO.md | Native commenting, assignment, @-mentions |
| Cross-referencing | Manual `→ [link]()` syntax | Auto-linked from commits, PRs, other issues |
| Labeling/filtering | Grep + section headers | Native labels, milestones, projects |
| Notifications | None | Email, mobile, integrations |
| Agent access | Read file | `gh issue list`, `glab issue list` |
| Visualization | `todo-kanban.sh` | GitHub Projects, GitLab Boards |

Neither is strictly better. Use Issues when you want the collaboration
features; use local files when portability and grep-ability matter more.
This skill takes the Issues-first stance.

## Practical patterns

### Solo dev with agents

1. Capture ideas as Issues (labeled `backlog`)
2. When ready, assign an issue and let an agent work on it via worktree
3. Agent opens PR, you review
4. Merge, cleanup, repeat

The backlog is always visible on the forge. You never lose track of ideas
because they're buried in a file you forgot to grep.

### Solo dev, multiple agents in parallel

1. Open N issues for different features/fixes
2. Each agent claims an issue via `forge-worktree.sh --agent start <N>`
3. Each agent works in isolation (separate worktree + branch)
4. PRs appear as they finish — review at your pace
5. `forge-cleanup.sh` sweeps up after merges

### Team collaboration

Issues become the shared language. Anyone can:
- File an issue (with templates guiding what to include)
- Discuss trade-offs in issue comments or Discussions
- Assign work to humans or agents
- Review PRs linked to issues
- Track progress via Projects/Boards

### Migration from TODO.md

If you have an existing `project-knowledge-harness` setup:

1. For each active `TODO.md` item, create an Issue with matching labels
2. For `backlog/*.md` research docs, either:
   - Create a Discussion linking to the doc (keep docs in-repo)
   - Paste content into issue body (if short enough)
3. Keep `pitfalls/` in-repo — they need grep-ability
4. Remove the PKH agent-guidance block from `AGENTS.md`
5. Run `forge-init.sh` to set up the forge-native workflow

## When to stick with local files

- Private repos where you don't want to expose backlog publicly
- Repos without a forge remote (pure local development)
- Projects where grep-ability of TODO items is critical
- When working offline frequently

## The lifecycle in detail

```
  ┌─────────┐     ┌─────────┐     ┌───────────┐     ┌─────────┐
  │  Issue   │────>│  Branch  │────>│  Worktree  │────>│  Work   │
  │ (intent) │     │ (named)  │     │ (isolated) │     │(commits)│
  └─────────┘     └─────────┘     └───────────┘     └────┬────┘
                                                          │
  ┌─────────┐     ┌─────────┐     ┌───────────┐          │
  │ Cleanup  │<────│  Merge   │<────│    PR     │<─────────┘
  │(auto)    │     │ (gate)   │     │ (review)  │
  └─────────┘     └─────────┘     └───────────┘
```

Each step has a script. The agent (or human) drives the lifecycle forward;
the scripts handle the forge interaction and git plumbing.
