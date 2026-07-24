# Plan: harness scripts are skill-provided, not copied into the target repo (approach B)

## Context

`project-knowledge-harness` (and its sibling `experiment-knowledge-harness`)
bundle helper scripts. Their `init.sh` sets up files in a **target** project
and appends a guidance snippet to the target's `CLAUDE.md`/`AGENTS.md` — but it
**never copies the helper scripts into the target repo**. Yet the seeded
templates, the appended guidance, and `init.sh`'s printed epilogue all refer to
the helpers with bare `scripts/foo.sh` paths, which reads as *"the script lives
in this repo's `./scripts/`"*. It doesn't. A target-repo agent hits exactly this
gap: it finds no `scripts/`, then silently falls back to hand-editing
(observed live in the `unify-ashare-sdk` project).

**Decision (approach B):** keep NOT copying. Make every piece of text that lands
in a target repo say plainly that the helpers are **provided by the skill** and
are invoked *through the skill* (which knows where its `scripts/` live), with
hand-editing per the schema as the always-available fallback. This is a
**docs/template change** — no script *logic* changes except converting one
`init.sh` epilogue heredoc. Separately, this repo dogfoods the harness with
**byte-identical copies** of the 4 scripts at repo-root `scripts/`; the user
chose to migrate those to invoke the skill's copies and delete the duplicates.

`(end)` sentinel safety was investigated and is **fine** — it is always wrapped
in `<!-- … (end) -->` (verified empirically: 0 visible occurrences after
stripping comments). No change needed there.

## Wording pattern (applied everywhere text lands in a target repo)

1. Add ONE authoritative note near the first helper reference:
   > These helpers are provided by the **`<skill-name>` skill** and are *not*
   > copied into this repo. Invoke them through that skill (it knows where its
   > `scripts/` live) — they operate on this repo's files. If the skill isn't
   > available, maintain the files by hand using the schema below.
2. Everywhere else in target-landing text, drop the `scripts/` prefix and use
   the **bare command name** (`add-todo.sh`, `todo-kanban.sh --validate-only`,
   `promote-todo.sh`, `sweep-inbox.sh`; and for the experiment skill
   `new-experiment.py`, `render-index.py`, `log-finding.py`, `retriage.py`,
   `sweep-inbox.py`, `snapshot-provenance.py`). A bare name reads as "the skill
   helper named X", not "a file at ./scripts/X here".
3. **Skill-internal docs stay as-is** — `SKILL.md`, `references/*.md`, and each
   script's `--help`/`usage()` already describe running from the skill dir with
   bare `scripts/…`; that's correct in that context. Do NOT churn them.

## Part 1 — project-knowledge-harness (skill)

