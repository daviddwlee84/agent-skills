# Bundled scripts

Every script in this repo's [`scripts/`](https://github.com/daviddwlee84/agent-skills/tree/main/scripts)
directory is also bundled inside the skill that owns it (so the package
shipped via `npx skills` stays self-contained). The pair must stay
byte-identical — see [Conventions](../conventions.md).

Shell scripts are written in **Bash 3.2** so they run on stock macOS without
homebrew bash. The MkDocs build helper is Python and runs inside the project's
uv-managed docs environment.

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

## Documentation sites

These ship with
[`mkdocs-site-bootstrap`](../skills/mkdocs-site-bootstrap.md). They are not
mirrored into the repo-wide `scripts/` directory: the build helper is copied
into each scaffolded project, while migration runs from the installed skill.

### `build-docs-site.py`

```bash
uv run python scripts/build-docs-site.py
uv run python scripts/build-docs-site.py --dry-run
uv run python scripts/build-docs-site.py --site-dir public --keep-temp
```

Canonical strict production build for scaffolded docs sites. Monolingual sites
use one pass. Multilingual sites with llmstxt build default-language output
separately from the full locale HTML site, validate and merge the artifacts, then replace
the target site directory only after both passes succeed. Root `llms.txt`,
`llms-full.txt`, and raw `.md` sidecars are default-language-only.

Flags: `--target-dir DIR`, `--config-file FILE`, `--site-dir DIR`, `--dry-run`,
`--keep-temp`. Stdout is JSON; MkDocs logs and diagnostics go to stderr. Exits:
`0` success, `2` invalid/missing input, `3` MkDocs failed, `4` output validation
failed. There is no non-strict mode. Direct `mkdocs build --strict` remains an HTML-only
preview because llmstxt is disabled by default in the scaffolded config.

### `migrate-i18n-llmstxt.sh`

```bash
bash .agents/skills/mkdocs-site-bootstrap/scripts/migrate-i18n-llmstxt.sh \
  --target-dir . --json
bash .agents/skills/mkdocs-site-bootstrap/scripts/migrate-i18n-llmstxt.sh \
  --target-dir . --apply --dry-run --json
bash .agents/skills/mkdocs-site-bootstrap/scripts/migrate-i18n-llmstxt.sh \
  --target-dir . --apply --verify --json
```

Audits by default and only writes with `--apply`. It patches recognizable
older scaffold shapes, installs/refreshes only a marker-owned build helper, and
leaves custom config/CI/Makefile shapes in `manual_actions[]`. Candidate files
are staged and validated before replacement, and the migration is idempotent.
Updating the skill merely downloads this tool; it never runs automatically.

