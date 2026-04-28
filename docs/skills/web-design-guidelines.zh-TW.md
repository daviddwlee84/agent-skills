# web-design-guidelines (vendored)

!!! note "Terminology rule (zh-TW pages)"
    技術名詞首次出現以「中文 (English original)」格式呈現，例:依賴注入
    (dependency injection)。**不自創翻譯**——若無公認譯名直接保留英文
    （如 `embedding`、`tokenizer`）。代碼、API 名、CLI flag、套件名、檔名一律不翻。

從
[vercel-labs/agent-skills/skills/web-design-guidelines](https://github.com/vercel-labs/agent-skills/tree/main/skills/web-design-guidelines)
vendor 過來（屬於 [`fullstack-nextjs`](index.md#fullstack-nextjs-series) series）。
透過 [`make sync`](https://github.com/daviddwlee84/agent-skills/blob/main/Makefile)
同步；不要在本機編輯
[`skills/vendor/fullstack-nextjs/web-design-guidelines/SKILL.md`](https://github.com/daviddwlee84/agent-skills/blob/main/skills/vendor/fullstack-nextjs/web-design-guidelines/SKILL.md)
—— 變更會在下次同步被蓋掉。

## Upstream frontmatter description

> Review UI code for Web Interface Guidelines compliance. Use when asked
> to "review my UI", "check accessibility", "audit design", "review UX",
> or "check my site against best practices".

## 教什麼 (What it teaches)

reviewer 角色的 skill —— 從 `vercel-labs/web-interface-guidelines`
拉最新的 Web Interface Guidelines，依規則集稽核 (audit) 檔案，
以 `file:line` 格式回傳發現。涵蓋 a11y、perf、UX。
與 [`shadcn`](shadcn.md) 跟
[`react-best-practices`](react-best-practices.md) 自然搭配。

## 相關 fullstack-nextjs skill

- [`shadcn`](shadcn.md) —— 這個 skill 稽核的 UI component
- [`react-best-practices`](react-best-practices.md) —— 重疊的 component 級 review
- [`frontend-design`](frontend-design.md) —— 美學方向（這個 skill 是稽核者；那個是創作者）

## Canonical SKILL.md

完整指示見
[skills/vendor/fullstack-nextjs/web-design-guidelines/SKILL.md](https://github.com/daviddwlee84/agent-skills/blob/main/skills/vendor/fullstack-nextjs/web-design-guidelines/SKILL.md)。
Upstream 來源：
[vercel-labs/agent-skills](https://github.com/vercel-labs/agent-skills)。