- `assets/agent-guidance.md.template` — the main offender (appended verbatim to
  the target's `CLAUDE.md`). Add the note (§pattern.1) up top; strip `scripts/`
  from the inline refs at L13-14, L19, L22 (code block), L37, L42, L58; fix the
  L2 HTML comment to say "the skill's `scripts/init.sh`".
- `assets/TODO.md.template` — seeded into the target. Reword L14 (HTML comment)
  and L49 (`promote-todo.sh` instruction) per §pattern; qualify the helper once
  as a `project-knowledge-harness`-skill helper so a standalone reader isn't
  misled.
- `scripts/init.sh`:
  - **Inbox heredoc** (`<<'INBOX_EOF'`, ~L212-226): L216 references
    `scripts/sweep-inbox.sh` and is written into the *target's* `backlog/inbox.md`
    → reword to the bare/skill-qualified name (keep the heredoc quoted; do NOT
    bake an absolute path into a committed target file).
  - **"Next steps" epilogue** (`<<'EOF'`, ~L249-264): this prints to the person
    running `init.sh` (who *has* the skill). Match the experiment sibling
    (`experiment-knowledge-harness/scripts/init.sh` L154-164 already does this):
    convert `<<'EOF'` → `<<EOF` and use absolute `"$scripts_dir"/foo.sh` so the
    installer gets copy-pasteable commands. **Care:** unquoted heredoc — escape
    the trailing line-continuation backslashes (`\` → `\\`) and confirm no other
    `$`/backtick in the block expands unintentionally.

## Part 2 — experiment-knowledge-harness (skill)

Same pattern. Target-landing edits only (per the inventory):
- `assets/agent-guidance.md.template` — strengthen the existing L17 note
  ("scripts live in the skill folder") into the full §pattern.1 note; strip
  `scripts/` at L2, L25, L28, L39, L40, L43, L46 (L42 already bare).
- `assets/LEDGER.md.template` (L8, L13), `assets/ROADMAP.md.template`
  (L10, L13), `assets/experiments-README.md.template` (L14, L15, L20, L26) —
  seeded files: strip `scripts/`; add a one-line skill-provided note where the
  file first names a helper.
- `assets/report.md.template` (L69, HTML comment) — reaches the target via
  `new-experiment.py`; strip `scripts/` from `snapshot-provenance.py`.
- `scripts/render-index.py` (L51) — the "no experiments yet" placeholder string
  is written into the target README; strip `scripts/` from `new-experiment.py`
  (L87 is already bare).
- `scripts/init.sh` epilogue already uses `$scripts_dir` — **no change**.

## Part 3 — migrate THIS repo (M1: repoint + delete duplicates)

Root `scripts/` holds the 4 harness scripts as byte-identical copies plus 3
unrelated scripts (`add-vendor.sh`, `sync-vendor.sh`, `validate-marketplace.sh`,
which stay). Confirmed correct: invoking e.g.
`./skills/local/project-knowledge-harness/scripts/add-todo.sh` from repo root
resolves its validator/template via `dirname "$0"` (→ the skill's own
`scripts/`+`assets/`) and operates on repo-root `TODO.md`/`backlog/` (CWD-relative).

- `Makefile` — repoint the `kanban` (L14), `add-todo` (L25), `promote-todo`
  (L29), `sweep-inbox` (L32) recipes from `./scripts/<x>.sh` to
  `./skills/local/project-knowledge-harness/scripts/<x>.sh`. Update the L21
  comment. `make kanban` etc. stay as the short aliases.
- Root `CLAUDE.md` — repoint the harness-script paths at L34, L38-39, L42, L154,
  L159, L162, L177, L183, L191 to the skill path (leave `make kanban` mentions
  and the non-harness `add-vendor.sh`/marketplace references alone).
- `README.md` (L108, L111, L114) and `backlog/inbox.md` (L4 link + L28-30) —
  repoint the same way.
- **Delete** the 4 duplicated root copies:
  `scripts/{add-todo,promote-todo,sweep-inbox,todo-kanban}.sh`.

## Explicitly out of scope

- `SKILL.md` / `references/*.md` / script `--help` in both skills (skill-internal
  — bare `scripts/…` is correct there).
- `.specstory/history/*` and `.cursor/plans/*` matches — immutable committed
  agent artifacts; do not edit.
- The `$repo_root/scripts/...` fallback candidates inside `add-todo.sh` /
  `sweep-inbox.sh` — become unused under M1 but are harmless; leave them.

## Verification

1. **`(end)`/no-leak + guidance render** — dry-run `init.sh` into a temp dir for
   BOTH skills; confirm the appended guidance + seeded files contain no bare
   `scripts/<helper>` implying an in-repo path, and no visible `(end)`:
   ```sh
   TMP=$(mktemp -d); printf '# X\n' > "$TMP/CLAUDE.md"; printf '# X\n' > "$TMP/README.md"
   skills/local/project-knowledge-harness/scripts/init.sh --target "$TMP" --deployment npm
   grep -rnE 'scripts/(add-todo|promote-todo|sweep-inbox|todo-kanban)' "$TMP"   # expect: none
   sed 's/<!--[^>]*-->//g' "$TMP/CLAUDE.md" "$TMP/README.md" | grep -c '(end)'  # expect: 0
   ```
   Repeat for `experiment-knowledge-harness` (checks `experiments/` + agent guidance).
2. **init.sh epilogue** — `bash -n skills/local/project-knowledge-harness/scripts/init.sh`,
   then eyeball the printed "Next steps" shows absolute `$scripts_dir/...` paths
   with correctly-escaped `\\` continuations.
3. **This repo still works after M1** (run from repo root):
   ```sh
   make kanban                                   # validates + renders root TODO.md
   make add-todo ARGS="--priority P3 --effort S --title 'Tmp probe' --description 'x' --dry-run"
   ls scripts/                                    # 4 harness copies gone; add-vendor/sync-vendor/validate-marketplace remain
   ./scripts/todo-kanban.sh 2>/dev/null || echo "root copy correctly removed"
   ```
4. `git grep -nE '(^|[^/.a-z])scripts/(add-todo|promote-todo|sweep-inbox|todo-kanban)'`
   returns only skill-internal (`SKILL.md`/`references`) + history-artifact hits.
