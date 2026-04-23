# `npx skills add` ignores skills under `skills/local/` without `--full-depth`

## Symptom

```
$ npx skills@latest add daviddwlee84/agent-skills -g -s skill-author -y
...
■  No matching skills found for: skill-author
│
●  Available skills:
│    - find-skills
│    - skill-creator
```

The skill clearly exists at `skills/local/skill-author/SKILL.md` in the
upstream repo, but `skills` CLI can't find it. Only skills sitting at
`skills/<name>/SKILL.md` (one level under `skills/`) are discovered.

## Root cause

The `npx skills` CLI (vercel-labs/skills) discovers skills by looking
**one level deep** under `skills/` for `SKILL.md`. If it finds at least
one match at that level, it stops. Recursive fallback **only** kicks in
when zero skills are discovered at the top level.

This repo uses `skills/local/` and `skills/vendor/` to organize
custom-authored vs cherry-picked skills. Because `skills/vendor/` (and
indirectly `skills/local/`) doesn't put a `SKILL.md` immediately at
`skills/<name>/`, the CLI's default discovery goes:

1. Check `skills/local/SKILL.md` and `skills/vendor/SKILL.md` → both
   missing.
2. Walk one level deeper: `skills/local/<name>/SKILL.md` and
   `skills/vendor/<name>/SKILL.md` → fallback recursive search finds
   `skills/vendor/skill-creator` and `skills/vendor/marimo-notebook`
   etc., **stops there**.
3. Never descends into `skills/local/<name>/`.

So `skills/local/*` skills are invisible to `add` / `update` / `list`
unless the user explicitly opts into deeper discovery.

## Workaround

Pass `--full-depth` to force the CLI to keep walking even after it found
top-level skills:

```bash
npx --yes skills@latest add daviddwlee84/agent-skills \
  -g -s skill-author -y --full-depth
```

Verified to discover all four skills:

```
✓ ~/.agents/skills/skill-author
  universal: Antigravity, Codex, Cursor, Gemini CLI, GitHub Copilot ...
  symlinked: Claude Code, Continue, Droid
```

## Prevention

- Document `--full-depth` prominently in this repo's
  [`README.md`](../README.md) install snippet for any skill under
  `skills/local/`. The current snippet
  (`npx skills@latest add daviddwlee84/agent-skills`) installs only
  `skills/vendor/*` plus whatever's at `skills/<name>/`, silently
  skipping local skills.
- Alternatively: flatten `skills/` so all skills live at
  `skills/<name>/` directly. Trade-off: loses the visual local/vendor
  separation. The current nested layout is intentional (per
  [`docs/conventions.md`](../docs/conventions.md)) so flattening is
  not the preferred fix.
- For repo dogfooding (this same repo using its own skills via
  `.claude/skills/<name>` symlinks), CLI discovery doesn't matter —
  symlinks bypass the CLI entirely. Only matters when an outside
  user runs `npx skills add daviddwlee84/agent-skills`.

## Where this was hit

After authoring `skill-author`, ran
`npx skills@latest add daviddwlee84/agent-skills -g -s skill-author -y`
to install it globally. CLI reported "no matching skills" and listed
only `find-skills` + `skill-creator` (both from `skills/vendor/` because
the latter is at `skills/vendor/skill-creator/` which the fallback
recursive walk does find on its first pass — but it doesn't continue
into `skills/local/` after finding vendor entries). Adding
`--full-depth` fixed it. Found in commit `a365f30`'s preceding session.
