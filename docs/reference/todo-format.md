# TODO format

This page documents the exact grammar that
[`scripts/todo-kanban.sh`](scripts.md#todo-kanbansh) validates. It applies
to this repo's own [`TODO.md`](https://github.com/daviddwlee84/agent-skills/blob/main/TODO.md)
and to any project that has run
[`project-knowledge-harness`'s `init.sh`](../skills/project-knowledge-harness.md).

## File-level structure

1. The first non-empty heading **must** be `# TODO`.
2. Sections **must** appear in this order:
   `## P1`, `## P2`, `## P3`, `## P?`, `## Done`.
3. After `## Done`, additional `## ...` headings are allowed (e.g. a
   `## Notes` section, a prune log). The validator stops checking item
   format at that point.
4. Anything that is **not** a top-level `- [ ]` / `- ✅` item — prose
   paragraphs, blockquotes, HTML comments, `---` rules, indented
   sub-bullets — is ignored. You can write inline guidance under each
   section heading without breaking validation.

## Item-level grammar

| Lane | Format |
|---|---|
| `P1` / `P2` / `P3` | `- [ ] **[Effort] Title** — description` |
| `P?` | `- [ ] **[?/Effort] Title** — description` |
| `Done` | `- ✅ [YYYY-MM-DD] [P#/Effort] Title — summary` |

Where:

- **Effort** is one of `S`, `M`, `L`, `XL`. For `P?` items where effort
  is also unknown, use `[?/?]`.
- **Title** must not contain `*` (the validator uses the closing `**` as
  a delimiter).
- **Description / summary** can be free text after the em-dash
  (`—`, U+2014). Plain hyphens (`-`) are not accepted.
- Active items may end with ` → [research](backlog/<slug>.md)` to link
  the index entry to a `backlog/` doc.
- `Done` items use a date in `YYYY-MM-DD` format. UTC by convention; the
  promote script uses `date -u +%Y-%m-%d`.

## Examples

```markdown
## P1

- [ ] **[S] Wire up GitHub Pages** — first deploy of the docs site

## P2

- [ ] **[L] Migrate kanban to Python** — Bash 3.2 compat is getting expensive → [research](backlog/kanban-python.md)

## P?

- [ ] **[?/M] Try Rspress for docs** — evaluate AI-native docs framework alternative
- [ ] **[?/?] Skill-set lint** — vague idea, needs scoping

## Done

- ✅ [2026-04-23] [P1/M] Restructure project-knowledge-harness — looser validator, init/promote scripts, references/ progressive disclosure
```

## Tools that depend on this format

- [`scripts/todo-kanban.sh`](scripts.md#todo-kanbansh) — validator and
  Markdown / JSON board renderer.
- [`scripts/promote-todo.sh`](scripts.md#promote-todosh) — atomic move
  from active lane to `## Done`.
- [`scripts/add-todo.sh`](scripts.md#add-todosh) — structured insert into
  the right lane.
- [`scripts/sweep-inbox.sh`](scripts.md#sweep-inboxsh) — formalize loose
  captures from `backlog/inbox.md` via repeated `add-todo.sh` calls.

If you find yourself wanting a syntax that isn't here, it's worth asking
whether the new shape is genuinely useful or whether it's another
`IDEAS.md` file in disguise — see
[`references/anti-patterns.md`](https://github.com/daviddwlee84/agent-skills/blob/main/skills/local/project-knowledge-harness/references/anti-patterns.md).
