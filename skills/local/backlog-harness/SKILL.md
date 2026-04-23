---
name: backlog-harness
description: Set up a structured long-term backlog for any project — TODO.md as priority/effort-tagged index plus a backlog/ folder of resume-friendly research docs for paused troubleshooting, P? evaluations, and L/XL design notes. Use when a user wants somewhere to record "maybe later" ideas, freeze troubleshooting state, or capture trade-off analysis without it evaporating in chat history.
---

# backlog-harness

A lightweight, file-based backlog harness for any software project. Lets a user
park ideas, freeze incomplete troubleshooting, and record design trade-offs in a
way that's resume-friendly months later — without spawning a graveyard of
`ROADMAP.md` / `IDEAS.md` / `BACKLOG.md` / `WISHLIST.md` files that nobody
maintains.

## When to use this skill

Trigger this skill when the user expresses any of:

- "I have a long-term TODO list, where should it go?"
- "Can we have somewhere to record ideas we might do later?"
- "I keep solving the same problem twice — can we save the investigation?"
- "I want to record this troubleshooting before I forget"
- "Need a place for low-priority / high-effort ideas to live"
- A `TODO.md` exists but is structurally messy (no priority, mixed formats,
  stale entries) and the user asks for organisation

Do NOT use this skill for:

- Active sprint/iteration planning (use issue trackers, not files)
- Per-session agent scratchpad notes (those belong in `.claude/plans/` or
  similar ephemeral locations)
