# Conventions

These are the rules every local skill in this repo follows. They exist so
the package shipped via `npx skills` stays predictable and so adding a new
skill is mechanical, not a design exercise.

## Local skill layout

Each `skills/local/<skill>/` directory should contain:

- **`SKILL.md`** — required, with YAML frontmatter (`name`, `description`)
  and a body that follows the
  [agentskills.io best practices](https://agentskills.io/skill-creation/best-practices)
  (lean SKILL.md under ~500 lines, defaults over menus, procedures over
  declarations).
- **`assets/`** — templates the skill copies into a target project
  (e.g. `TODO.md.template`, `pitfall-doc.md.template`).
- **`scripts/`** — executable helpers the agent should invoke instead of
  re-implementing logic in chat. Bash 3.2 compatible (so they run on stock
  macOS without homebrew bash).
- **`references/`** — long-form material the agent loads on demand
  (decision tables, schema cheatsheets, anti-pattern lists). Push detail
  here rather than swelling `SKILL.md`.

## Mirror scripts to top-level `scripts/`

Where a skill ships scripts that this repo also wants to run directly
(currently only [`project-knowledge-harness`](skills/project-knowledge-harness.md)),
copy them into the top-level [`scripts/`](reference/scripts.md) directory
so `make` targets and CI can invoke them. Keep the canonical copy inside
the skill so the package shipped via `npx skills` stays self-contained.

The pair must stay byte-identical. The repo doesn't (yet) enforce this in
CI; if you edit one, edit the other in the same commit.

## Vendor skill layout

`skills/vendor/<skill>/` mirrors the upstream layout exactly. Don't edit
vendored skills in place — modifications get overwritten by `make sync`.
If you need to customize a vendored skill, fork it into `skills/local/`
and update [`vendor.yaml`](https://github.com/daviddwlee84/agent-skills/blob/main/vendor.yaml)
to drop the upstream entry.

## Documentation

Every local skill should also have a page under `docs/skills/<skill>.md`.
The skill's `SKILL.md` is for the agent (concise, machine-aimed); the
`docs/skills/<skill>.md` page is for humans deciding whether to use it.
Both surfaces are valuable — don't try to merge them.

Long-form references that the agent loads on demand
(`skills/local/<skill>/references/*.md`) can be mirrored or summarized
under `docs/reference/` when the audience extends to humans browsing the
site, but the canonical copy still lives next to `SKILL.md`.

## Personal scratch areas

`Collections.md` and `notes/` at the repo root are personal scratch space
for the maintainer and are intentionally not part of the published docs
site or the agent-facing surface. Don't link into them from `SKILL.md` or
from any docs page.
