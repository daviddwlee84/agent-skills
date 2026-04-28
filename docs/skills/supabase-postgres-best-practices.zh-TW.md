# supabase-postgres-best-practices (vendored)

!!! note "Terminology rule (zh-TW pages)"
    技術名詞首次出現以「中文 (English original)」格式呈現，例：依賴注入
    (dependency injection)。**不自創翻譯**——若無公認譯名直接保留英文
    （如 `embedding`、`tokenizer`）。代碼、API 名、CLI flag、套件名、檔名一律不翻。

從
[supabase/agent-skills/skills/supabase-postgres-best-practices](https://github.com/supabase/agent-skills/tree/main/skills/supabase-postgres-best-practices)
vendor 過來（屬於 [`fullstack-nextjs`](index.md#fullstack-nextjs-series) series）。
透過 [`make sync`](https://github.com/daviddwlee84/agent-skills/blob/main/Makefile)
同步；不要在本機編輯
[`skills/vendor/fullstack-nextjs/supabase-postgres-best-practices/SKILL.md`](https://github.com/daviddwlee84/agent-skills/blob/main/skills/vendor/fullstack-nextjs/supabase-postgres-best-practices/SKILL.md)
—— 變更會在下次同步被蓋掉。

## Upstream frontmatter description

> Postgres performance optimization and best practices from Supabase. Use
> this skill when writing, reviewing, or optimizing Postgres queries, schema
> designs, or database configurations.

## 教什麼 (What it teaches)

橫跨 8 個分類的效能規則 —— query performance、index、connection
management、RLS、pooling —— 依影響度排序。每條規則含錯誤對正確的
SQL 範例、query plan 分析、以及目標效能 metric。是廣泛的
[`supabase`](supabase.md) skill (涵蓋整個產品表面) 的補充。

## 相關 fullstack-nextjs skill

- [`supabase`](supabase.md) —— Supabase 完整產品涵蓋 (auth、storage、edge fns、…)
- [`vercel-storage`](vercel-storage.md) —— Vercel 端整合 pattern

## Canonical SKILL.md

完整指示見
[skills/vendor/fullstack-nextjs/supabase-postgres-best-practices/SKILL.md](https://github.com/daviddwlee84/agent-skills/blob/main/skills/vendor/fullstack-nextjs/supabase-postgres-best-practices/SKILL.md)。
Upstream 來源：
[supabase/agent-skills](https://github.com/supabase/agent-skills)。