Flags: `--target-dir DIR`, `--apply`, `--dry-run`, `--verify`, `--json`.
Important exits: `0` safe/migrated, `10` affected legacy config found during
audit/dry-run, `11` manual work remains, `12` strict verification failed. See the
canonical
[`migration guide`](https://github.com/daviddwlee84/agent-skills/blob/main/skills/local/mkdocs-site-bootstrap/references/i18n-llmstxt-migration.md).

## Skill authoring

These ship with [`skill-author`](../skills/skill-author.md); the canonical
copies live at
[`skills/local/skill-author/scripts/`](https://github.com/daviddwlee84/agent-skills/tree/main/skills/local/skill-author/scripts).
Not mirrored to top-level `scripts/` because they're agent-author tooling,
not repo-wide make targets.

### `new-skill.sh`

```bash
bash skills/local/skill-author/scripts/new-skill.sh <skill-name>
bash skills/local/skill-author/scripts/new-skill.sh --project my-skill
bash skills/local/skill-author/scripts/new-skill.sh --global my-skill
bash skills/local/skill-author/scripts/new-skill.sh --local --vendor cherry-picked
bash skills/local/skill-author/scripts/new-skill.sh --dry-run my-skill
```

Scaffolds the canonical skill directory (`SKILL.md` + `references/` +
`scripts/` + `assets/` from templates) and adds *relative* discovery
symlinks for non-universal agents. Auto-detects placement scope by walking
up from CWD; explicit flags override.

Placement scopes (see
[creating local skills](../workflows/creating-local-skills.md) for the
full table):

- **LOCAL** — publishing-repo anchor (`vendor.yaml` / `skills/local/` /
  `skills/.claude-plugin/`) found. Canonical at `<repo>/skills/local/<name>/`
  (or `skills/vendor/` with `--vendor`); symlinks for `.agents/skills/` and
  `.claude/skills/`.
- **PROJECT** — `.git` found. Canonical at `<repo>/.agents/skills/<name>/`;
  symlink for `.claude/skills/<name>` (+ any already-present non-universal
  agent dir at the repo root).
- **GLOBAL** — neither anchor, or `--global`. Canonical at
  `~/.agents/skills/<name>/`; symlinks for `~/.claude/skills/<name>` and
  any other already-present non-universal agent dir under `$HOME`.

The symlink fan-out matches `npx skills add`'s discipline: "claude-code
always, others only if their config root dir already exists at the base
dir" — never creates `.windsurf/` or similar for agents the user doesn't
actually use. Each created symlink is post-write verified with
`test -e <link>/SKILL.md`; a dangling link aborts with exit 4.

Flags:

- `--local` / `--project` / `--global` — force scope (mutually exclusive).
- `--vendor` — LOCAL only; use `skills/vendor/<name>/`.
- `--root DIR` — override walk-up start dir.
- `--no-symlinks` — skip the agent-dir fan-out.
- `--dry-run` — print every action without writing.
- `--force` — overwrite the canonical dir and replace any existing symlinks.

Output: single JSON object on stdout
(`{skill, mode, canonical, symlinks[], next_steps[]}`); prose on stderr.

Exit codes: `0` ok; `1` invalid args; `2` canonical dir already exists
(use `--force`); `3` scope precondition failed (e.g. `--project` outside
a git repo); `4` post-write symlink verification failed (the
[symlink-target-relative footgun](../reference/pitfalls.md)).

### `lint-skill.sh`

```bash
bash skills/local/skill-author/scripts/lint-skill.sh skills/local/<name>
bash skills/local/skill-author/scripts/lint-skill.sh --strict skills/local/<name>
bash skills/local/skill-author/scripts/lint-skill.sh --json   skills/local/<name>
```

Lints a skill directory for frontmatter + length, script hygiene
(shebang / +x / `--help` handler), and reference reachability. See
[`skill-author`](../skills/skill-author.md) for the full checklist.

### `lint-frontmatter.sh`

```bash
make lint-frontmatter                                  # sweep skills/
./scripts/lint-frontmatter.sh skills/local/<name>/SKILL.md
./scripts/lint-frontmatter.sh --parser node skills     # exact npx-skills parity
```

YAML-parses the frontmatter of every `SKILL.md` under the given paths and
checks that the root is a mapping with string `name` + `description`.
`lint-skill.sh` delegates to it for the single-skill case.

This exists because harnesses **silently skip** a skill whose frontmatter
does not parse — `npx skills add` prints `⚠ Skipped … YAML parse error` and
still exits `0`. The usual cause is an unquoted `description:` containing
`": "`; a ` #` in an unquoted value is worse, since it parses but truncates
the description at the comment marker (warning, not error). See
[pitfalls](../reference/pitfalls.md).

Parser is auto-detected: `yq` → PyYAML → the js `yaml` package (what
`npx skills` itself uses; force it with `--parser node`). With none
installed the script degrades to a pattern heuristic and says so.

Exit codes: `0` clean; `1` at least one file failed; `2` bad args, missing
path, or forced parser unavailable.

### `git-hooks/pre-push`

```bash
make install-hooks     # symlink it into .git/hooks/pre-push
git push --no-verify   # bypass once
rm .git/hooks/pre-push # uninstall
```

Runs `make validate` (frontmatter + `marketplace.json` + `TODO.md` format)
and aborts the push on failure, printing the tail of the output. Mirrors
[`.github/workflows/validate.yml`](https://github.com/daviddwlee84/agent-skills/blob/main/.github/workflows/validate.yml),
which runs the same three gates on push and PR — the hook just moves the
signal earlier, since a broken `SKILL.md` is invisible at install time.
