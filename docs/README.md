# Local Skills

This directory documents the custom-authored skills under
[`skills/local/`](../skills/local/) — what each one is for, how it's
structured, and how to use the bundled scripts. Vendored skills under
[`skills/vendor/`](../skills/vendor/) are documented by their upstream
repositories (see [`vendor.yaml`](../vendor.yaml)).

## Index

| Skill | One-line | Detailed doc |
|---|---|---|
| [`project-knowledge-harness`](../skills/local/project-knowledge-harness/) | TODO + backlog + pitfalls structure with a bundled validator/init/promote toolkit | [`project-knowledge-harness.md`](project-knowledge-harness.md) |
| [`quantatitive-factor-researcher`](../skills/local/quantatitive-factor-researcher/) | Quantitative factor research persona for Python-based strategy work | [`quantatitive-factor-researcher.md`](quantatitive-factor-researcher.md) |

## Conventions for local skills in this repo

Each `skills/local/<skill>/` directory should contain:

- `SKILL.md` — required, with YAML frontmatter (`name`, `description`)
  and a body that follows the
  [agentskills.io best practices](https://agentskills.io/skill-creation/best-practices)
  (lean SKILL.md, defaults over menus, procedures over declarations).
- `assets/` — templates the skill copies into a target project.
- `scripts/` — executable helpers the agent should invoke instead of
  re-implementing logic in chat.
- `references/` — long-form material the agent loads on demand
  (e.g., schema cheatsheets, decision tables); keep `SKILL.md` itself
  under ~500 lines and push detail here.

Where a skill ships scripts that the host repo also wants to use directly
(as is the case for `project-knowledge-harness`), copy them into the
top-level [`scripts/`](../scripts/) directory so `make` targets can call
them; keep the canonical copy inside the skill so the package shipped via
`npx skills` stays self-contained.
