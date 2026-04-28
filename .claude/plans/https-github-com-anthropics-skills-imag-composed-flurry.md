# Add category groupings to the `npx skills@latest add` selection UI

## Context

`npx skills@latest add anthropics/skills` shows skills grouped under
**Document Skills**, **Example Skills**, **Claude Api**, **Other** (see
the user's screenshot). This repo (`daviddwlee84/agent-skills`) currently
presents all 22 skills as a flat list. Goal: same grouped UX so picking a
subset is easier — especially as the repo now spans unrelated domains
(ML, notebooks, fullstack web, skill authoring, project hygiene, job
queues, docs).

## Why `.claude-plugin/marketplace.json` (and only that)

Verified by reading the `npx skills` source (npm package `skills` =
`vercel-labs/skills`, `src/plugin-manifest.ts` and `src/add.ts`):

- `npx skills` only ever opens two paths:
  `.claude-plugin/marketplace.json` (catalog of plugins) and
  `.claude-plugin/plugin.json` (single-plugin repo). **There is no native
  `skills.json` / `skills.yaml` / catalog format.** Greppable in the source.
- Group headers in the picker = `kebabToTitle(plugins[].name)`. Anything not
  listed in any plugin auto-falls into **Other**.
- Fields read by `npx skills` for grouping: only `plugins[].name`,
  `plugins[].source`, `plugins[].skills`. `category`, `tags`, `version`,
  `description`, `strict`, `author` pass through but **are not used by the
  picker** — they are, however, honored by Claude Code's native `/plugin`
  marketplace UI, so it's cheap to include them.
- `plugin.json` is **not** needed for us. It's for single-plugin repos;
  `anthropics/skills` ships none, and neither should we.
- A canonical `skills.catalog.yaml` + generator (the layered design ChatGPT
  proposed) is **not** justified yet: only one consumer reads this metadata.
  Adding a generator before a second native target exists is overdesign.

### Verified gotchas (all from official Claude Code plugin-marketplaces docs)

- **Reserved marketplace `name`s** include `agent-skills`,
  `claude-code-marketplace`, `claude-code-plugins`,
  `claude-plugins-official`, `anthropic-marketplace`, `anthropic-plugins`,
  `knowledge-work-plugins`, `life-sciences`, plus impersonations like
  `official-claude-plugins`. So this repo's marketplace `name` will be
  **`daviddwlee84-skills`** (folder name `agent-skills` is fine — only the
  `name` field is restricted).
- `source: "./..."` is relative to the marketplace **root** (= repo root),
  not relative to `.claude-plugin/`.
- Omitting `metadata.version` while hosting in git makes every commit a
  new version. Desired during active dev. Match `anthropics/skills`, which
  ships no version.

## Plan

### 1. Create `.claude-plugin/marketplace.json`

Top-level shape modeled on upstream, with the corrections above:

```json
{
  "name": "daviddwlee84-skills",
  "owner": { "name": "Da-Wei Lee", "email": "daviddwlee84@gmail.com" },
  "metadata": {
    "description": "Personal collection of authored + vendored agent skills",
    "version": "1.0.0"
  },
  "plugins": [ ... ]
}
```

Plugin groupings (6 plugins, all 22 skills accounted for; no skills will
fall under "Other" by default). The "UI label" column shows what
`kebabToTitle(name)` will render in the picker — names chosen so the
casing reads sensibly:

| `name` | UI label | Skill paths |
|---|---|---|
| `skill-authoring` | Skill Authoring | `./skills/local/skill-author`, `./skills/vendor/skill-creator` |
| `project-memory` | Project Memory | `./skills/local/project-knowledge-harness`, `./skills/local/agent-history-hygiene` |
| `ml-workflow` | Ml Workflow | `./skills/local/mlflow-tracking`, `./skills/local/dvc-ml-workflow`, `./skills/local/marimo-batch-mlflow`, `./skills/local/quantatitive-factor-researcher` |
| `notebooks` | Notebooks | `./skills/vendor/marimo-notebook`, `./skills/vendor/streamlit-to-marimo`, `./skills/vendor/anywidget` |
| `fullstack-nextjs` | Fullstack Nextjs | the 9 dirs under `./skills/vendor/fullstack-nextjs/` |
| `infra-and-docs` | Infra And Docs | `./skills/local/mkdocs-site-bootstrap`, `./skills/local/pueue-job-queue` |

(If the "Ml Workflow" / "Fullstack Nextjs" titlecasing looks ugly, we can
rename to e.g. `machine-learning` → "Machine Learning", `nextjs-stack` →
"Nextjs Stack". Easy to tweak.)

Each `plugins[]` entry includes `name`, `description`, `source: "./"`,
`strict: false`, `skills: [...]`. We will additionally include `category`
and `tags` per plugin (ignored by `npx skills`, honored by Claude Code's
native `/plugin` UI — zero downside). No `version` field — match upstream.

### 2. Add `scripts/validate-marketplace.sh`

Bash + `jq` validator (jq already used by `scripts/sync-vendor.sh`).
Checks:

1. `.claude-plugin/marketplace.json` parses as JSON.
2. `name` is not in the reserved list (hard-coded inside the script).
3. Every `plugins[].skills[]` path exists and contains a `SKILL.md`.
4. No path is listed in more than one plugin.
5. Every on-disk `skills/**/SKILL.md` (one or four levels deep, matching
   `CLAUDE.md`'s discovery rules) is either listed in some plugin or
   logged as a warning that it will fall through to **Other**.

Wire as `make marketplace`. Exit non-zero on errors (1–4); warnings only
for (5) so adding a skill mid-edit doesn't break the build.

### 3. Documentation touch-ups

- **`README.md`** — short "Categories in the install UI" section pointing
  at `.claude-plugin/marketplace.json` and `make marketplace`.
- **`CLAUDE.md`** — one bullet under Commands (`make marketplace`) and
  one line in "Vendor System" reminding that adding a skill also means
  editing `marketplace.json` (or accepting the "Other" fallback).

## Critical files

- **New:** `.claude-plugin/marketplace.json` — the only file the CLI reads
- **New:** `scripts/validate-marketplace.sh`
- **Edit:** `Makefile` — add `marketplace` target
- **Edit:** `README.md` — categories section
- **Edit:** `CLAUDE.md` — workflow note + new command bullet
- **Reference (do not change):** `vendor.yaml` — different purpose
  (governs upstream syncing, not user-facing grouping); the `series:`
  field is independent of `marketplace.json`. Both can coexist.

## Verification

1. `jq . .claude-plugin/marketplace.json` — well-formed JSON.
2. `bash scripts/validate-marketplace.sh` — exits 0; no broken paths,
   no duplicates, all 22 skills accounted for.
3. `make marketplace` — invokes the validator and passes.
4. Push to `main`, then from an unrelated directory run
   `npx skills@latest add daviddwlee84/agent-skills`. Confirm the picker
   shows the 6 group headers and an empty/absent **Other**. The CLI pulls
   from the GitHub remote, not the working tree, so changes must be
   pushed first.
5. Sanity check: temporarily remove one path from `marketplace.json`,
   re-run `npx skills@latest add daviddwlee84/agent-skills`, confirm
   that skill now lives under **Other** — then revert.

---

## Follow-up commit: docs additions for hide/deprecate + per-row rendering

Question raised after the first commit: are there `marketplace.json`
fields that annotate a skill in the picker UI without modifying SKILL.md,
and is there a way to hide a deprecated skill while keeping it in the
repo?

Verified from `vercel-labs/skills` source:

- **No external annotation.** Per `src/add.ts` lines 1184-1188, each
  picker row is `{ label: skill.name, hint: skill.description.slice(0,57)+'…' }`
  — both pulled from SKILL.md. Nothing in `marketplace.json` is rendered
  for an individual skill row. Plugin `name` only appears as the group
  header.
- **Hide mechanism exists.** Per `src/skills.ts` lines 47-54, setting
  `metadata.internal: true` in SKILL.md frontmatter hides the skill
  from the picker by default. Still installable by name, with
  `INSTALL_INTERNAL_SKILLS=1`, or via `--include-internal`.

### Changes (already applied to working tree, awaiting commit)

- `docs/reference/npx-skills-metadata.md` — added two subsections:
  - **"What the picker actually shows for a skill row"** (under Manifest
    shape) — clarifies SKILL.md is the only knob for per-skill
    annotations.
  - **"Hiding / deprecating a skill without deleting it"** — documents
    `metadata.internal: true`, the install-by-name override, the
    interaction with `marketplace.json` (mutually exclusive), and a
    sketch of validator extension #2 left as a deferred TODO.
- `.specstory/history/2026-04-28_08-24-41Z-https-github-com-anthropics.md`
  — auto-appended chat transcript (per `agent-history-hygiene`).

### Commit

Single commit, message focused on documentation.

```
docs: hide/deprecate mechanism + per-row picker rendering for npx skills

Document `metadata.internal: true` in SKILL.md frontmatter as the
officially-supported hide mechanism for deprecated-but-kept skills,
verified in vercel-labs/skills src/skills.ts. Also clarify that no
marketplace.json field is rendered per skill row (label = SKILL.md name,
hint = SKILL.md description) — plugin name only appears as the group
header. Sketch validator extension #2 as a deferred TODO.
```

### Verification

- `make docs-build` — already verified, builds cleanly.
- `git diff --stat` — only `docs/reference/npx-skills-metadata.md`
  (+92) and the specstory transcript should be in the commit.
