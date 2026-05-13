# Web & Fullstack

Web app development — Next.js / React / Tailwind / shadcn / Supabase /
Vercel / Postgres / browser automation / GitHub workflow / web quality
audits. This is the most-populated domain in this repo, anchored by the
[`fullstack-nextjs`](../../skills/index.md) series.

## Skills in this repo

### Local

| Skill | One-line | Notes |
|---|---|---|
| _none direct_ | | The local skill lineup leans towards ML / docs / process tooling rather than web frameworks. |

### Vendored

`fullstack-nextjs` series (9 skills, all from official orgs):

| Skill | Upstream | Series |
|---|---|---|
| [`nextjs`](../../skills/nextjs.md) | [`vercel/vercel-plugin`](https://github.com/vercel/vercel-plugin) | `fullstack-nextjs` |
| [`shadcn`](../../skills/shadcn.md) | [`vercel/vercel-plugin`](https://github.com/vercel/vercel-plugin) | `fullstack-nextjs` |
| [`react-best-practices`](../../skills/react-best-practices.md) | [`vercel/vercel-plugin`](https://github.com/vercel/vercel-plugin) | `fullstack-nextjs` |
| [`vercel-storage`](../../skills/vercel-storage.md) | [`vercel/vercel-plugin`](https://github.com/vercel/vercel-plugin) | `fullstack-nextjs` |
| [`supabase`](../../skills/supabase.md) | [`supabase/agent-skills`](https://github.com/supabase/agent-skills) | `fullstack-nextjs` |
| [`supabase-postgres-best-practices`](../../skills/supabase-postgres-best-practices.md) | [`supabase/agent-skills`](https://github.com/supabase/agent-skills) | `fullstack-nextjs` |
| [`web-design-guidelines`](../../skills/web-design-guidelines.md) | [`vercel-labs/agent-skills`](https://github.com/vercel-labs/agent-skills) | `fullstack-nextjs` |
| [`frontend-design`](../../skills/frontend-design.md) | [`anthropics/skills`](https://github.com/anthropics/skills) | `fullstack-nextjs` |
| [`webapp-testing`](../../skills/webapp-testing.md) | [`anthropics/skills`](https://github.com/anthropics/skills) | `fullstack-nextjs` |

GitHub workflow + web quality (Warp Oz, see [`docs/reference/warp-oz-skills.md`](../../reference/warp-oz-skills.md)):

| Skill | Upstream | Notes |
|---|---|---|
| `ci-fix`, `create-pull-request`, `github-bug-report-triage`, `github-issue-dedupe` | [`warpdotdev/oz-skills`](https://github.com/warpdotdev/oz-skills) | All in `github-workflow` plugin grouping. |
| `web-accessibility-audit`, `web-performance-audit` | [`warpdotdev/oz-skills`](https://github.com/warpdotdev/oz-skills) | `web-performance-audit` requires the Chrome DevTools MCP. |

## External skills (manual install)

--8<-- "_snippets/external-install.md"

| Skill / Plugin | Upstream | Status | Why this status | Install hint |
|---|---|---|---|---|
| Other `vercel/vercel-plugin` skills | [`vercel/vercel-plugin`](https://github.com/vercel/vercel-plugin) | `evaluated` | We already vendored 4 of them into `fullstack-nextjs`. Remaining ones (e.g. `tailwind`, `vercel-ai-sdk`, etc.) are candidates if needed. | `npx skills@latest add vercel/vercel-plugin -s <skill>` |
| Remaining `vercel-labs/agent-skills` | [`vercel-labs/agent-skills`](https://github.com/vercel-labs/agent-skills) | `evaluated` | We vendored `web-design-guidelines`. Others are similar audit-style skills. | `npx skills@latest add vercel-labs/agent-skills -s <skill>` |
| Other `warpdotdev/oz-skills` (9 skipped) | [`warpdotdev/oz-skills`](https://github.com/warpdotdev/oz-skills) | `skipped` | Skipped per [`docs/reference/warp-oz-skills.md`](../../reference/warp-oz-skills.md): `mcp-builder` (duplicate), `webapp-testing` (duplicate), `scheduler` (too narrow), Slack-/BigQuery-specific ones. | (not vendored) |

## MCP servers

| Name | Upstream | Status | Auth | Records |
|---|---|---|---|---|
| `chrome-devtools` | [`@modelcontextprotocol/server-chrome-devtools`](https://www.npmjs.com/package/chrome-devtools-mcp) | `evaluated` | Local stdio | _no per-MCP record yet — required by `web-performance-audit`_ |

## Backlog (TODO `P?` items)

See the [`P?` lane in `TODO.md`](https://github.com/daviddwlee84/agent-skills/blob/main/TODO.md):

- `[?/M]` **Playwright skill** — web automation, testing, and website-cloning workflows realistic for agents to maintain.
- `[?/L]` **Sibling docs-stack skills (docusaurus / vitepress / hugo / sphinx)** — paired with the existing `mkdocs-site-bootstrap` skill.

## See also

- [`docs/reference/browser-automation-skills.md`](../../reference/browser-automation-skills.md) — Playwright vs agent-browser vs browser-use vs stagehand vs Playwright MCP comparison.
- [`docs/reference/warp-oz-skills.md`](../../reference/warp-oz-skills.md) — Warp Oz GitHub-workflow + web-quality skills.
- [`docs/skills/index.md`](../../skills/index.md#fullstack-nextjs-series) — full Skills overview with the `fullstack-nextjs` series tables.
