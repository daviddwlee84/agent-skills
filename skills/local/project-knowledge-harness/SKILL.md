---
name: project-knowledge-harness
description: Set up a structured project memory for any software project — TODO.md as a priority-section/effort-tagged index of future work, backlog/ for resume-friendly research/design notes on P? items, pitfalls/ as a symptom-grep-able knowledge base of past traps, plus a bundled `scripts/todo-kanban.sh` validator/renderer so agents can keep the TODO format machine-readable after install.
---

# project-knowledge-harness

A lightweight, file-based memory harness for any software project. Two
orthogonal time directions, one consistent format:

- **Future** — `TODO.md` (index) + `backlog/` (deep research) for ideas you
  might do later, paused spikes, design trade-offs
- **Past** — `pitfalls/` for traps you've already debugged, so the next time
  the same symptom shows up you grep the error message and land on the root
  cause + workaround instead of re-debugging from scratch

Goal: stop letting valuable investigation evaporate from chat history, and
prevent the graveyard of `ROADMAP.md` / `IDEAS.md` / `BACKLOG.md` /
`WISHLIST.md` / `LESSONS.md` files that nobody maintains.

## When to use this skill

Trigger this skill when the user expresses any of:

**Future-direction signals (TODO + backlog):**

- "I have a long-term TODO list, where should it go?"
- "Can we have somewhere to record ideas we might do later?"
- "Need a place for low-priority / high-effort ideas to live"
- A `TODO.md` exists but is structurally messy (no priority, mixed formats,
  stale entries) and the user asks for organisation

**Past-direction signals (pitfalls):**

- "I keep solving the same problem twice — can we save the investigation?"
- "I want to record this troubleshooting before I forget"
- "踩過的坑 / 避免重複犯錯 / lessons learned"
- "Where should this `TROUBLESHOOTING.md` content live?"
- A repo has scattered "Common issues" / "Known limitations" sections in
  multiple `docs/` files and the user wants them consolidated

**Either direction:**

- User asks "is there a place for X?" where X is non-feature, non-current
  documentation (i.e., metadata about decisions or history)

Do NOT use this skill for:

- Active sprint/iteration planning (use issue trackers, not files)
- Per-session agent scratchpad notes (those belong in `.claude/plans/` or
  similar ephemeral locations)
