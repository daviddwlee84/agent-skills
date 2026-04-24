# react-best-practices (vendored)

Vendored from
[vercel/vercel-plugin/skills/react-best-practices](https://github.com/vercel/vercel-plugin/tree/main/skills/react-best-practices)
(part of the [`fullstack-nextjs`](index.md#fullstack-nextjs-series) series).
Synced via [`make sync`](https://github.com/daviddwlee84/agent-skills/blob/main/Makefile);
do not edit
[`skills/vendor/fullstack-nextjs/react-best-practices/SKILL.md`](https://github.com/daviddwlee84/agent-skills/blob/main/skills/vendor/fullstack-nextjs/react-best-practices/SKILL.md)
locally — changes will be clobbered on the next sync.

## Upstream frontmatter description

> React best-practices reviewer for TSX files. Triggers after editing
> multiple TSX components to run a condensed quality checklist covering
> component structure, hooks usage, accessibility, performance, and
> TypeScript patterns.

## What it teaches

70+ rules across 8 categories from Vercel Engineering. Includes a `validate`
rule that nudges legacy CSS-in-JS / MUI / Chakra users toward shadcn/ui +
Tailwind for the modern Vercel stack. Auto-triggers when editing
`src/components/**/*.tsx`, `app/components/**/*.tsx` etc.

## Related fullstack-nextjs skills

- [`nextjs`](nextjs.md) — same upstream repo, deeper Next.js framework knowledge
- [`shadcn`](shadcn.md) — component library this skill explicitly recommends

## Canonical SKILL.md

See
[skills/vendor/fullstack-nextjs/react-best-practices/SKILL.md](https://github.com/daviddwlee84/agent-skills/blob/main/skills/vendor/fullstack-nextjs/react-best-practices/SKILL.md)
for the full instructions. Upstream source:
[vercel/vercel-plugin](https://github.com/vercel/vercel-plugin). See also
[Introducing: React Best Practices (Vercel blog)](https://vercel.com/blog/introducing-react-best-practices).
