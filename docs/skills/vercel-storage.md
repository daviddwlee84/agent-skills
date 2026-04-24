# vercel-storage (vendored)

Vendored from
[vercel/vercel-plugin/skills/vercel-storage](https://github.com/vercel/vercel-plugin/tree/main/skills/vercel-storage)
(part of the [`fullstack-nextjs`](index.md#fullstack-nextjs-series) series).
Synced via [`make sync`](https://github.com/daviddwlee84/agent-skills/blob/main/Makefile);
do not edit
[`skills/vendor/fullstack-nextjs/vercel-storage/SKILL.md`](https://github.com/daviddwlee84/agent-skills/blob/main/skills/vendor/fullstack-nextjs/vercel-storage/SKILL.md)
locally — changes will be clobbered on the next sync.

## Upstream frontmatter description

> Vercel storage expert guidance — Blob, Edge Config, and Marketplace
> storage (Neon Postgres, Upstash Redis). Use when choosing, configuring,
> or using data storage with Vercel applications.

## What it teaches

Storage selection + integration for Vercel apps. Notably its `pathPatterns`
include `supabase/**`, `lib/supabase.*`, `prisma/schema.prisma`, `prisma/**`
— so the skill auto-triggers on Supabase and Prisma projects too, not just
on Vercel-native storage.

## Related fullstack-nextjs skills

- [`supabase`](supabase.md) — full Supabase coverage when you go beyond integration
- [`supabase-postgres-best-practices`](supabase-postgres-best-practices.md) — Postgres-side performance rules

## Canonical SKILL.md

See
[skills/vendor/fullstack-nextjs/vercel-storage/SKILL.md](https://github.com/daviddwlee84/agent-skills/blob/main/skills/vendor/fullstack-nextjs/vercel-storage/SKILL.md)
for the full instructions. Upstream source:
[vercel/vercel-plugin](https://github.com/vercel/vercel-plugin).
