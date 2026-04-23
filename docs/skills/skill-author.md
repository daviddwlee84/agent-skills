# skill-author

Authoring helper for **new agent skills**. Ships:

- A scaffolder ([`new-skill.sh`](https://github.com/daviddwlee84/agent-skills/blob/main/skills/local/skill-author/scripts/new-skill.sh))
  that creates `skills/local/<name>/` with the standard layout pre-seeded.
- A linter ([`lint-skill.sh`](https://github.com/daviddwlee84/agent-skills/blob/main/skills/local/skill-author/scripts/lint-skill.sh))
  that checks frontmatter, script hygiene, and reference reachability.
- Two reference docs that condense the agentskills.io guides:
  [authoring-patterns.md](https://github.com/daviddwlee84/agent-skills/blob/main/skills/local/skill-author/references/authoring-patterns.md)
  and [script-design.md](https://github.com/daviddwlee84/agent-skills/blob/main/skills/local/skill-author/references/script-design.md).
- A repo-specific conventions reference
  ([this-repo-conventions.md](https://github.com/daviddwlee84/agent-skills/blob/main/skills/local/skill-author/references/this-repo-conventions.md))
  that explains layout, mirroring, and bash 3.2 compatibility.
- Templates for SKILL.md, reference docs, bash scripts (with
  `--help` / `--dry-run` / strict-mode boilerplate), and Python scripts (with
  PEP 723 inline deps).

## When to use this vs `skill-creator`

| Task | Use |
|---|---|
| "I want to make a new skill for X" | **skill-author** |
| Scaffold SKILL.md / a reference / a script | **skill-author** |
| Lint a draft skill | **skill-author** |
| Skill isn't triggering when expected | `skill-creator` (description optimization) |
| Run test cases / benchmark a skill | `skill-creator` (eval loop) |

If both apply, start with `skill-author`, then hand off to `skill-creator` once
the structure is right.

## Quick start

```bash
# 1. Scaffold
bash skills/local/skill-author/scripts/new-skill.sh my-skill

# 2. Edit skills/local/my-skill/SKILL.md to fill in the description and workflow

# 3. Lint
bash skills/local/skill-author/scripts/lint-skill.sh skills/local/my-skill

# 4. (Optional) hand off to skill-creator for quantitative validation
```

## Why a separate skill?

`skill-creator` (the Anthropic-published skill bundled at `.agents/skills/`) is
the canonical authority for skill creation, but it's heavily focused on the
**eval/iterate loop**: spawning subagents, grading, benchmarking, optimizing
the description triggering rate. `skill-author` covers the **authoring
patterns** that the agentskills.io best-practices and using-scripts pages
document — gotchas sections, output templates, validation loops, calibrated
specificity, and agentic CLI design — plus repo-specific conventions and
working scaffolder/linter scripts.

The two are complementary and explicitly cross-reference each other.

## Canonical SKILL.md

See [skills/local/skill-author/SKILL.md](https://github.com/daviddwlee84/agent-skills/blob/main/skills/local/skill-author/SKILL.md)
for the full triggering description and workflow.
