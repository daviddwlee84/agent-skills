# Creating local skills

A local skill is a custom-authored skill maintained in this repo under
[`skills/local/<skill-name>/`](https://github.com/daviddwlee84/agent-skills/tree/main/skills/local).

## Scaffold a new skill

```bash
cd skills/local
npx skills@latest init [skill-name]
```

This creates `skills/local/<skill-name>/SKILL.md` with the required YAML
frontmatter (`name`, `description`).

Before writing the description, check the repo's
[Agent skill compatibility](../reference/agent-skill-compatibility.md) policy.
Local skills should target portable coding-agent limits: hyphen-case names
under 64 chars, descriptions under 1024 chars, and 120-500 chars preferred.

## Required structure

See [Conventions](../conventions.md) for the full layout rules. In short:

- `SKILL.md` — required, lean (under ~500 lines).
- `assets/` — templates the skill copies into target projects.
- `scripts/` — executable helpers (Bash 3.2 compatible).
- `references/` — long-form material loaded on demand.

## Author the SKILL.md following agentskills.io best practices

The two highest-leverage rules from the
[agentskills.io best practices](https://agentskills.io/skill-creation/best-practices):

1. **Procedures over declarations.** Tell the agent what to *do*, not what
   to *be*. A SKILL.md that says "follow these three steps" is much more
   reliable than one that says "be a careful and methodical helper".
2. **Defaults over menus.** Pick one workflow as the default; offer
   alternatives via flags or in `references/`. Letting the agent choose
   between three equivalent options at every step is a debugging nightmare.

A third rule we apply in this repo:

- **Bundle the workflow as a script if you can.** If the skill keeps asking
  the agent to perform the same multi-step procedure, write it as a shell
  script in `scripts/` and make the SKILL.md call the script. The
  [`project-knowledge-harness`](../skills/project-knowledge-harness.md)
  skill is the reference for this pattern.

## Add a docs page

Every local skill should also have a page under `docs/skills/<skill>.md`
that explains, for a human reader, what the skill is for, when it
triggers, and what it costs to use. The `SKILL.md` is the agent-facing
contract; the docs page is the human-facing pitch. Both are valuable.

When you create the docs page, also link it from
[`docs/skills/index.md`](../skills/index.md) and from `mkdocs.yml`'s `nav:`
block at the repo root.

## Test by installing into a scratch project

```bash
mkdir /tmp/scratch && cd /tmp/scratch
git init
npx skills@latest add daviddwlee84/agent-skills/skills
```

This pulls the new skill into `.agents/skills/` of a clean project so you
can verify the SKILL.md activates as you expect.
