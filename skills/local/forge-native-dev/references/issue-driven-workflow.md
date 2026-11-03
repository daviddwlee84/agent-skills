# Right-Sized Issue-Driven Workflow

## The thesis: shared intent, not a ticket for every action

For work that needs shared tracking, Issues record intent and PRs expose the
diff for review. This makes assignment, blockers, and asynchronous decisions
visible. It does **not** mean every agent action needs an Issue, or that research
must pass through a Discussion before implementation.

Agent-generated records are cheap to create but still cost human attention,
notifications, triage, and maintenance. The objective is useful coordination,
not a complete external log of the conversation.

Background on the issue-first approach:

- [Sindre Sorhus on "issue is the new PR"](https://x.com/sindresorhus/status/2105693826690298314)
  and [follow-up](https://x.com/sindresorhus/status/2105720399266984369)
- [lazygit #1147 — Show which branches have unmerged changes](https://github.com/jesseduffield/lazygit/issues/1147)

## First decide whether an external record is needed

Use the scope gate in `SKILL.md` before choosing an Issue or Discussion.

| Situation | Lightest sufficient record |
|---|---|
| Small fix or bounded experiment completed now | Conversation + diff, normal validation/review |
| Useful findings with no outstanding shared decision | Local research doc, e.g. `backlog/` |
| Execution context must survive another session | Local task tool or handoff note, if sufficient |
| Committed future work, shared ownership, blocker/dependency | Existing or new Issue |
| Open question that needs continuing asynchronous input | Existing or new Discussion |
| User explicitly requests a particular forge record | That record, subject to publication policy |

Neither duration nor line count is a hard threshold. A small release blocker
can need an Issue; a large solo experiment may not. "Research", "maybe later",
and "先記下來" do not themselves specify where to publish.

Before creating a warranted external record, look for a relevant existing one.
An experiment within an Issue normally updates that Issue; it does not need
another Issue plus a Discussion. Do not backfill tickets solely to document work
that is already finished.

## Issues versus local files

| Dimension | Local research / task notes | Forge Issues |
|---|---|---|
| Portability | Available from the repo or local task store | Requires forge access |
| Collaboration | Best for bounded work and durable supporting evidence | Comments, assignment, notifications |
| Traceability | Link from the diff/PR when useful | Shared owner, state, blockers, milestones |
| Overhead | No additional external lifecycle | Must triage, update, and eventually close |

Hosted-first means the **shared backlog** lives on the forge. Local research,
pitfalls and execution handoffs are compatible with it; avoid duplicating the
same actionable backlog in two competing indexes.

## Practical patterns

### Bounded solo work

1. Investigate or implement locally; use a normal branch/worktree if useful.
2. Validate and report the result.
3. Keep a local note only if the findings are worth retaining.
4. Follow the project's review policy and the user's commit/publication request.

A directly requested PR can carry a small change's rationale without an Issue.
Do not create an Issue just because `forge-worktree.sh` takes an issue number.

### Durable backlog or team coordination

1. Reuse/create an Issue with an owner or clear acceptance criteria.
2. Use the issue-linked worktree lifecycle when ready.
3. Update the Issue for meaningful milestones, blockers, or changed decisions.
4. Publish the PR when authorized, review, merge, and clean up.

For parallel agents, split into separate Issues only when work streams need
independent tracking. Local subtasks/worktrees can remain under one Issue.

## Issue versus Discussion: second-stage choice

After deciding an external record is warranted:

- **Issue:** an outstanding action, deliverable, owner, blocker, or dependency.
- **Discussion:** an unresolved question that benefits from ongoing shared
  deliberation, not merely a place to paste a research report.

### Conditional promotion

An existing Discussion can lead to an Issue when the resulting work needs its
own tracking. Reuse any existing Issue and link the decision. A small follow-up
can instead link the Discussion from its PR/diff. Do not create a Discussion
retroactively for a decision already settled in the conversation.

### Keep one primary record

Keep issue bodies concise and actionable. Detailed benchmarks and trade-offs
can remain in a local research document linked from an existing Issue or PR.
Do not mirror every document to Discussions, and do not create both surfaces
merely because a task contains research and code.

## Migrating an existing backlog

Only migrate when the user has chosen a new canonical backlog, not merely
because local notes exist alongside forge tooling.

1. Triage outstanding actionable TODO items into Issues; do not recreate
   completed work or every speculative thought as a ticket.
2. Keep `backlog/` research docs; link from a relevant Issue if needed. Create a
   Discussion only for a still-open question needing asynchronous input, not
   based on document length.
3. Keep `pitfalls/` in-repo for symptom-based lookup.
4. Replace conflicting guidance with the bootstrap template's scope gate.

Existing projects with the `forge-native-dev:guidance` sentinel are not rewritten
by `forge-init.sh`. Review and update their policy block explicitly; rerunning
init alone will not remove an old "create an Issue for every idea" rule.

## Merge and review

Default to squash-merge for one logical change per commit. Link an Issue when
there is one; issue-free PRs are valid for bounded work unless repository policy
requires otherwise. Rebase-merge fits deliberately curated commits.

Keep required review and permission gates. A lightweight tracking policy does
not authorize skipping tests, publishing unrequested content, or bypassing
required PR review. For the tracked lifecycle's commands, see `SKILL.md` and
`references/conventions.md`.
