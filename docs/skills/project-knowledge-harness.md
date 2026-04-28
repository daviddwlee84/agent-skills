# project-knowledge-harness

A lightweight, file-based memory harness that gives any software project
three sharply-separated surfaces:

| Surface | Time direction | Question it answers | Access pattern |
|---|---|---|---|
| `TODO.md` | Future | "What might we do later?" | Read top to bottom (priority lanes) |
| `backlog/<slug>.md` | Future | "What was the analysis behind this idea?" | Indexed from `TODO.md` |
| `pitfalls/<slug>.md` | **Past** | **"I see error X — has this happened before?"** | **Grep symptom keywords** |

The skill exists to stop two common failure modes: valuable investigation
evaporating from chat history, and the graveyard of `IDEAS.md` /
`ROADMAP.md` / `WISHLIST.md` / `LESSONS.md` files that nobody maintains.

## When the skill triggers

Future-direction signals: "where should ideas go?", "maybe later", "nice to
have", "工程量太大需要再評估", "先記下來".

Past-direction signals: "save this troubleshooting", "踩過的坑", scattered
"Common issues" sections across `docs/`.

Either: "is there a place for X?" where X is metadata about decisions or
history rather than current features.

## Structure of the skill itself

```
skills/local/project-knowledge-harness/
├── SKILL.md                      # ~170-line entry point; loads on activation
├── assets/                       # Copied into target projects
│   ├── TODO.md.template
│   ├── backlog-README.md.template
│   ├── backlog-doc.md.template
│   ├── pitfalls-README.md.template
│   ├── pitfall-doc.md.template
│   ├── agent-guidance.md.template   # Snippet for AGENTS.md / CLAUDE.md
│   └── readme-roadmap.md.template   # Snippet for README.md
├── scripts/                      # Executed during setup or by the agent
│   ├── init.sh                   # One-shot setup of all of the above
│   ├── todo-kanban.sh            # Validator + Markdown / JSON board renderer
│   └── promote-todo.sh           # Atomic active → ## Done move + re-validate
└── references/                   # Loaded on demand from SKILL.md links
    ├── tag-schema.md             # Priority × effort schema and exact syntax
    ├── when-to-add-docs.md       # Backlog vs pitfall vs invariant decision rules
    ├── anti-patterns.md          # Mistakes to avoid
    └── deployment-exclusion.md   # Per-mechanism ignore-rule cheatsheet
```

