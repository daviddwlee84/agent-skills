# shadcn (vendored)

Vendored from
[vercel/vercel-plugin/skills/shadcn](https://github.com/vercel/vercel-plugin/tree/main/skills/shadcn)
(part of the [`fullstack-nextjs`](index.md#fullstack-nextjs-series) series).
Synced via [`make sync`](https://github.com/daviddwlee84/agent-skills/blob/main/Makefile);
do not edit
[`skills/vendor/fullstack-nextjs/shadcn/SKILL.md`](https://github.com/daviddwlee84/agent-skills/blob/main/skills/vendor/fullstack-nextjs/shadcn/SKILL.md)
locally — changes will be clobbered on the next sync.

## Upstream frontmatter description

> shadcn/ui expert guidance — CLI, component installation, composition
> patterns, custom registries, theming, Tailwind CSS integration, and
> high-quality interface design. Use when initializing shadcn, adding
> components, composing product UI, building custom registries, configuring
> themes, or troubleshooting component issues.

## What it teaches

Covers the full shadcn workflow: `init`, `add`, `build`, `search`, `migrate`,
`info`, `view`, custom registries, theming, Tailwind integration. Triggers on
`components.json`, `components/ui/**`, and any `npx shadcn@latest <subcmd>`.
Includes a `validate` rule warning about Base UI / Radix incompatibility with
AI Elements.

## Related fullstack-nextjs skills

- [`nextjs`](nextjs.md) — App Router context where shadcn components live
- [`web-design-guidelines`](web-design-guidelines.md) — a11y/perf review for shadcn UIs
- [`frontend-design`](frontend-design.md) — aesthetic direction beyond default shadcn looks

## Canonical SKILL.md

See
[skills/vendor/fullstack-nextjs/shadcn/SKILL.md](https://github.com/daviddwlee84/agent-skills/blob/main/skills/vendor/fullstack-nextjs/shadcn/SKILL.md)
for the full instructions. Upstream source:
[vercel/vercel-plugin](https://github.com/vercel/vercel-plugin) (shadcn was
acquired by Vercel; this is the same canonical guidance redistributed under
the Vercel plugin).