- Project-level documentation of *current* features (that's `docs/`)

## Core design

Two surfaces, sharply separated:

### `TODO.md` — the index

- One-line entries with two tags: **priority** + **effort**
- Entries grouped by priority section (`## P1`, `## P2`, `## P3`, `## P?`)
- Each entry can link to a corresponding `backlog/<slug>.md` for details
- A `## Done` section preserves recently shipped items (proves the backlog is
  alive; prune yearly into a changelog if it grows large)

### `backlog/` — the knowledge base

- One markdown file per non-trivial item, named with a slug matching the TODO entry
- Lives at repo root (`backlog/`), not under `docs/` — `docs/` is for users,
  `backlog/` is repo metadata for maintainers
- Should be excluded from any deployment/packaging mechanism (e.g.,
  `.chezmoiignore`, `.dockerignore`, `MANIFEST.in`, etc. — depends on project)
- Contains an indexed `README.md` listing every backlog doc

## Tag schema

Two orthogonal axes prevent the "important but unimplementable" trap:

**Priority**:

- `P1` — likely next batch (you'd reach for this if you sat down today)
- `P2` — worth doing, no rush
- `P3` — someday / nice-to-have
- `P?` — needs evaluation first; spike before committing to priority

**Effort**:

- `S` — under an hour
- `M` — half day
- `L` — multi-day
- `XL` — architectural; design doc required before code

A `[?/L]` item carries explicit "unknown of size L" — the most honest tag.
A `[P3/S]` item is "small enough to slip into any free moment".
A `[P1/XL]` item warns "you said this is urgent but it's actually huge — re-scope".

## When a TODO entry needs a `backlog/<slug>.md` companion

Add a backlog doc when **any** apply:

- `P?` priority (record what was tried so it doesn't need re-investigation)
- Captures paused troubleshooting (preserve error trace + root-cause analysis
  before context evaporates from chat history)
- Multiple options were considered (record trade-offs, not only the winner)
- `L` or `XL` effort (architectural; needs design before code)

`S` items rarely need a backlog doc — a file path in the TODO line is usually
enough.

## Standard workflow

When the user agrees to set this up in a fresh project:

1. **Create or rewrite `TODO.md`** at repo root using the template in
   `assets/TODO.md.template`.
2. **Create `backlog/` folder** with `backlog/README.md` (template at
   `assets/backlog-README.md.template`) — explains the purpose, when to add
   docs, and indexes existing entries.
3. **Add ignore rules** so `backlog/` doesn't ship with the project:
   - chezmoi: `backlog/**` in `.chezmoiignore.tmpl`
   - Python package: `recursive-exclude backlog *` in `MANIFEST.in`
   - npm package: `"backlog"` in `package.json` `files` exclusion or `.npmignore`
   - Docker: `backlog/` in `.dockerignore`
   - Generic: confirm `.gitignore` does NOT ignore it (we want it tracked!)
4. **Add agent guidance** to project's agent contract file
   (`AGENTS.md` / `CLAUDE.md` / `.cursorrules` / `.opencode/AGENTS.md`):
   tell future agent sessions to use this harness rather than spawn parallel
   files. Template snippet at `assets/agent-guidance.md.template`.
5. **Add a Roadmap section to `README.md`** — short, links to `TODO.md`, lets
   users browsing the repo discover it. Template at `assets/readme-roadmap.md.template`.
6. **Migrate existing TODO content** if any — categorise into P1/P2/P3/P?,
   tag effort, identify which items already shipped (mark `## Done`),
   identify which deserve a backlog doc.
7. **Seed at least one backlog doc** from a real ongoing topic — sets the tone
   for the file structure and proves the system works.

## What to do mid-conversation when the user surfaces a "maybe later" idea

Recognise the signals: "maybe later", "nice to have", "if I'm interested",
"工程量太大需要再評估", "先記下來", "not now but…", "could be useful someday".

Then:

1. Check if `TODO.md` + `backlog/` already exist. If not, suggest setting up
   the harness (this skill).
2. If they exist, add the entry with appropriate `P?/S/M/L/XL` tags.
3. If the conversation produced meaningful investigation (research, error
   traces, options analysis), create a `backlog/<slug>.md` capturing it before
   the conversation context is lost.
4. Cross-link: TODO entry → backlog doc via `→ [research](backlog/<slug>.md)`.

## What to do when implementing a backlog item

Same commit:

1. Move the TODO entry to `## Done` with a one-line summary.
2. Update `backlog/<slug>.md` `Status: shipped` (don't delete — historical
   record may inform adjacent decisions).
3. If shipping reveals new follow-ups, add them as fresh TODO entries
   (linking back if related).

## Anti-patterns to avoid

- **Spawning new files** like `IDEAS.md`, `ROADMAP.md`, `WISHLIST.md`,
  `FUTURE.md`, `BACKLOG.md` alongside `TODO.md`. Single index, always.
- **Backlog docs in `docs/`**. `docs/` is user-facing reference; `backlog/`
  is maintainer-facing speculation. Mixing them confuses readers.
- **Backlog docs without dates**. A 6-month-old "we decided X" without a date
  loses meaning — re-validate or treat as stale.
- **Backlog docs that paraphrase error messages**. Copy-paste the full error
  including stack/codes — paraphrasing throws away the searchable bits.
- **Auto-redacting `backlog/`** the way agent scratchpads are redacted. These
  are first-class docs you write deliberately; treat them like any other doc
  for secret review.
- **Letting `## Done` grow unbounded**. Prune yearly into a `CHANGELOG.md` or
  similar, keeping the most recent ~10 entries for context.

## Templates

See the `assets/` folder in this skill for:

- `TODO.md.template` — full TODO.md skeleton
- `backlog-README.md.template` — backlog/ index + when-to-add-doc rules
- `backlog-doc.md.template` — single backlog doc template
- `agent-guidance.md.template` — snippet for AGENTS.md / CLAUDE.md
- `readme-roadmap.md.template` — snippet for project README

## Reference implementation

A live example of this harness is in
[`daviddwlee84/dotfiles`](https://github.com/daviddwlee84/dotfiles) — see
`TODO.md`, `backlog/README.md`, the `### Long-term backlog → TODO.md + backlog/`
section in `AGENTS.md`, and the `## Roadmap` section in `README.md`.
