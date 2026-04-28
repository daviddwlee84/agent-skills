# react-best-practices (vendored)

!!! note "Terminology rule (zh-TW pages)"
    技術名詞首次出現以「中文 (English original)」格式呈現，例：依賴注入
    (dependency injection)。**不自創翻譯**——若無公認譯名直接保留英文
    （如 `embedding`、`tokenizer`）。代碼、API 名、CLI flag、套件名、檔名一律不翻。

從
[vercel/vercel-plugin/skills/react-best-practices](https://github.com/vercel/vercel-plugin/tree/main/skills/react-best-practices)
vendor 過來（屬於 [`fullstack-nextjs`](index.md#fullstack-nextjs-series) series）。
透過 [`make sync`](https://github.com/daviddwlee84/agent-skills/blob/main/Makefile)
同步；不要在本機編輯
[`skills/vendor/fullstack-nextjs/react-best-practices/SKILL.md`](https://github.com/daviddwlee84/agent-skills/blob/main/skills/vendor/fullstack-nextjs/react-best-practices/SKILL.md)
—— 變更會在下次同步被蓋掉。

## Upstream frontmatter description

> React best-practices reviewer for TSX files. Triggers after editing
> multiple TSX components to run a condensed quality checklist covering
> component structure, hooks usage, accessibility, performance, and
> TypeScript patterns.

## 教什麼 (What it teaches)

來自 Vercel Engineering、橫跨 8 個分類的 70+ 條規則。包含一條
`validate` 規則，把 legacy CSS-in-JS / MUI / Chakra 使用者推往
shadcn/ui + Tailwind，配合現代的 Vercel stack。在編輯
`src/components/**/*.tsx`、`app/components/**/*.tsx` 等時自動觸發。

## 相關 fullstack-nextjs skill

- [`nextjs`](nextjs.md) —— 同 upstream repo，更深的 Next.js 框架知識
- [`shadcn`](shadcn.md) —— 這個 skill 明確推薦的 component library

## Canonical SKILL.md

完整指示見
[skills/vendor/fullstack-nextjs/react-best-practices/SKILL.md](https://github.com/daviddwlee84/agent-skills/blob/main/skills/vendor/fullstack-nextjs/react-best-practices/SKILL.md)。
Upstream 來源：
[vercel/vercel-plugin](https://github.com/vercel/vercel-plugin)。另見
[Introducing: React Best Practices (Vercel blog)](https://vercel.com/blog/introducing-react-best-practices)。
