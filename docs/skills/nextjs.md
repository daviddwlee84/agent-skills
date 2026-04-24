# nextjs (vendored)

Vendored from
[vercel/vercel-plugin/skills/nextjs](https://github.com/vercel/vercel-plugin/tree/main/skills/nextjs)
(part of the [`fullstack-nextjs`](index.md#fullstack-nextjs-series) series).
Synced via [`make sync`](https://github.com/daviddwlee84/agent-skills/blob/main/Makefile);
do not edit
[`skills/vendor/fullstack-nextjs/nextjs/SKILL.md`](https://github.com/daviddwlee84/agent-skills/blob/main/skills/vendor/fullstack-nextjs/nextjs/SKILL.md)
locally — changes will be clobbered on the next sync.

## Upstream frontmatter description

> Next.js App Router expert guidance. Use when building, debugging, or
> architecting Next.js applications — routing, Server Components, Server
> Actions, Cache Components, layouts, middleware/proxy, data fetching,
> rendering strategies, and deployment on Vercel.

## What it teaches

The flagship Next.js skill in this repo. Ships an 18 KB SKILL.md plus 20+
reference files under `references/` (app-router-files, async-patterns,
hydration-error, parallel-routes, rsc-boundaries, …) and an `overlay.yaml`
metadata layer with `pathPatterns` for `app/**`, `pages/**`,
`tailwind.config.*`, `tsconfig.json`. Triggers automatically when editing
Next.js code.

## Related fullstack-nextjs skills

- [`shadcn`](shadcn.md) — UI component layer on top of Next.js
- [`react-best-practices`](react-best-practices.md) — TSX-level review checklist
- [`vercel-storage`](vercel-storage.md) — DB / Blob / KV integration patterns

## Canonical SKILL.md

See
[skills/vendor/fullstack-nextjs/nextjs/SKILL.md](https://github.com/daviddwlee84/agent-skills/blob/main/skills/vendor/fullstack-nextjs/nextjs/SKILL.md)
for the full instructions. Upstream source:
[vercel/vercel-plugin](https://github.com/vercel/vercel-plugin).
