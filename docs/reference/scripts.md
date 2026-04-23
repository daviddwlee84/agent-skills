# Bundled scripts

Every script in this repo's [`scripts/`](https://github.com/daviddwlee84/agent-skills/tree/main/scripts)
directory is also bundled inside the skill that owns it (so the package
shipped via `npx skills` stays self-contained). The pair must stay
byte-identical — see [Conventions](../conventions.md).

Scripts are written in **Bash 3.2** so they run on stock macOS without
homebrew bash.

## Vendor system

### `add-vendor.sh`

```bash
./scripts/add-vendor.sh owner/repo/path/to/skill
./scripts/add-vendor.sh https://github.com/owner/repo/tree/branch/path/to/skill
./scripts/add-vendor.sh --name custom --branch dev owner/repo/skills/some-skill
./scripts/add-vendor.sh --no-sync owner/repo/path/to/skill
```

Verifies the upstream path exists via `gh api`, deduplicates against
existing entries in [`vendor.yaml`](https://github.com/daviddwlee84/agent-skills/blob/main/vendor.yaml),
appends the new entry, and triggers `sync-vendor.sh` (skip with
`--no-sync`).

**Dependencies:** `gh` (authenticated) and `yq`.

### `sync-vendor.sh`

```bash
./scripts/sync-vendor.sh           # download all vendored skills
./scripts/sync-vendor.sh --check   # dry-run: report which entries have new upstream commits
```

Iterates `vendor.yaml`, downloads each skill via the GitHub trees API,
and updates `last_sync.{date,commit}` on success. `--check` prints what
would change without writing.

## Project memory

These ship with [`project-knowledge-harness`](../skills/project-knowledge-harness.md);
the canonical copies live at
[`skills/local/project-knowledge-harness/scripts/`](https://github.com/daviddwlee84/agent-skills/tree/main/skills/local/project-knowledge-harness/scripts).

### `todo-kanban.sh`

```bash
./scripts/todo-kanban.sh                    # default: TODO.md, Markdown board
./scripts/todo-kanban.sh path/to/TODO.md    # explicit file
./scripts/todo-kanban.sh --validate-only    # exit code only, no rendering
./scripts/todo-kanban.sh --json             # machine-readable lane summary
```

Validates the [TODO format](todo-format.md) and renders a kanban-style
board to stdout. Anything that's not a top-level `- [ ]` / `- ✅` item is
ignored, so you can sprinkle prose under section headings.

Exit codes: `0` valid; `1` validation failure (line number printed to
stderr); `2` usage error.

### `add-todo.sh`

```bash
./scripts/add-todo.sh \
  --priority P3 \
  --effort M \
  --title "Add docs versioning" \
  --description "Use mike for versioned docs"

./scripts/add-todo.sh \
  --priority "P?" \
  --effort "?" \
  --title "Try Rspress for docs" \
  --description "Evaluate AI-native docs framework alternative"

./scripts/add-todo.sh \
  --priority P2 --effort L \
  --title "Migrate kanban to Python" \
  --description "Bash 3.2 compat is getting expensive" \
  --backlog
```

Inserts a canonically-formatted entry into the matching `## P*` lane. With
`--backlog`, also scaffolds `backlog/<slug>.md` from the skill's template
and appends ` → [research](backlog/<slug>.md)` to the new line.

After writing, re-runs the validator. If validation fails, the original
`TODO.md` is restored.

Flags:

- `--priority {P1|P2|P3|P?}` — required.
- `--effort {S|M|L|XL|?}` — required. `?` is only valid with `P?`.
- `--title TEXT` — required. Must not contain `*`.
- `--description TEXT` — required. Free-form after the em-dash.
- `--backlog` — also create the backlog research doc.
- `--file PATH` — TODO file (default `TODO.md`).
- `--dry-run` — print the rewritten file to stdout instead of mutating.

### `promote-todo.sh`

```bash
./scripts/promote-todo.sh \
  --title "<substring of the item's title>" \
  --summary "<one-line shipped summary>"
```

Atomically moves an active item from its lane into `## Done` with the
dated `Done` syntax, then re-validates. Refuses to run if the substring
matches zero or more than one active item — refine the substring.

Flags:

- `--title SUBSTRING` — required. Case-sensitive substring of the title.
- `--summary TEXT` — required.
- `--file PATH` — TODO file (default `TODO.md`).
- `--date YYYY-MM-DD` — override completion date (default: today, UTC).
- `--dry-run` — print to stdout, don't modify.
- `--validator PATH` — override validator path (default: sibling `todo-kanban.sh`).

### `sweep-inbox.sh`

```bash
./scripts/sweep-inbox.sh                # interactive triage of backlog/inbox.md
./scripts/sweep-inbox.sh --dry-run      # preview without modifying inbox or TODO
./scripts/sweep-inbox.sh --batch        # non-interactive: skip lines that need a prompt
```

Reads [`backlog/inbox.md`](https://github.com/daviddwlee84/agent-skills/tree/main/backlog)
line by line. For each non-empty, non-comment line it prompts for the
priority / effort / formal title / description (defaulting where
possible), calls `add-todo.sh`, and removes the line from the inbox once
the entry is committed.

`--batch` is intended for agent workflows: lines whose `priority:` /
`effort:` / `title:` / `description:` are inferable get formalized
automatically; ambiguous ones are left in the inbox for the next
interactive sweep.

Inbox-line conventions (all optional; loose lines are also accepted):

```text
# Comments and blank lines are ignored.
- maybe add docs versioning with mike
- priority=P3 effort=M title="Add docs versioning" desc="Use mike for versioned docs"
- the find-skills bootstrap UX is rough
```

The first form requires interactive prompting. The second form is fully
parseable and works in `--batch` mode.

### `init.sh`

Lives only inside the skill (not mirrored to top-level `scripts/`):
[`skills/local/project-knowledge-harness/scripts/init.sh`](https://github.com/daviddwlee84/agent-skills/blob/main/skills/local/project-knowledge-harness/scripts/init.sh).

```bash
skills/local/project-knowledge-harness/scripts/init.sh \
  --target /path/to/project \
  --project-name "My Project" \
  --deployment chezmoi   # or npm | pip | docker | none
```

One-shot setup of `TODO.md` + `backlog/` + `pitfalls/` + agent guidance
snippet + README snippet for any target repo. Idempotent. See
[`project-knowledge-harness`](../skills/project-knowledge-harness.md) for
the full flag list.
