# skill-creator (vendored)

Vendored from
[anthropics/skills/skills/skill-creator](https://github.com/anthropics/skills/tree/main/skills/skill-creator).
Synced via [`make sync`](https://github.com/daviddwlee84/agent-skills/blob/main/Makefile);
do not edit
[`skills/vendor/skill-creator/SKILL.md`](https://github.com/daviddwlee84/agent-skills/blob/main/skills/vendor/skill-creator/SKILL.md)
locally — changes will be clobbered on the next sync.

## Upstream frontmatter description

> Create new skills, modify and improve existing skills, and measure
> skill performance. Use when users want to create a skill from scratch,
> edit, or optimize an existing skill, run evals to test a skill,
> benchmark skill performance with variance analysis, or optimize a
> skill's description for better triggering accuracy.

## What it teaches

Anthropic's own methodology for authoring skills, including:

- Evaluation harness for measuring how reliably a skill's `description`
  actually triggers on the prompts it should.
- Benchmarking with variance analysis (repeat runs to distinguish real
  gains from noise).
- Optimization loops for iterating on the `description` field until
  trigger rate meets target.

## `skill-creator` vs local `skill-author`

| Aspect | `skill-creator` (vendored, this) | [`skill-author`](skill-author.md) (local) |
|---|---|---|
| Focus | **Evaluation** — test cases, trigger-rate benchmarks, variance | **Authoring** — scaffolding, linting, agentskills.io best practices |
| Scripts | Eval harness, benchmarking | `new-skill.sh`, `lint-skill.sh` |
| When to use | After authoring, to measure & optimize | While writing the SKILL.md + references + scripts |

The two are complementary — use `skill-author` to build the skill, then
`skill-creator` to evaluate and tune its trigger description.

## Canonical SKILL.md

See
[skills/vendor/skill-creator/SKILL.md](https://github.com/daviddwlee84/agent-skills/blob/main/skills/vendor/skill-creator/SKILL.md)
for the full instructions. Upstream source:
[anthropics/skills](https://github.com/anthropics/skills).