- Project-level documentation of *current* features (that's `docs/`)

## Core design

Three surfaces, sharply separated by **time direction** and **access pattern**:

| Surface | Time | Question it answers | Access pattern |
|---|---|---|---|
| `TODO.md` | Future | "What might we do later?" | Read top to bottom (priority sections) |
| `backlog/<slug>.md` | Future | "What was the analysis behind this idea?" | Indexed from `TODO.md` |
| `pitfalls/<slug>.md` | **Past** | **"I see error X — has this happened before?"** | **Grep symptom keywords** |

Plus, in projects that already have agent contracts:

| Surface | Time | Question it answers |
|---|---|---|
| `AGENTS.md` Hard invariants | Present | "What rules MUST agents follow?" |

Pitfalls *graduate* to Hard invariants when serious enough (see "Upgrade path"
below).

### `TODO.md` — the future-work index

- One-line entries with two tags: **priority** + **effort**
- Entries grouped by exact priority section headings:
  `## P1`, `## P2`, `## P3`, `## P?`, `## Done`
- Each entry can link to a corresponding `backlog/<slug>.md` for details
- A `## Done` section preserves recently shipped items (proves the backlog is
  alive; prune into a changelog once prior-year items appear or the section
  grows past ~20 entries)
- Recommended exact syntax:
  - Active items in `P1` / `P2` / `P3`:
    `- [ ] **[M] Title** — description` where the effort is one of `S`, `M`,
    `L`, or `XL`
  - Active items in `P?`:
    `- [ ] **[?/L] Title** — description` where the effort is one of `S`, `M`,
    `L`, or `XL`
  - Shipped items in `Done`:
    `- ✅ [YYYY-MM-DD] [P#/Effort] Title — one-line shipped summary`

### `backlog/` — future-work knowledge base

- One markdown file per non-trivial future item, named with a slug matching
  the TODO entry
- **Context-first** structure (Context → Investigation → Options → Decision)
- Lives at repo root (`backlog/`), not under `docs/` — `docs/` is for users,
  `backlog/` is maintainer-facing speculation
- Contains an indexed `README.md` listing every backlog doc

### `pitfalls/` — past-trap knowledge base

- One markdown file per debugged trap, named by **symptom** (not root cause —
  you'll search by what you're seeing, not by what you eventually learned)
- **Symptom-first** structure (Symptom → Root cause → Workaround → Prevention)
- Verbatim error messages — never paraphrase, it kills grep-ability
- Lives at repo root (`pitfalls/`), parallel to `backlog/`
- Contains an indexed `README.md` with a "Cross-referenced pitfalls" table
  pointing to traps documented elsewhere (avoids duplication)

### `scripts/todo-kanban.sh` — bundled validator + board view

- Bundled helper script that ships with this skill when installed
- Validates `TODO.md` heading order and item syntax before rendering a board
- Gives humans and agents a single command to confirm the file is still
  machine-readable after edits
- Should stay compatible with macOS system Bash 3.2 (avoid associative arrays)

### Deployment exclusion

All three surfaces are repo metadata for maintainers, NOT files to ship to
users. Exclude from any deployment/packaging mechanism:

- chezmoi: `TODO.md` `backlog/**` `pitfalls/**` in `.chezmoiignore.tmpl`
- Python package: `recursive-exclude backlog *` etc. in `MANIFEST.in`
- npm package: in `package.json` `files` exclusion or `.npmignore`
- Docker: in `.dockerignore`
- Generic: confirm `.gitignore` does NOT ignore them (they should be tracked)

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
An item in `## P3` with `[S]` effort is "small enough to slip into any free moment".
An item in `## P1` with `[XL]` effort warns "you said this is urgent but it's actually huge — re-scope".

## When a TODO entry needs a `backlog/<slug>.md` companion

Add a backlog doc when **any** apply:

- `P?` priority (record what was tried so it doesn't need re-investigation)
- Captures paused troubleshooting **that you intend to fix later**
  (preserve error trace + root-cause analysis before context evaporates)
- Multiple options were considered (record trade-offs, not only the winner)
- `L` or `XL` effort (architectural; needs design before code)

`S` items rarely need a backlog doc — a file path in the TODO line is usually
enough.

## When a debugging session needs a `pitfalls/<slug>.md`

Add a pitfall doc when you've spent more than ~15 minutes on something that
wasn't googleable, AND any of:

- The symptom is non-obvious from the root cause (silent state, weird side
  effect, behaviour change without error)
- The fix is "do nothing different but in a specific order" (sentinel writes
  must come after process completion, etc.)
- The same trap could be hit by a new agent / new machine / new contributor
- An upstream bug exists with no ETA — workaround needs to outlive memory
- A specific tool version is required or forbidden, and failure at the wrong
  version is silent / confusing

Skip a pitfall doc when:

- Trivially googleable (next person solves in 30 seconds)
- Already covered as part of normal config docs in `docs/<tool>.md` —
  cross-link from `pitfalls/README.md`'s "Cross-referenced pitfalls" table
  instead of duplicating
- Already a Hard invariant in `AGENTS.md` — those have higher enforcement
  (cross-link only)
- One-off transient (network glitch, machine-specific config rot)

### Pitfall vs backlog vs TODO entry — disambiguation

| Situation | Goes in |
|---|---|
| "We hit X, debugged it, applied workaround, moving on" | `pitfalls/` |
| "We hit X, debugged it, but the real fix is queued" | `pitfalls/` (capture trace) AND `TODO.md` (queue the fix) — link both ways |
| "We thought about doing X but deferred" | `TODO.md` (P2/P3) |
| "We thought about doing X, did a 2-day spike, deferred" | `TODO.md` (P?) + `backlog/` |
| "X is a rule everyone must follow forever" | `AGENTS.md` Hard invariant |

### Upgrade path: pitfall → Hard invariant

A pitfall **graduates** to a Hard invariant in `AGENTS.md` (or the project's
agent contract file) when:

- It recurs across machines / agents / sessions despite being documented
- The trap silently corrupts state (no error message, just wrong behaviour)
- The workaround is non-obvious enough that "remember to do X" is unsafe

When graduating:

1. Add the rule to `AGENTS.md` Hard invariants section
2. Link from the invariant back to `pitfalls/<slug>.md` for context
3. Leave the pitfall doc as historical record (don't delete — it explains
   *why* the invariant exists)

## Standard workflow

When the user agrees to set this up in a fresh project:

1. **Create or rewrite `TODO.md`** at repo root using the template in
   `assets/TODO.md.template`.
2. **Create `backlog/` folder** with `backlog/README.md` (template at
   `assets/backlog-README.md.template`).
3. **Create `pitfalls/` folder** with `pitfalls/README.md` (template at
   `assets/pitfalls-README.md.template`).
4. **Use the bundled `scripts/todo-kanban.sh`** from this skill to validate
   the target repo's `TODO.md` after editing it. Run the script from the target
   repo root, or pass an explicit path to `TODO.md`.
5. **Add ignore rules** so `backlog/` and `pitfalls/` don't ship with the project:
   - chezmoi: `backlog/**` `pitfalls/**` in `.chezmoiignore.tmpl`
   - Python package: `recursive-exclude backlog *` etc. in `MANIFEST.in`
   - npm package: in `package.json` `files` exclusion or `.npmignore`
   - Docker: in `.dockerignore`
   - Generic: confirm `.gitignore` does NOT ignore them (we want them tracked!)
6. **Add agent guidance** to project's agent contract file
   (`AGENTS.md` / `CLAUDE.md` / `.cursorrules` / `.opencode/AGENTS.md`):
   tell future agent sessions to use this harness rather than spawn parallel
   files. Template snippet at `assets/agent-guidance.md.template`.
7. **Add a Roadmap & lessons section to `README.md`** — short, links to both
   `TODO.md` and `pitfalls/`. Template at `assets/readme-roadmap.md.template`.
8. **Migrate existing TODO content** if any — categorise into P1/P2/P3/P?,
   tag effort, mark shipped items as `## Done`.
9. **Seed at least one doc each** in `backlog/` and `pitfalls/` from real
   topics — sets the tone and proves the system works. Don't bulk-migrate
   scattered historical pitfalls; index them in `pitfalls/README.md`'s
   "Cross-referenced pitfalls" table instead, and only physically move them
   if their original location stops being a natural reading flow.

## What to do mid-conversation when the user surfaces a "maybe later" idea

Recognise the signals: "maybe later", "nice to have", "if I'm interested",
"工程量太大需要再評估", "先記下來", "not now but…", "could be useful someday".

Then:

1. Check if `TODO.md` + `backlog/` already exist. If not, suggest setting up
   the harness (this skill).
2. If they exist, add the entry to the right priority section with the
   appropriate effort tag (`[S]` / `[M]` / `[L]` / `[XL]`, or `[?/...]` in `P?`).
3. If the conversation produced meaningful investigation (research, error
   traces, options analysis), create a `backlog/<slug>.md` capturing it
   before the conversation context is lost.
4. Cross-link: TODO entry → backlog doc via `→ [research](backlog/<slug>.md)`.
5. Run this skill's bundled `scripts/todo-kanban.sh` against the target repo's
   `TODO.md` so syntax drift is caught immediately.

## What to do mid-conversation when you finish debugging something tricky

Recognise the signals: "phew, that took a while", "weird, the error didn't
say anything about X", "this is the third time we've hit this", or you find
yourself reconstructing context that isn't in any doc.

Then:

1. Check if `pitfalls/` exists. If not, suggest setting up the harness.
2. Create `pitfalls/<symptom-slug>.md` immediately while the trace is fresh —
   verbatim error message, root cause, workaround, prevention. Don't wait
   until "later" — the verbatim error degrades within minutes of context shift.
3. If the trap is severe (silent corruption / cross-machine recurrence /
   non-obvious workaround), surface it to the user: "should this graduate
   to a Hard invariant in AGENTS.md?"

## What to do when implementing a backlog item

Same commit:

1. Move the TODO entry to `## Done` using
   `- ✅ [YYYY-MM-DD] [P#/Effort] Title — one-line shipped summary`.
2. Update `backlog/<slug>.md` `Status: shipped` (don't delete — historical
   record may inform adjacent decisions).
3. If shipping reveals new follow-ups, add them as fresh TODO entries
   (linking back if related).
4. If shipping uncovered a trap that bit you during implementation, write
   a `pitfalls/<slug>.md` for it — don't let it evaporate.
5. Run this skill's bundled `scripts/todo-kanban.sh` before finishing so the
   updated `TODO.md` is still parseable.

## Anti-patterns to avoid

- **Spawning new files** like `IDEAS.md`, `ROADMAP.md`, `WISHLIST.md`,
  `FUTURE.md`, `BACKLOG.md`, `LESSONS.md`, `TROUBLESHOOTING.md`,
  `GOTCHAS.md` alongside `TODO.md` / `backlog/` / `pitfalls/`. Three
  surfaces, always.
- **Backlog or pitfall docs in `docs/`**. `docs/` is user-facing reference;
  these folders are maintainer-facing memory. Mixing them confuses readers.
- **Pitfall docs titled by root cause** (e.g. `tmux-update-environment.md`)
  instead of symptom (e.g. `tmux-pane-loses-ssh-connection-var.md`). You'll
  search by what you're seeing, not by what you eventually learned.
- **Paraphrasing error messages** in pitfall docs. Copy-paste the full
  error including stack/codes — paraphrasing throws away the searchable bits.
- **Backlog or pitfall docs without dates**. A 6-month-old "we decided X"
  without a date loses meaning — re-validate or treat as stale.
- **Bulk-migrating scattered historical pitfalls** into `pitfalls/` on day
  one. High risk of broken cross-links + lost context. Index them in the
  README's cross-reference table; physically migrate only when natural.
- **Auto-redacting `backlog/` or `pitfalls/`** the way agent scratchpads
  are redacted. These are first-class docs you write deliberately; treat
  them like any other doc for secret review.
- **TODO heading drift or free-form item syntax** after adopting the validator.
  Keep the exact section order and item forms that this skill's
  `scripts/todo-kanban.sh` validates, or update the validator and the
  documented format in the same change.
- **Letting `## Done` grow unbounded**. Prune into a `CHANGELOG.md` or similar
  once prior-year items appear or the section grows past ~20 entries, keeping
  recent entries for context.

## Templates

See the `assets/` folder in this skill for:

- `TODO.md.template` — full TODO.md skeleton with priority sections
- `backlog-README.md.template` — `backlog/` index + when-to-add-doc rules
- `backlog-doc.md.template` — single backlog doc (context-first structure)
- `pitfalls-README.md.template` — `pitfalls/` index + when-to-add-doc rules + cross-reference table for traps in other locations
- `pitfall-doc.md.template` — single pitfall doc (symptom-first structure)
- `agent-guidance.md.template` — snippet for `AGENTS.md` / `CLAUDE.md`, covers all three surfaces + upgrade-to-invariant path
- `readme-roadmap.md.template` — snippet for project `README.md`, covers both forward (TODO/backlog) and backward (pitfalls) directions
- `scripts/todo-kanban.sh` — bundled validator + Markdown kanban renderer for target-project `TODO.md`

## Reference implementation

A live example of this harness is in
[`daviddwlee84/dotfiles`](https://github.com/daviddwlee84/dotfiles) — see:

- `TODO.md` — priority-section/effort-tagged future work
- `backlog/README.md` + entries — design notes and paused investigation
- `pitfalls/README.md` + entries — debugged traps with symptom-first titles
- `scripts/todo-kanban.sh` — strict `TODO.md` validator + kanban-style board
- `AGENTS.md` `### Long-term backlog → TODO.md + backlog/` and
  `### Past pitfalls → pitfalls/` sections — agent-facing guidance
- `README.md` `## Roadmap & lessons learned` section — user-facing discoverability
