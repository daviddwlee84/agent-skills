# Plan: make project-knowledge-harness td-aware (optional, one-way bridge)

## Context

td (marcus/td, via sidecar) is being piloted, not adopted everywhere. Its store is
`.todos/issues.db` (gitignored SQLite); cross-machine needs the experimental
`td-sync` server (feature flag `sync_cli` off by default), and Project IDs are not
tied to the git remote. So td cannot be the source of truth for anything that must
survive `git clone` on another devbox.

Decision: **keep the harness independent, make its scripts td-aware.**

- Git (TODO.md / backlog/ / pitfalls/) stays the durable SoT for *intent + knowledge*.
- td, when present, is the SoT for *execution state only* (in-flight, handoff, review).
- References point **ephemeral → durable only**: a td issue names its TODO item;
  TODO.md never stores td ids (a clone elsewhere would hold dangling ids).
- Every td path is a no-op when td is absent → projects without td behave exactly as today.
- Scripts never close td issues themselves (respect td's review gate); they print hints.

This matches the ChatGPT pilot advice: td is reversible (delete `.todos/`, nothing in
git breaks), and the harness can be deprecated-proof from td's side.

## Changes (all under `skills/local/project-knowledge-harness/`)

### 1. `scripts/lib/td-bridge.sh` (new, sourced; Bash 3.2)
- `pkh_td_enabled`: mode from `PKH_TD=auto|on|off` (default `auto`). auto = `command -v td`
  AND `td info >/dev/null 2>&1` succeeds in cwd (resolves worktrees / `.td-root`). `on`
  errors if unavailable; `off` always false.
- `pkh_td_find <title>`: `td list --all --json -l pkh` → match exact title (use `jq` if
  present, else python3 fallback; fail soft to "not found" with stderr note).
- Priority map: P1→P1, P2→P2, P3→P3, P?→P4. Effort → `--points` (S=1, M=3, L=8, XL=13).

### 2. `scripts/lib/todo-match.sh` (new) — extract the active-item matcher
Move the lane/regex loop from `promote-todo.sh` (lines ~96–150) into a sourced function
returning line_no / priority / effort / title / description, so `start-todo.sh`,
`promote-todo.sh` and the kanban overlay share one parser. `promote-todo.sh` behaviour
must be byte-identical afterwards.

### 3. `scripts/start-todo.sh` (new)
`start-todo.sh --title <substr> [--no-start] [--dry-run]`
- Match exactly one active TODO item (same rules/errors as promote).
- td disabled → print "td not enabled; nothing to do (TODO.md is unchanged)" and exit 0.
- td enabled → idempotent: if `pkh_td_find` hits an open issue, print its id (+ `td start`
  hint) and exit. Else `td create "<title>" --labels pkh --priority … --points …
  --description-file -` with body: original TODO line, `Source: TODO.md`, backlog link
  if present; then `td start <id>` unless `--no-start`. Print the id on stdout.
- Does **not** modify TODO.md.

### 4. `scripts/promote-todo.sh` — post-promotion hint
After a successful (non-dry-run) promotion, if td enabled and `pkh_td_find` finds a
non-closed issue: print to stderr
`td issue <id> still <status> → td review <id> / td approve <id> ...` plus a harvest
reminder: "check `td show <id>` logs/handoff for pitfall- or backlog-worthy findings
before closing (td logs are machine-local)". Exit code unchanged.

### 5. `scripts/todo-kanban.sh` — optional overlay
- New `--td` flag (default: auto when `pkh_td_enabled`; `--no-td` to suppress;
  `--validate-only` never touches td so CI stays hermetic).
- Markdown board: append ` 🔧 td-xxxx (in_progress)` to active items with a matching
  open `pkh` issue; `--json` adds `"td": {"id","status"}`.
- Warnings section (stderr in validate path is untouched): orphan `pkh` issues whose
  title no longer matches any active item (shipped/renamed/removed) and still open.

### 6. `scripts/init.sh` + `assets/td-routing.md.template` (new)
If td is detected in target, append a sentinel-guarded "td ↔ TODO.md routing" snippet to
the agent contract (placed after the harness snippet; coexists with td's own
`td-agent-instructions` block). Routing rules:
- "maybe later / 先記下來" → `add-todo.sh` (TODO.md), never `td create`/`td defer`.
- Starting a TODO item → `start-todo.sh`; ad-hoc session work with no TODO line → plain `td`.
- Shipping → `promote-todo.sh` in the same commit, then td review/approve.
- Before approving a td issue: harvest durable findings into pitfalls/ or backlog/.
- Never commit `.todos/`; never write td ids into TODO.md.
Add `--td auto|on|off` to init (default auto).

### 7. Docs
- `references/integrating-trackers.md` (new): layering table (git knowledge / TODO
  intent / td execution / GitHub Issues for external reports), the one-way reference
  rule, cross-machine notes (local-only vs td-sync, Project ID not bound to remote),
  worktree note (`td link` path caveat), exit plan (`rm -rf .todos` + delete snippet).
- `SKILL.md`: short "Optional: td integration" section + list `start-todo.sh` and libs.
- `references/anti-patterns.md`: add "td ids in TODO.md", "dual-tracking the same item".

### 8. This repo
- Symlink `scripts/start-todo.sh` like the existing `scripts/add-todo.sh` symlinks;
  add `make start-todo` wrapper in `Makefile` next to `promote-todo`.
- Replace this repo's CLAUDE.md content with the routing snippet (by running the updated
  `init.sh --target .`, or pasting the template) — CLAUDE.md is currently uncommitted-
  modified with td's block; preserve that block.

## Verification
1. Regression: `make validate`; `./scripts/promote-todo.sh --dry-run --title <x> --summary y`
   output identical before/after refactor (diff against `git stash` version).
2. td-absent path: `PKH_TD=off ./scripts/start-todo.sh --title "Bump GitHub Actions"`
   → exits 0, TODO.md untouched; kanban output identical to today.
3. td path in a scratch copy (`cp -r` a temp repo into the scratchpad, `git init`,
   `td init`, `init.sh --target`): `start-todo.sh` creates+starts one `pkh` issue;
   re-run is idempotent; `todo-kanban.sh` shows the 🔧 marker; `promote-todo.sh` prints
   the review/harvest hint; kanban then warns about the orphan until `td approve`.
4. Worktree: `git worktree add` in the scratch repo, run `start-todo.sh` there → finds
   the same issue (no duplicate).
5. `bash -n` all scripts; run under `/bin/bash` (3.2) on macOS.
6. `make lint-frontmatter` for SKILL.md.

## Out of scope (follow-ups to note, not do)
- td-sync setup / Project-ID-vs-remote check (`.td-project` file) — only if multi-devbox
  td is adopted after the pilot.
- Pitfall `Last verified` + staleness check; fixing the stale Node 20 TODO item.
