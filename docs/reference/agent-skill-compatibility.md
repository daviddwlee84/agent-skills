# Agent skill compatibility

This page records the cross-agent `SKILL.md` constraints this repo targets.
The goal is practical portability across coding agents, not the broadest set
of optional product-specific extensions.

## Baseline we target

Use the [Agent Skills specification](https://agentskills.io/specification) as
the portable baseline:

| Field | Repo policy |
|---|---|
| `name` | Required, 1-64 chars, lowercase letters/digits with single hyphen separators, no leading/trailing hyphen, no `--`, should match the skill directory |
| `description` | Required, 1-1024 chars, describes both what the skill does and when to use it |
| `SKILL.md` body | Keep under ~500 lines; move long detail into `references/` |
| Optional frontmatter | Allowed only when a target agent needs it; keep local skills portable by default |

Description budget tiers used by `skill-author`:

| Tier | Length | Meaning |
|---|---:|---|
| Green | 120-500 chars | Preferred for local skills: enough trigger surface without context bloat |
| Yellow | 501-900 chars | Valid, but context-heavy; move details to the body or references |
| Orange | 901-1024 chars | Valid, but close to hard loader limits |
| Red | >1024 chars | Invalid for Codex/Cursor/spec-aligned validators |

Also make the first 60 characters useful. The `npx skills` installer truncates
picker hints to 60 characters, and Codex may shorten descriptions when the
installed skill list is large.

## Agent notes

| Tool | Preference / constraint | Link |
|---|---|---|
| Agent Skills spec | Defines the portable directory layout, frontmatter fields, 64-char `name`, 1024-char `description`, optional `scripts/`, `references/`, and `assets/`. | [Specification](https://agentskills.io/specification) |
| Codex | Starts with each skill's name, description, and path, then loads full `SKILL.md` only when selected. The initial skills list has a context budget; descriptions should be concise and front-loaded. Codex can use optional `agents/openai.yaml` for UI metadata and invocation policy. | [Codex skills docs](https://developers.openai.com/codex/skills/create-skill) |
| Claude Code | Follows the open standard and adds fields such as `when_to_use`, `disable-model-invocation`, `user-invocable`, `allowed-tools`, `context`, and `hooks`. It truncates combined `description`/`when_to_use` listing text at 1,536 chars. | [Claude Code skills docs](https://code.claude.com/docs/en/skills) |
| Cursor | Uses `SKILL.md` skills with the same practical 64-char `name` and 1024-char `description` budget in its managed `create-skill` guidance. It also supports `disable-model-invocation` for explicit-only skills. | [Cursor skills docs](https://cursor.com/docs/skills) |
| OpenCode | Recognizes `.opencode/skills`, `.claude/skills`, and `.agents/skills`; only specific frontmatter fields are recognized, unknown fields are ignored. It enforces 1-64 char names and 1-1024 char descriptions. | [OpenCode Agent Skills](https://opencode.ai/docs/skills/) |
| `npx skills` | Installer/distributor. Reads `name` and `description` from `SKILL.md`, shows only a 60-char description hint in the picker, and uses `.claude-plugin/marketplace.json` for grouping. | [npx skills metadata model](npx-skills-metadata.md) |

## How this repo applies it

- Local skills should keep `description` in the green tier unless there is a
  concrete trigger-coverage reason to go longer.
- `skills/local/skill-author/scripts/lint-skill.sh` enforces the portable hard
  limits: hyphen-case names, 64-char names, and 1024-char descriptions. It also
  reports yellow/orange tier notes without failing strict mode.
- `skills/local/skill-author/assets/SKILL.md.template` tells new authors to
  target 120-500 chars and never exceed 1024.
- Detailed trigger examples belong in `SKILL.md` body or `references/`, not in
  an oversized frontmatter description.
- Product-specific metadata is acceptable when needed, but should be deliberate:
  prefer portable frontmatter for local skills, leave vendored upstream metadata
  intact, and document any target-agent-only field in the skill body.

## Incident that set the policy

`mkdocs-site-bootstrap` previously had a 1106-character frontmatter
`description`. Codex 0.128.0 skipped it as invalid because the description
exceeded 1024 characters. We shortened the description to 489 characters and
updated `skill-author` so future local skills are caught before install-time
loader failures.
