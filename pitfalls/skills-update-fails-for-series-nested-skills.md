# `npx skills update` reports "Failed to update" for series-nested (depth-4) skills and leaves `.claude/skills` symlinks missing

## Symptom

Running `npx skills update` in a downstream project that installed skills
from this repo:

```
Updating for: Universal, Claude Code
Refreshing 8 skill(s)...

✗ Failed to check for deleted skills from daviddwlee84/agent-skills
Updating agent-history-hygiene...
  ✓ Updated agent-history-hygiene
Updating frontend-design...
  ✗ Failed to update frontend-design
Updating nextjs...
  ✗ Failed to update nextjs
...
Updating shadcn...
  ✗ Failed to update shadcn
Updating supabase...
  ✗ Failed to update supabase

✓ Updated 4 skill(s)
Failed to update 4 skill(s)
```

Key signal: **only the skills under a `vendor/<series>/` subdir fail** —
here `frontend-design`, `nextjs`, `shadcn`, `supabase`, all of which live
at `skills/vendor/fullstack-nextjs/<name>/SKILL.md`. Everything at
`skills/local/<name>/` and `skills/vendor/<name>/` (one shallower)
updates fine.

Second symptom — **agent symlink drift**. The project's
`.agents/skills/` (canonical Universal copies) has all 8 skills, but
`.claude/skills/` only has symlinks for the 4 that updated
successfully:

```
$ ls .agents/skills/    # 8 real dirs
agent-history-hygiene  frontend-design  nextjs  project-knowledge-harness
shadcn  skill-author  skill-creator  supabase
$ ls .claude/skills/    # only 4 symlinks — the 4 that succeeded
agent-history-hygiene -> ../../.agents/skills/agent-history-hygiene
project-knowledge-harness -> ../../.agents/skills/project-knowledge-harness
skill-author -> ../../.agents/skills/skill-author
skill-creator -> ../../.agents/skills/skill-creator
```

## Root cause

`skills update` does not fetch skills itself — for each locked skill it
**spawns** the equivalent of:

```
skills add daviddwlee84/agent-skills --skill <name> -y      # NOTE: no --full-depth
```

`add`'s `discoverSkills()` without `--full-depth` does a *priority walk*
only: `skills/` → child (`local`/`vendor`) → grandchild (`<name>`). That
is **two levels under `skills/`**, so it discovers:

- `skills/local/<name>/SKILL.md` ✓ (depth 3)
- `skills/vendor/<name>/SKILL.md` ✓ (depth 3)

but **not** `skills/vendor/<series>/<name>/SKILL.md` (depth 4) — the
series skill is a *great-grandchild* and is never walked. The recursive
`findSkillDirs` fallback that *would* reach depth 4 only runs when the
priority walk found **zero** skills; this repo has ~22 shallow skills, so
the fallback never fires.

Because `update` hard-codes the spawn without `--full-depth`, there is
**no way to opt in from the `update` command** — the series skills fail
every time. `filterSkills` gets an empty match → `No matching skills
found for: frontend-design` → `add` exits 1 → `update` prints
`✗ Failed to update`.

Reproduced with `skills@1.5.14`:

```
without --full-depth :  Found 22 skills → "No matching skills found for: frontend-design"
with    --full-depth :  Found 47 skills → "✓ Installed frontend-design"
```

Two knock-on effects:

1. **Symlink drift.** `add` writes the canonical copy to
   `.agents/skills/<name>` and then (re)creates a symlink in every
   detected agent dir (`.claude/skills/<name>`) on *each successful*
   install/update. A skill that fails to update never gets its
   `.claude/skills` symlink — hence `.agents` has 8 but `.claude` has 4.
   This is *not* a first-install-only mechanism: a successful
   `add`/`update` always reconciles the symlinks, as long as the agent
   dir (`.claude`) exists at that moment.
2. **False "deleted skill" hazard.** `update`'s deletion check also runs
   `discoverSkills()` without `--full-depth`, so the series skills look
   absent and could be offered up for removal. In the run above the whole
   deletion block threw (`✗ Failed to check for deleted skills`) and was
   skipped — which accidentally saved them.

Note: an older `pitfalls/skills-cli-skips-nested-skills-without-full-depth.md`
claimed `skills/local/*` were invisible without `--full-depth`. That is
**stale** for `skills@1.5.14` — the priority walk now reaches depth-3
`local/` and `vendor/`. Only depth-4 **series** subdirs are still missed.

## Workaround

Re-install the series skills once with `--full-depth`. This refreshes the
content, updates `skills-lock.json`, **and** creates the missing
`.claude/skills` symlinks (multiple `--skill` allowed):

```bash
cd <downstream-project>
npx skills@latest add daviddwlee84/agent-skills \
  --skill frontend-design --skill nextjs --skill shadcn --skill supabase \
  -y --full-depth
```

Plain `npx skills update` keeps working for every non-series skill; only
the series ones need this manual `--full-depth` refresh each time.

## Prevention

- **Preferred structural fix:** flatten the series so each skill sits at
  `skills/vendor/<name>/` (depth 3), where `update`'s shallow discovery
  finds it. The marketplace grouping is driven by
  `skills/.claude-plugin/marketplace.json`, not by directory depth, so
  flattening keeps the grouped install UI intact. Cost: touches
  `vendor.yaml` (`series:` field), `scripts/sync-vendor.sh`, and the
  `marketplace.json` paths.
- If the nested `vendor/<series>/<name>/` layout is kept, document that
  those skills can only be updated via
  `npx skills add … --skill <name> --full-depth`, never plain
  `npx skills update`.
- To keep `.agents/skills` and `.claude/skills` consistent, make sure the
  agent dir (`.claude/`) exists **before** the install/update that should
  populate it, and that the install actually succeeds — the CLI
  reconciles symlinks on every success, so a green install == a present
  symlink.

## Where this was hit

Downstream project `EcojoyComponents` ran `npx skills update` after
manually creating `.claude/`. The 4 `fullstack-nextjs` series skills
failed to update and never got `.claude/skills` symlinks; the 4
shallow-path skills updated and symlinked fine. Diagnosed by reading
`skills@1.5.14`'s `dist/cli.mjs` (`updateProjectSkills` → spawns
`add --skill` without `--full-depth`; `discoverSkills` priority walk) and
reproducing the 22-vs-47 skill count with/without `--full-depth`.
See also [`skills-cli-skips-nested-skills-without-full-depth.md`](skills-cli-skips-nested-skills-without-full-depth.md).
