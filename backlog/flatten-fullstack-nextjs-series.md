# Decide: flatten fullstack-nextjs series vs upstream CLI fix

**Status**: P? (effort M)
**Related**: [`pitfalls/skills-update-fails-for-series-nested-skills.md`](../pitfalls/skills-update-fails-for-series-nested-skills.md) · [`pitfalls/skills-cli-skips-nested-skills-without-full-depth.md`](../pitfalls/skills-cli-skips-nested-skills-without-full-depth.md) · `vendor.yaml` (`series:`) · `scripts/sync-vendor.sh` · `skills/.claude-plugin/marketplace.json`

## Context

2026-07, surfaced while debugging a downstream project (`EcojoyComponents`)
that ran `npx skills update` against this repo. The 4 skills under the
`fullstack-nextjs` series (`frontend-design`, `nextjs`, `shadcn`,
`supabase`) all reported `✗ Failed to update`, and their
`.claude/skills/<name>` symlinks were never created (`.agents/skills` had
8, `.claude/skills` had 4). Non-series skills at depth 3 updated fine.

## Investigation

Root-caused against `skills@1.5.14` `dist/cli.mjs` (full detail in the
pitfall). Key facts:

- `updateProjectSkills()` spawns, per locked skill:
  `skills add <repo> --skill <name> -y` — **hard-coded without
  `--full-depth`**. No way to opt in from the `update` command.
- `discoverSkills()` without `--full-depth` does a priority walk only:
  `skills/` → child (`local`/`vendor`) → grandchild (`<name>`) = 2 levels
  under `skills/`. Finds depth-3 `local/<name>` and `vendor/<name>`, but
  **not** depth-4 `vendor/<series>/<name>`. The recursive `findSkillDirs`
  fallback only runs when the priority walk found **zero** skills, which
  never happens here (~22 shallow skills).
- Reproduced: `Found 22 skills` (no `--full-depth`, series missing) vs
  `Found 47 skills` (with `--full-depth`, series present).
- Symlinks: a successful `add`/`update` reconciles `.claude/skills`
  symlinks on every run; a failed update leaves them missing → drift.
- Deletion-check hazard: `update`'s "check for deleted skills" step also
  uses `discoverSkills()` without `--full-depth`, so series skills can be
  mistaken for deleted (in the observed run the block threw and was
  skipped, which accidentally protected them).

Immediate workaround already applied downstream:
`npx skills add <repo> --skill frontend-design --skill nextjs --skill shadcn --skill supabase -y --full-depth`
→ refreshed content, updated `skills-lock.json`, created the 4 missing
symlinks. Verified `.agents`/`.claude` fully consistent afterward.

## Options considered

| Option | Pros | Cons |
|---|---|---|
| **A. Flatten series** — move `skills/vendor/fullstack-nextjs/<name>/` → `skills/vendor/<name>/` (depth 3) | Fully self-serve fix; series skills become updatable via plain `npx skills update`; no dependency on upstream. Grouped install UI is preserved (driven by `marketplace.json`, not directory depth). | Loses on-disk `fullstack-nextjs/` grouping. Touches `vendor.yaml` (`series:` field), `scripts/sync-vendor.sh` (series-dest handling), `marketplace.json` paths, and moves ~9 skill dirs. Possible name collisions to check (e.g. `supabase` vs any existing). Nested `nextjs/upstream/SKILL.md` + `react-best-practices/upstream/SKILL.md` need handling — they add a second SKILL.md per skill. |
| **B. Upstream CLI fix** — file issue on `vercel-labs/skills` so `update` passes `--full-depth` (and the deletion-check honors it) | Keeps the intentional series layout; benefits every repo that nests skills. Small, well-scoped upstream change. | Out of our control / unbounded timeline; even if merged, downstream users must upgrade the CLI. Until then, series skills still need the manual `--full-depth` refresh. |

These are mutually exclusive as the *primary* remedy, but **B can be filed
regardless** — it improves the ecosystem even if we also do A. If we do A,
B becomes optional.

## Current blocker / open questions

- Need user preference on whether the on-disk `fullstack-nextjs/` grouping
  is worth keeping. If not → do A. If yes → do B (+ document the
  `--full-depth` refresh caveat).
- If A: confirm no skill-name collisions after flattening; decide fate of
  the two `*/upstream/SKILL.md` nested copies; update the "Active series"
  note in `CLAUDE.md`.
- If B: draft the issue with the 22-vs-47 repro and the `dist/cli.mjs`
  `updateProjectSkills` / `discoverSkills` references.

## Decision (if any)

`2026-07 deferred` — captured as P? pending user's call on keeping the
series grouping. Interim: downstream refresh with `--full-depth` works.

`2026-07-08` — **Option B actioned** (does not resolve the A-vs-B structural
choice). Found the canonical upstream bug already open as
[vercel-labs/skills#1298](https://github.com/vercel-labs/skills/issues/1298)
("npx skills update does not support --full-depth"), so rather than file a
duplicate, enriched it with our independent root-cause + 22-vs-47 repro +
knock-on effects (symlink drift, false-deletion hazard) + suggested fix:
[comment](https://github.com/vercel-labs/skills/issues/1298#issuecomment-4910758441).
The **A (flatten) vs keep-nested** decision is still open — B only improves the
upstream on an unbounded timeline; until it lands, series skills still need the
manual `--full-depth` refresh downstream.

## References

- Upstream CLI: https://github.com/vercel-labs/skills (file issue here for option B)
- Local pitfalls linked above (symptom + repro + code refs).
