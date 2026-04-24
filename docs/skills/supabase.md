# supabase (vendored)

Vendored from
[supabase/agent-skills/skills/supabase](https://github.com/supabase/agent-skills/tree/main/skills/supabase)
(part of the [`fullstack-nextjs`](index.md#fullstack-nextjs-series) series).
Synced via [`make sync`](https://github.com/daviddwlee84/agent-skills/blob/main/Makefile);
do not edit
[`skills/vendor/fullstack-nextjs/supabase/SKILL.md`](https://github.com/daviddwlee84/agent-skills/blob/main/skills/vendor/fullstack-nextjs/supabase/SKILL.md)
locally — changes will be clobbered on the next sync.

## Upstream frontmatter description

> Use when doing ANY task involving Supabase. Triggers: Supabase products
> (Database, Auth, Edge Functions, Realtime, Storage, Vectors, Cron, Queues);
> client libraries and SSR integrations (supabase-js, @supabase/ssr) in
> Next.js, React, SvelteKit, Astro, Remix; auth issues (login, logout,
> sessions, JWT, cookies, getSession, getUser, getClaims, RLS); Supabase
> CLI or MCP server; schema changes, migrations, security audits, Postgres
> extensions (pg_graphql, pg_cron, pg_vector).

## What it teaches

The single canonical Supabase skill. Covers the entire Supabase surface +
explicit `@supabase/ssr` Next.js patterns. Includes a security checklist for
Supabase-specific traps (e.g. **never use `user_metadata` in JWT-based
authorization**, deleting a user does not invalidate tokens, RLS-by-default
on exposed schemas).

## Related fullstack-nextjs skills

- [`supabase-postgres-best-practices`](supabase-postgres-best-practices.md) — performance rules from same upstream
- [`vercel-storage`](vercel-storage.md) — Vercel-side integration patterns (its pathPatterns include `supabase/**`)
- [`nextjs`](nextjs.md) — App Router context where `@supabase/ssr` is used

## Canonical SKILL.md

See
[skills/vendor/fullstack-nextjs/supabase/SKILL.md](https://github.com/daviddwlee84/agent-skills/blob/main/skills/vendor/fullstack-nextjs/supabase/SKILL.md)
for the full instructions. Upstream source:
[supabase/agent-skills](https://github.com/supabase/agent-skills).
