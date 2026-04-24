# web-design-guidelines (vendored)

Vendored from
[vercel-labs/agent-skills/skills/web-design-guidelines](https://github.com/vercel-labs/agent-skills/tree/main/skills/web-design-guidelines)
(part of the [`fullstack-nextjs`](index.md#fullstack-nextjs-series) series).
Synced via [`make sync`](https://github.com/daviddwlee84/agent-skills/blob/main/Makefile);
do not edit
[`skills/vendor/fullstack-nextjs/web-design-guidelines/SKILL.md`](https://github.com/daviddwlee84/agent-skills/blob/main/skills/vendor/fullstack-nextjs/web-design-guidelines/SKILL.md)
locally — changes will be clobbered on the next sync.

## Upstream frontmatter description

> Review UI code for Web Interface Guidelines compliance. Use when asked
> to "review my UI", "check accessibility", "audit design", "review UX",
> or "check my site against best practices".

## What it teaches

A reviewer skill — fetches the latest Web Interface Guidelines from
`vercel-labs/web-interface-guidelines` and audits files against the rule
set, returning findings in `file:line` format. Covers a11y, perf, and UX.
Pairs naturally with [`shadcn`](shadcn.md) and [`react-best-practices`](react-best-practices.md).

## Related fullstack-nextjs skills

- [`shadcn`](shadcn.md) — UI components that this skill audits
- [`react-best-practices`](react-best-practices.md) — overlapping component-level review
- [`frontend-design`](frontend-design.md) — aesthetic direction (this skill is the auditor; that one is the creator)

## Canonical SKILL.md

See
[skills/vendor/fullstack-nextjs/web-design-guidelines/SKILL.md](https://github.com/daviddwlee84/agent-skills/blob/main/skills/vendor/fullstack-nextjs/web-design-guidelines/SKILL.md)
for the full instructions. Upstream source:
[vercel-labs/agent-skills](https://github.com/vercel-labs/agent-skills).