`SKILL.md` is intentionally short and points to `references/*.md` so the
agent only loads decision detail when it needs it
([progressive disclosure](https://agentskills.io/specification#progressive-disclosure)).

## How to apply the skill in a fresh repo

The default workflow is one command:

```sh
skills/local/project-knowledge-harness/scripts/init.sh \
  --target /path/to/project \
  --project-name "My Project" \
  --deployment chezmoi   # or npm | pip | docker | none
```

This is idempotent — re-running it skips files that already exist and
snippets whose sentinel marker is already present. Pass `--force` to
overwrite the three template files; snippets are still appended only once.

`init.sh` performs:

1. Render `TODO.md`, `backlog/README.md`, `pitfalls/README.md` from
   `assets/*.template`, substituting `<PROJECT NAME>`,
   `<DEPLOYMENT MECHANISM>`, `<IGNORE FILE>`.
2. Append the agent guidance snippet to `AGENTS.md` / `CLAUDE.md`
   (auto-detected; override with `--agent-contract`).
3. Append the "Roadmap & lessons learned" snippet to `README.md`
   (skip with `--readme ""`).
4. Run `todo-kanban.sh --validate-only TODO.md` to confirm the file is
   machine-readable.
5. Print the deployment-specific lines you should add to your ignore file.

`init.sh` deliberately does **not** edit `.gitignore` /
`.chezmoiignore.tmpl` / `.dockerignore` — the blast radius is too high
for an automated tool. Use the printed cheatsheet as your TODO.

## Bundled scripts in detail

### `scripts/todo-kanban.sh`

Validates the format and renders a kanban-style board.

```sh
scripts/todo-kanban.sh                    # default: TODO.md, Markdown board
scripts/todo-kanban.sh path/to/TODO.md    # explicit file
scripts/todo-kanban.sh --validate-only    # exit code only
scripts/todo-kanban.sh --json             # machine-readable lane summary
```

Validation rules:

- First non-empty heading must be `# TODO`.
- Sections must appear in order: `## P1`, `## P2`, `## P3`, `## P?`,
  `## Done`. Additional headings after `## Done` are allowed (e.g., a
  `## Notes` or prune log section).
- Top-level list items are validated:
  - `P1` / `P2` / `P3`: `- [ ] **[Effort] Title** — description`
  - `P?`:               `- [ ] **[?/Effort] Title** — description`
  - `Done`:             `- ✅ [YYYY-MM-DD] [P#/Effort] Title — summary`
  Effort is one of `S`, `M`, `L`, `XL`. Active items may end with
  `→ [research](backlog/<slug>.md)`.
- Anything that is **not** a top-level `- [ ]` / `- ✅` item — prose,
  blockquotes, HTML comments, `---` rules, indented sub-bullets — is
  ignored and does not count toward lane totals. This lets you write
  inline guidance under each section without breaking the validator.
- Compatible with macOS system Bash 3.2 (no associative arrays,
  no `readarray`).

### `scripts/promote-todo.sh`

Move an active item from `P1` / `P2` / `P3` / `P?` into `## Done` with
the dated `Done` syntax, then re-validate.

```sh
scripts/promote-todo.sh \
  --title "<substring of the item's title>" \
  --summary "<one-line shipped summary>"
```

Behaviour:

- Substring match against the title field (case-sensitive). Refuses to
  run if zero or multiple active items match — refine the substring.
- Inserts the new `Done` entry immediately after the `## Done` heading,
  using `date -u +%Y-%m-%d` (override with `--date YYYY-MM-DD`).
- Looks up the validator next to itself; if validation fails after the
  edit, the original file is restored.
- Use `--dry-run` to preview the rewritten file without mutating.

### `scripts/init.sh`

See the workflow above. Notable flags:

- `--agent-contract FILE` — override the auto-detected `AGENTS.md` /
  `CLAUDE.md` / `.opencode/AGENTS.md` / `.cursorrules` choice.
- `--readme ""` — skip the README snippet (useful for repos with their
  own conventions).
- `--no-validate` — skip the final `todo-kanban.sh --validate-only` pass
  (for scripted bootstraps where validation is checked separately).

## Reference docs the skill loads on demand

- [`references/tag-schema.md`](https://github.com/daviddwlee84/agent-skills/blob/main/skills/local/project-knowledge-harness/references/tag-schema.md)
  (also surfaced as a human-readable page: [Tag schema](../reference/tag-schema.md))
- [`references/when-to-add-docs.md`](https://github.com/daviddwlee84/agent-skills/blob/main/skills/local/project-knowledge-harness/references/when-to-add-docs.md)
- [`references/anti-patterns.md`](https://github.com/daviddwlee84/agent-skills/blob/main/skills/local/project-knowledge-harness/references/anti-patterns.md)
- [`references/deployment-exclusion.md`](https://github.com/daviddwlee84/agent-skills/blob/main/skills/local/project-knowledge-harness/references/deployment-exclusion.md)

## How this repo uses the skill on itself

The repo's own [`TODO.md`](https://github.com/daviddwlee84/agent-skills/blob/main/TODO.md),
[`backlog/`](https://github.com/daviddwlee84/agent-skills/tree/main/backlog) (when populated),
[`pitfalls/`](https://github.com/daviddwlee84/agent-skills/tree/main/pitfalls) (when populated),
and [`scripts/`](https://github.com/daviddwlee84/agent-skills/tree/main/scripts) `todo-kanban.sh` /
`promote-todo.sh` are a live example of the harness applied to a real
project. The [`make kanban`](https://github.com/daviddwlee84/agent-skills/blob/main/Makefile)
target wraps the validator/renderer.
