# Vendor Matt Pocock's full "Skills for Real Engineers" flow + a docs deep-dive

## Context (why)

The user watched Matt Pocock's video
[*"mattpocock/skills: Learn the whole flow, end-to-end"*](https://youtu.be/M6mYodf0dJM)
and wants a **dedicated docs page introducing his series of skills** — noting we've
"already added it to vendor." Two things surfaced during exploration:

1. **Our vendored snapshot is stale and partly broken.** We ship 9 skills under
   `series: engineering-fundamentals`, frozen at the 2026-07-05 sync. Since then
   Matt Pocock reorganized the repo: `to-prd`→`to-spec`, `to-issues`→`to-tickets`
   (renamed), `zoom-out` deleted (already frozen locally), and ~15 new skills added
   across `engineering/`, `productivity/`, `misc/`, `deprecated/`, `in-progress/`,
   `personal/` buckets. `make sync-check` shows the two renamed paths as
   "update available (…→386d4ff)", but `386d4ff` is the *deletion* commit — a real
   `make sync` would download **zero files** for `to-prd`/`to-issues` and fail hard
   (the exact case CLAUDE.md documents under "When an upstream skill is renamed").
2. **The reorg introduced cross-skill dependencies.** `grill-with-docs` now says
   *"Run a `/grilling` session, using the `/domain-modeling` skill"* — a hard dep on
   two skills we don't vendor. `implement` drives `/tdd` + `/code-review`. Re-syncing
   without adding these would ship a broken `grill-with-docs`.

**Decisions locked (from the plan Q&A):**
- **Format:** a single **Reference deep-dive** page (`docs/reference/mattpocock-skills.md`
  + `.zh-TW.md`), modeled on `docs/reference/warp-oz-skills.md`, cross-linked from the
  catalog. (Not per-skill Skills pages.)
- **Vendor drift:** *"Directly update vendor upstream first"* — fix the vendored set
  now, then document.
- **Vendor scope:** **Vendor the full flow** — series grows **9 → 14**: re-sync 6,
  rename 2, keep `zoom-out` frozen, and **add 5**: `grilling`, `domain-modeling`,
  `implement`, `code-review`, `wayfinder`. This makes the
  grill → spec → tickets → implement → review chain the video teaches actually
  installable and self-consistent. Remaining upstream skills go to a TODO.

Upstream is **MIT-licensed** (confirmed via the GitHub license endpoint) and
agentskills.io-portable — safe to vendor.

---

## Part A — Update the vendored `engineering-fundamentals` series (do this first)

Final membership (14): `grill-with-docs`, `tdd`, `diagnosing-bugs`,
`improve-codebase-architecture`, `triage`, `prototype` (re-sync) · `to-spec`,
`to-tickets` (renamed) · `zoom-out` (frozen) · **`grilling`, `domain-modeling`,
`implement`, `code-review`, `wayfinder`** (new).

**A1. Handle the two renames** (follow CLAUDE.md → "When an upstream skill is renamed").
For each of `to-prd`→`to-spec` and `to-issues`→`to-tickets`, in `vendor.yaml`:
- change `name:` and `upstream.path:` to the new value
  (`skills/engineering/to-spec`, `skills/engineering/to-tickets`),
- add `renamed_from: to-prd` / `renamed_from: to-issues`,
- `git mv skills/vendor/engineering-fundamentals/to-prd .../to-spec` (and to-tickets),
- update that skill's path in `marketplace.json` (Part A5).
Mirror the existing `diagnosing-bugs` (`renamed_from: diagnose`) precedent.
Note: renaming changes the downstream install id (documented, acceptable).

**A2. Re-sync existing entries.** Run `make sync`. This refreshes the 6 survivors and
the 2 renamed paths to HEAD (`697d4ce` / `386d4ff`); `zoom-out` stays skipped (frozen).
- Caveat: `make sync` also refreshes any other pending entry — `sync-check` shows
  `supabase` + `supabase-postgres-best-practices` have an update (1356046→1ad9aae).
  Prefer a mattpocock-scoped sync if `scripts/sync-vendor.sh` supports name/series
  filtering; if not, let the supabase bump ride (harmless) or split it into its own
  commit to keep this PR focused.

**A3. Add the 5 new skills** via `scripts/add-vendor.sh --series engineering-fundamentals`
(verifies upstream exists, dedupes, auto-syncs):
- `mattpocock/skills/skills/productivity/grilling`
- `mattpocock/skills/skills/engineering/domain-modeling`
- `mattpocock/skills/skills/engineering/implement`
- `mattpocock/skills/skills/engineering/code-review`
- `mattpocock/skills/skills/engineering/wayfinder`

(Series grouping is ours — `grilling` lands in
`skills/vendor/engineering-fundamentals/grilling/` even though upstream files it under
`productivity/`.)

**A4. Resolve transitive dependencies.** After A2/A3, grep each refreshed/added
`SKILL.md` for `/<skill>` references to un-vendored skills and confirm the set closes:
- Known: `grill-with-docs` → `/grilling`, `/domain-modeling` (now vendored ✓);
  `implement` → `/tdd` (✓) + `/code-review` (✓); `triage`/`improve-codebase-architecture`
  → `/grilling` (✓).
- `to-spec`, `to-tickets`, `triage` reference `/setup-matt-pocock-skills` — a **soft**
  dep (they say "run it if not provided" and degrade gracefully). Not vendored; document
  it as a one-time prerequisite (Part B) and list in the TODO (Part E). If the grep finds
  any *new* hard dep on an un-vendored skill, add it or flag it.

**A5. Update `skills/.claude-plugin/marketplace.json`** (`engineering-fundamentals` plugin):
- Repoint `./vendor/engineering-fundamentals/to-prd` → `to-spec`,
  `.../to-issues` → `to-tickets`.
- Add 5 `skills[]` paths for the new skills.
- Refresh the plugin `description` to name the end-to-end flow.
- Run `make marketplace` (validates paths, dupes, reserved names).

**A6. Validate Part A:** `make sync-check` (should now show no rename breakage),
`make marketplace`, and confirm all 14 `skills/vendor/engineering-fundamentals/*/SKILL.md`
exist. Note the possible `code-review` naming overlap with the built-in `/code-review`
command — distinct skill, acceptable, but mention it in the docs.

---

## Part B — Reference deep-dive page (EN + zh-TW)

Create `docs/reference/mattpocock-skills.md` (+ `.zh-TW.md` full translation with the
standard zh-TW terminology admonition). Model on `docs/reference/warp-oz-skills.md`.
Outline:

1. **Intro** — who Matt Pocock is, the repo pitch ("skills I use every day to do real
   engineering — not vibe coding"; "small, easy to adapt, composable; work with any
   model"), and the video link (*"Learn the whole flow, end-to-end"*).
2. **The end-to-end flow** — the video's thesis, as a `mermaid` flowchart plus prose:
   `grill-with-docs`/`grill-me` (align + `CONTEXT.md`/ADRs) → `to-spec` → `to-tickets`/
   `wayfinder` (tracer-bullet vertical slices) → `triage` (ready-for-agent briefs) →
   `implement` (drives `/tdd` + `/code-review`) → `improve-codebase-architecture`
   (deepen), with `diagnosing-bugs` on the break path. (mermaid fence already enabled
   in `mkdocs.yml`.)
3. **Why it's installable here** — MIT license + agentskills.io portability (mirror the
   Warp Oz licensing section).
4. **Skills we vendor (14)** — table(s) grouped by role (user-invoked orchestrators vs
   model-invoked disciplines), each row: skill · one-line · upstream bucket. Mark the
   frozen `zoom-out`.
5. **Prerequisite: `/setup-matt-pocock-skills`** — the one-time bootstrap the flow
   assumes (issue tracker + triage labels + docs location); why we don't vendor it.
6. **Upstream skills we don't vendor (yet)** — mirror Warp Oz's "skipped" paragraph:
   `ask-matt` (router), `research` (dup of vendored `deep-research`), `handoff`/`teach`
   (niche productivity), `writing-great-skills` (dup of local `skill-author`), `grill-me`
   (user wrapper of `grilling`), `resolving-merge-conflicts`, `misc/*`
   (`git-guardrails-claude-code`, `setup-pre-commit`, …), and the `deprecated/`,
   `in-progress/`, `personal/` buckets — skipped wholesale. Link the Part E TODO.
7. **The 2026-07 reorg** — renames (`to-prd`→`to-spec`, `to-issues`→`to-tickets`),
   `zoom-out` deletion (frozen locally), bucket restructure, and how our
   `renamed_from:`/`frozen:` bookkeeping records it.
8. **Install** — ours (`npx skills@latest add daviddwlee84/agent-skills`) + upstream full
   set (`npx skills@latest add mattpocock/skills`; `claude plugin marketplace add
   mattpocock/skills`).
9. **See also** — the catalog row, the Agent Harness domain hub, `warp-oz-skills.md`
   (its GitHub triage skills complement `triage`).

---

## Part C — Catalog cross-reference

Update the mattpocock row in `docs/catalog/skill-collections.md` **and**
`skill-collections.zh-TW.md` (line ~38 / ~43): fix the stale skill list
(`diagnose`→`diagnosing-bugs`, `to-prd`→`to-spec`, `to-issues`→`to-tickets`, note
`zoom-out` frozen; 9→14), and append the Warp-Oz-style cross-link
`— see [reference/mattpocock-skills.md](../reference/mattpocock-skills.md)`.

## Part D — Nav wiring

In `mkdocs.yml`, add under `Reference:` (next to `Warp Oz skills`):
`- Matt Pocock skills: reference/mattpocock-skills.md`. The `llmstxt` `Reference:`
glob (`reference/*.md`) picks it up automatically; zh-TW is auto-derived by the i18n
suffix plugin.

## Part E — TODO for the remaining upstream skills

`./scripts/add-todo.sh --priority P? --effort M --backlog --title "Evaluate remaining
mattpocock/skills for engineering-fundamentals" --description "Core flow vendored (14).
Decide on the rest: setup-matt-pocock-skills (opinionated bootstrap), ask-matt (router),
research (dup deep-research), handoff, teach, writing-great-skills (dup skill-author),
grill-me, resolving-merge-conflicts, misc/*. Skip deprecated/in-progress/personal
buckets."` The `--backlog` note captures the per-candidate skip rationale.

---

## Files to create / modify

| File | Change |
|---|---|
| `vendor.yaml` | 2 renames (+`renamed_from`, bumped `last_sync`), 5 new entries, refreshed SHAs |
| `skills/vendor/engineering-fundamentals/**` | `git mv` 2 dirs; re-synced content; 5 new dirs |
| `skills/.claude-plugin/marketplace.json` | 2 repointed paths, 5 new paths, updated description |
| `docs/reference/mattpocock-skills.md` **(new)** + `.zh-TW.md` **(new)** | the deep-dive |
| `docs/catalog/skill-collections.md` + `.zh-TW.md` | fixed + cross-linked mattpocock row |
| `mkdocs.yml` | nav leaf under `Reference` |
| `TODO.md` (+ `backlog/<slug>.md`) | P? entry via `add-todo.sh` |

Reuse existing utilities — don't hand-roll: `scripts/add-vendor.sh --series`,
`scripts/sync-vendor.sh` (`make sync` / `make sync-check`), `scripts/add-todo.sh`,
`make marketplace`, `make kanban`, `make docs-build`.

## Verification

1. `make sync-check` — no rename breakage; the 14 entries resolve.
2. `make marketplace` — manifest valid (paths, dupes, reserved names).
3. `ls skills/vendor/engineering-fundamentals/*/SKILL.md` — 14 present; grep for dangling
   `/<skill>` refs to confirm the dependency set closes (Part A4).
4. `make kanban` — TODO validates after `add-todo.sh`.
5. `make docs-build` (strict) — no broken links / missing snippet includes; then
   `make docs-serve` and eyeball the new page: mermaid flow renders, EN + zh-TW both
   load, catalog cross-link and nav entry resolve.

## Risks / notes

- **Install-id churn:** `to-prd`→`to-spec`, `to-issues`→`to-tickets` change downstream
  install ids (no lockfile in `npx skills`). Documented via `renamed_from:` — same as the
  `diagnose`→`diagnosing-bugs` precedent.
- **`setup-matt-pocock-skills` soft dep:** the flow assumes a configured issue tracker /
  labels / docs dir. We document it as a prerequisite rather than vendor the opinionated
  bootstrap; it's the top TODO candidate.
- **`make sync` breadth:** it will also pull the pending `supabase` update unless the sync
  is scoped — call it out or split commits.
- **`code-review` name overlap** with the built-in `/code-review` — distinct skill; noted
  in the docs.
