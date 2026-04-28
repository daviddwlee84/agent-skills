# vercel-storage (vendored)

!!! note "Terminology rule (zh-TW pages)"
    技術名詞首次出現以「中文 (English original)」格式呈現，例：依賴注入
    (dependency injection)。**不自創翻譯**——若無公認譯名直接保留英文
    （如 `embedding`、`tokenizer`）。代碼、API 名、CLI flag、套件名、檔名一律不翻。

從
[vercel/vercel-plugin/skills/vercel-storage](https://github.com/vercel/vercel-plugin/tree/main/skills/vercel-storage)
vendor 過來（屬於 [`fullstack-nextjs`](index.md#fullstack-nextjs-series) series）。
透過 [`make sync`](https://github.com/daviddwlee84/agent-skills/blob/main/Makefile)
同步；不要在本機編輯
[`skills/vendor/fullstack-nextjs/vercel-storage/SKILL.md`](https://github.com/daviddwlee84/agent-skills/blob/main/skills/vendor/fullstack-nextjs/vercel-storage/SKILL.md)
—— 變更會在下次同步被蓋掉。

## Upstream frontmatter description

> Vercel storage expert guidance — Blob, Edge Config, and Marketplace
> storage (Neon Postgres, Upstash Redis). Use when choosing, configuring,
> or using data storage with Vercel applications.

## 教什麼 (What it teaches)

Vercel app 的儲存選擇 + 整合。值得注意的是它的 `pathPatterns` 包含
`supabase/**`、`lib/supabase.*`、`prisma/schema.prisma`、`prisma/**`
—— 所以這個 skill 在 Supabase 跟 Prisma project 也會自動觸發，
不只是 Vercel 原生 storage。

## 相關 fullstack-nextjs skill

- [`supabase`](supabase.md) —— 超出整合層級時的 Supabase 完整涵蓋
- [`supabase-postgres-best-practices`](supabase-postgres-best-practices.md) —— Postgres 端的效能規則

## Canonical SKILL.md

完整指示見
[skills/vendor/fullstack-nextjs/vercel-storage/SKILL.md](https://github.com/daviddwlee84/agent-skills/blob/main/skills/vendor/fullstack-nextjs/vercel-storage/SKILL.md)。
Upstream 來源：
[vercel/vercel-plugin](https://github.com/vercel/vercel-plugin)。
