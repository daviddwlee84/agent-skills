---
name: project-knowledge-harness
description: Set up a structured project memory for any software project — TODO.md as priority/effort-tagged index of future work, backlog/ for resume-friendly research/design notes on P? items, and pitfalls/ as a symptom-grep-able knowledge base of past traps. Use when a user wants somewhere to record "maybe later" ideas, freeze troubleshooting state, capture trade-off analysis, or stop re-debugging the same problem.
---

# project-knowledge-harness

A lightweight, file-based memory harness for any software project.

Three surfaces, sharply separated by **time direction** and **access pattern**:

| Surface | Time | Question it answers | Access pattern |
|---|---|---|---|
| `TODO.md` | Future | "What might we do later?" | Read top to bottom (priority lanes) |
| `backlog/<slug>.md` | Future | "What was the analysis behind this idea?" | Indexed from `TODO.md` |
| `pitfalls/<slug>.md` | **Past** | **"I see error X — has this happened before?"** | **Grep symptom keywords** |

Plus, in projects that already have agent contracts, `AGENTS.md` Hard
invariants answer "What rules MUST agents follow?". Pitfalls *graduate* to
Hard invariants when serious enough — see
[`references/when-to-add-docs.md`](references/when-to-add-docs.md).

## When to use this skill

Use this skill when the user surfaces any of:

- A long-term TODO list with no home, or a messy `TODO.md` that needs
  structure (signals: "where should ideas go?", "maybe later", "工程量太大需要再評估")
