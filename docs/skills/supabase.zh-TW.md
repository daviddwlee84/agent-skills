# supabase (vendored)

!!! note "Terminology rule (zh-TW pages)"
    技術名詞首次出現以「中文 (English original)」格式呈現，例：依賴注入
    (dependency injection)。**不自創翻譯**——若無公認譯名直接保留英文
    （如 `embedding`、`tokenizer`）。代碼、API 名、CLI flag、套件名、檔名一律不翻。

從
[supabase/agent-skills/skills/supabase](https://github.com/supabase/agent-skills/tree/main/skills/supabase)
vendor 過來（屬於 [`fullstack-nextjs`](index.md#fullstack-nextjs-series) series）。
透過 [`make sync`](https://github.com/daviddwlee84/agent-skills/blob/main/Makefile)
同步；不要在本機編輯
[`skills/vendor/fullstack-nextjs/supabase/SKILL.md`](https://github.com/daviddwlee84/agent-skills/blob/main/skills/vendor/fullstack-nextjs/supabase/SKILL.md)
—— 變更會在下次同步被蓋掉。

## Upstream frontmatter description

> Use when doing ANY task involving Supabase. Triggers: Supabase products
> (Database, Auth, Edge Functions, Realtime, Storage, Vectors, Cron, Queues);
> client libraries and SSR integrations (supabase-js, @supabase/ssr) in
> Next.js, React, SvelteKit, Astro, Remix; auth issues (login, logout,
> sessions, JWT, cookies, getSession, getUser, getClaims, RLS); Supabase
> CLI or MCP server; schema changes, migrations, security audits, Postgres
> extensions (pg_graphql, pg_cron, pg_vector).

## 教什麼 (What it teaches)

唯一的 canonical Supabase skill。涵蓋整個 Supabase 表面 + 顯式的
`@supabase/ssr` Next.js pattern。包含一份 Supabase 特有陷阱的安全性
checklist（例如：**絕不在 JWT-based 授權中使用 `user_metadata`**、
刪除使用者並不會使 token 失效、暴露的 schema 預設啟用 RLS）。

## 相關 fullstack-nextjs skill

- [`supabase-postgres-best-practices`](supabase-postgres-best-practices.md) —— 同 upstream 的效能規則
- [`vercel-storage`](vercel-storage.md) —— Vercel 端整合 pattern (它的 pathPatterns 包含 `supabase/**`)
- [`nextjs`](nextjs.md) —— 使用 `@supabase/ssr` 的 App Router 環境

## Canonical SKILL.md

完整指示見
[skills/vendor/fullstack-nextjs/supabase/SKILL.md](https://github.com/daviddwlee84/agent-skills/blob/main/skills/vendor/fullstack-nextjs/supabase/SKILL.md)。
Upstream 來源：
[supabase/agent-skills](https://github.com/supabase/agent-skills)。
