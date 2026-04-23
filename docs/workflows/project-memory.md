# Project memory workflow

This page describes how to add and maintain entries in this repo's
[`TODO.md`](https://github.com/daviddwlee84/agent-skills/blob/main/TODO.md),
[`backlog/`](https://github.com/daviddwlee84/agent-skills/tree/main/backlog),
and [`pitfalls/`](https://github.com/daviddwlee84/agent-skills/tree/main/pitfalls)
directories. The same workflow applies to any project that has run
[`project-knowledge-harness`'s `init.sh`](../skills/project-knowledge-harness.md).

## Three ways to add a TODO

| Method | Best for | Validation |
|---|---|---|
| **`scripts/add-todo.sh`** | Structured items where you know priority + effort | Enforced — refuses to write a malformed entry |
| **`backlog/inbox.md`** | Quick captures from the maintainer; "I'll triage this later" | None — formalized later by `sweep-inbox.sh` |
| **Edit `TODO.md` directly** | Bulk import; agents that are happy following the format spec | Run `make kanban` after to catch drift |

`add-todo.sh` and the inbox sweeper are bundled with the
[`project-knowledge-harness`](../skills/project-knowledge-harness.md) skill
and mirrored into the top-level [`scripts/`](../reference/scripts.md).

### Method 1 — `scripts/add-todo.sh`

```bash
./scripts/add-todo.sh \
  --priority P3 \
  --effort M \
  --title "Add docs versioning" \
  --description "Use mike for versioned docs"

# P? items use --unknown-priority; effort can also be unknown:
./scripts/add-todo.sh \
  --priority "P?" \
  --effort "?" \
  --title "Try Rspress for docs" \
  --description "Evaluate AI-native docs framework alternative"

# Add a backlog research doc at the same time
./scripts/add-todo.sh \
  --priority P2 \
  --effort L \
  --title "Migrate kanban to Python" \
  --description "Bash 3.2 compat is getting expensive" \
  --backlog
```

What it does:

1. Builds the canonical line for the chosen lane.
2. Inserts it under the matching `## P?` heading in `TODO.md`.
3. If `--backlog` is set, scaffolds `backlog/<slug>.md` from
   the skill's `assets/backlog-doc.md.template` and appends
   ` → [research](backlog/<slug>.md)` to the new TODO line.
4. Re-runs the validator. If validation fails, the original `TODO.md` is
   restored.

See [`scripts/add-todo.sh --help`](../reference/scripts.md#add-todosh) for
the full flag list.

### Method 2 — `backlog/inbox.md`

For loose captures where you don't yet know the priority or effort:

```bash
echo "- maybe add docs versioning with mike" >> backlog/inbox.md
echo "- the find-skills bootstrap UX is rough" >> backlog/inbox.md
```

Anything goes in `inbox.md` — free-form prose, dashed lists, half-thoughts.
The validator does **not** look at this file.

When you (or an agent) are ready to triage, run:

```bash
./scripts/sweep-inbox.sh
```

The sweeper reads `inbox.md` line by line, prompts for the priority /
effort / formal title / description for each one, calls `add-todo.sh`, and
removes the line from the inbox once it's been formalized. Use
`--dry-run` to preview without mutating either file.

If you're working with an agent, the easier path is to ask it: *"sweep
the inbox"* or *"clear `backlog/inbox.md`"*. The
[`project-knowledge-harness`](../skills/project-knowledge-harness.md)
SKILL.md instructs the agent to invoke `sweep-inbox.sh` and to ask the
maintainer for the missing fields one item at a time.

### Method 3 — edit `TODO.md` directly

Sometimes the fastest path. The format is small enough to memorize:

```markdown
## P2

- [ ] **[M] Title here** — description goes after the em-dash

## P?

- [ ] **[?/L] Unsure-priority item** — description
```

After editing, run `make kanban` (or `./scripts/todo-kanban.sh --validate-only`)
to catch typos before committing. The full grammar lives in
[Reference → TODO format](../reference/todo-format.md).

## Promoting a finished item

When you ship a TODO item, in the same commit:

```bash
./scripts/promote-todo.sh \
  --title "<substring of the item's title>" \
  --summary "<one-line shipped summary>"
```

This atomically moves the matched active item into `## Done` with the
dated `Done` syntax and re-validates. It refuses to run if the substring
matches zero or more than one active item, so refine the substring if it
errors out.

If a `backlog/<slug>.md` exists for the item, set its `Status: shipped`
in the same commit — don't delete it. Historical research often informs
adjacent decisions.

## When to write a `backlog/` doc

Write `backlog/<slug>.md` when the conversation produced something worth
re-reading later: research notes, design trade-offs, error traces from a
failed spike, vendor comparison tables. The TODO line is the *index*;
the backlog doc is the *content*.

A useful filter: *"if I came back to this in three months with no memory,
would the TODO line alone be enough?"* If no, write the backlog doc.

The skill's [`references/when-to-add-docs.md`](https://github.com/daviddwlee84/agent-skills/blob/main/skills/local/project-knowledge-harness/references/when-to-add-docs.md)
has the full decision tree.

## When to write a `pitfalls/` doc

Write `pitfalls/<symptom-slug>.md` immediately after debugging something
non-obvious that could plausibly happen again. The title should be the
**symptom** (what you typed into a search bar), not the root cause.

Copy verbatim error messages — never paraphrase, it kills grep-ability.

If the trap is severe (silent data corruption, cross-machine recurrence,
non-obvious workaround), graduate it to a Hard invariant in `AGENTS.md` /
`CLAUDE.md`. The pitfall doc stays as the historical record; the
invariant is the rule that prevents recurrence.