- A debugging session worth saving (signals: "keep solving the same problem
  twice", "save this troubleshooting", "踩過的坑", "TROUBLESHOOTING.md
  scattered across docs/")
- A request to consolidate `IDEAS.md` / `ROADMAP.md` / `WISHLIST.md` /
  `LESSONS.md` files

Do NOT use this skill for active sprint planning (use issue trackers),
ephemeral agent scratchpads (use `.claude/plans/`), or current feature
documentation (use `docs/`).

## How to apply this skill (default workflow)

The skill bundles three scripts and several templates. **Default to the
init script** rather than asking the agent to copy templates by hand.

```
scripts/
  init.sh         # one-shot setup of TODO.md + backlog/ + pitfalls/
                  # + agent guidance + README snippet
  todo-kanban.sh  # validate TODO.md format and render kanban-style board
  promote-todo.sh # move an active TODO item to ## Done with the right syntax
```

### 1. Run `scripts/init.sh` against the target repo

```sh
scripts/init.sh \
  --target /path/to/project \
  --project-name "My Project" \
  --deployment chezmoi   # or npm | pip | docker | none
```

The script:

1. Creates `TODO.md`, `backlog/README.md`, `pitfalls/README.md` from
   `assets/*.template`, substituting placeholders.
2. Appends an agent-guidance snippet to `AGENTS.md` / `CLAUDE.md` (auto-detected,
   override with `--agent-contract`).
3. Appends a "Roadmap & lessons learned" section to `README.md`.
4. Runs `scripts/todo-kanban.sh --validate-only TODO.md` so any drift is
   caught immediately.
5. Prints the deployment-exclusion lines you should add manually (it does
   not edit ignore files — see
   [`references/deployment-exclusion.md`](references/deployment-exclusion.md)).

`init.sh` is idempotent: existing files are skipped unless `--force` is
given, and snippets append only if a sentinel marker is missing.

### 2. Mid-conversation, when the user surfaces a "maybe later" idea

Signals: "maybe later", "nice to have", "if I'm interested",
"工程量太大需要再評估", "先記下來", "not now but…".

1. If `TODO.md` doesn't exist yet, run `scripts/init.sh` first.
2. Add the entry by editing `TODO.md` directly. Use the syntax from
   [`references/tag-schema.md`](references/tag-schema.md):
   - `P1` / `P2` / `P3`: `- [ ] **[Effort] Title** — description`
   - `P?`:               `- [ ] **[?/Effort] Title** — description`
3. If the conversation produced real investigation (research, error
   traces, options analysis), create `backlog/<slug>.md` from
   `assets/backlog-doc.md.template` before the context evaporates and
   add `→ [research](backlog/<slug>.md)` to the TODO line.
4. Run `scripts/todo-kanban.sh --validate-only` to catch syntax drift.

### 3. Mid-conversation, when you finish debugging something tricky

Signals: "phew, that took a while", "weird, the error didn't say anything
about X", "this is the third time we've hit this", or you find yourself
reconstructing context that isn't in any doc.

1. Create `pitfalls/<symptom-slug>.md` immediately from
   `assets/pitfall-doc.md.template`, while the trace is fresh. Title the
   doc by the **symptom**, not the root cause — you'll search by what
   you're seeing, not by what you eventually learned.
2. Copy verbatim error messages — never paraphrase, it kills grep-ability.
3. If the trap is severe (silent corruption / cross-machine recurrence /
   non-obvious workaround), surface it: "should this graduate to a Hard
   invariant in AGENTS.md?" — see
   [`references/when-to-add-docs.md`](references/when-to-add-docs.md).

### 4. When implementing a `TODO.md` item

In the same commit:

1. Run `scripts/promote-todo.sh --title "<substring>" --summary "<what shipped>"`.
   It removes the active line and inserts the dated `Done` entry, then
   re-validates. It refuses to run if the substring matches zero or more
   than one active item.
2. If a `backlog/<slug>.md` exists, set its `Status: shipped` (don't
   delete — historical record may inform adjacent decisions).
3. If shipping uncovered a trap, write a `pitfalls/<slug>.md` for it.

## When a TODO entry needs a `backlog/` doc, when a debug needs a `pitfalls/` doc

Decision rules and the upgrade path to `AGENTS.md` invariants live in
[`references/when-to-add-docs.md`](references/when-to-add-docs.md). Read it
the first time you set up the harness; consult it again whenever you're
unsure which surface a piece of knowledge belongs in.

## Tag schema

Two orthogonal axes, validated by `scripts/todo-kanban.sh`. See
[`references/tag-schema.md`](references/tag-schema.md) for the full schema,
useful tag combinations, and the exact validator-checked syntax.

## Anti-patterns

Common mistakes to avoid (e.g., spawning `IDEAS.md` alongside `TODO.md`,
titling pitfalls by root cause, paraphrasing errors). Full list in
[`references/anti-patterns.md`](references/anti-patterns.md).

## Deployment exclusion

`TODO.md`, `backlog/`, and `pitfalls/` are maintainer-facing repo metadata,
not files to ship. Cheatsheet for chezmoi / npm / pip / Docker in
[`references/deployment-exclusion.md`](references/deployment-exclusion.md).
`scripts/init.sh --deployment ...` prints the exact lines to add.

## Templates and bundled assets

- `assets/TODO.md.template` — `TODO.md` skeleton with example items per lane
- `assets/backlog-README.md.template` — `backlog/` index + when-to-add rules
- `assets/backlog-doc.md.template` — single backlog doc (context-first)
- `assets/pitfalls-README.md.template` — `pitfalls/` index + cross-reference
  table for traps documented elsewhere
- `assets/pitfall-doc.md.template` — single pitfall doc (symptom-first)
- `assets/agent-guidance.md.template` — snippet for `AGENTS.md` / `CLAUDE.md`
- `assets/readme-roadmap.md.template` — snippet for project `README.md`
- `scripts/init.sh` — one-shot setup
- `scripts/todo-kanban.sh` — validator + Markdown kanban renderer
  (also supports `--json` and `--validate-only`)
- `scripts/promote-todo.sh` — atomic active-→-Done move with re-validation

## Reference implementation

A live example of this harness is at
[`daviddwlee84/dotfiles`](https://github.com/daviddwlee84/dotfiles):

- `TODO.md`, `backlog/`, `pitfalls/` directories at repo root
- `AGENTS.md` `### Long-term backlog → TODO.md + backlog/` and
  `### Past pitfalls → pitfalls/` sections
- `README.md` `## Roadmap & lessons learned` section
