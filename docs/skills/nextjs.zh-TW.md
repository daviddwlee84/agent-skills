# nextjs (vendored)

!!! note "Terminology rule (zh-TW pages)"
    技術名詞首次出現以「中文 (English original)」格式呈現，例：依賴注入
    (dependency injection)。**不自創翻譯**——若無公認譯名直接保留英文
    （如 `embedding`、`tokenizer`）。代碼、API 名、CLI flag、套件名、檔名一律不翻。

從
[vercel/vercel-plugin/skills/nextjs](https://github.com/vercel/vercel-plugin/tree/main/skills/nextjs)
vendor 過來（屬於 [`fullstack-nextjs`](index.md#fullstack-nextjs-series) series）。
透過 [`make sync`](https://github.com/daviddwlee84/agent-skills/blob/main/Makefile)
同步；不要在本機編輯
[`skills/vendor/fullstack-nextjs/nextjs/SKILL.md`](https://github.com/daviddwlee84/agent-skills/blob/main/skills/vendor/fullstack-nextjs/nextjs/SKILL.md)
—— 變更會在下次同步被蓋掉。

## Upstream frontmatter description

> Next.js App Router expert guidance. Use when building, debugging, or
> architecting Next.js applications — routing, Server Components, Server
> Actions, Cache Components, layouts, middleware/proxy, data fetching,
> rendering strategies, and deployment on Vercel.

## 教什麼 (What it teaches)

這個 repo 中旗艦級的 Next.js skill。出貨 18 KB 的 SKILL.md 加上
`references/` 底下 20+ 個 reference 檔（app-router-files、async-patterns、
hydration-error、parallel-routes、rsc-boundaries、…）以及一個
`overlay.yaml` metadata 層，包含 `pathPatterns`：`app/**`、`pages/**`、
`tailwind.config.*`、`tsconfig.json`。在編輯 Next.js code 時自動觸發。

## 相關 fullstack-nextjs skill

- [`shadcn`](shadcn.md) —— Next.js 之上的 UI component 層
- [`react-best-practices`](react-best-practices.md) —— TSX 層級的 review checklist
- [`vercel-storage`](vercel-storage.md) —— DB / Blob / KV 整合 pattern

## Canonical SKILL.md

完整指示見
[skills/vendor/fullstack-nextjs/nextjs/SKILL.md](https://github.com/daviddwlee84/agent-skills/blob/main/skills/vendor/fullstack-nextjs/nextjs/SKILL.md)。
Upstream 來源：
[vercel/vercel-plugin](https://github.com/vercel/vercel-plugin)。
