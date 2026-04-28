# shadcn (vendored)

!!! note "Terminology rule (zh-TW pages)"
    技術名詞首次出現以「中文 (English original)」格式呈現，例：依賴注入
    (dependency injection)。**不自創翻譯**——若無公認譯名直接保留英文
    （如 `embedding`、`tokenizer`）。代碼、API 名、CLI flag、套件名、檔名一律不翻。

從
[vercel/vercel-plugin/skills/shadcn](https://github.com/vercel/vercel-plugin/tree/main/skills/shadcn)
vendor 過來（屬於 [`fullstack-nextjs`](index.md#fullstack-nextjs-series) series）。
透過 [`make sync`](https://github.com/daviddwlee84/agent-skills/blob/main/Makefile)
同步；不要在本機編輯
[`skills/vendor/fullstack-nextjs/shadcn/SKILL.md`](https://github.com/daviddwlee84/agent-skills/blob/main/skills/vendor/fullstack-nextjs/shadcn/SKILL.md)
—— 變更會在下次同步被蓋掉。

## Upstream frontmatter description

> shadcn/ui expert guidance — CLI, component installation, composition
> patterns, custom registries, theming, Tailwind CSS integration, and
> high-quality interface design. Use when initializing shadcn, adding
> components, composing product UI, building custom registries, configuring
> themes, or troubleshooting component issues.

## 教什麼 (What it teaches)

涵蓋 shadcn 完整工作流程：`init`、`add`、`build`、`search`、`migrate`、
`info`、`view`、custom registry、theming、Tailwind 整合。在
`components.json`、`components/ui/**`、以及任何 `npx shadcn@latest <subcmd>`
時觸發。包含一條 `validate` 規則警告 Base UI / Radix 與 AI Elements
的不相容性。

## 相關 fullstack-nextjs skill

- [`nextjs`](nextjs.md) —— shadcn component 所在的 App Router 環境
- [`web-design-guidelines`](web-design-guidelines.md) —— 對 shadcn UI 做 a11y/perf review
- [`frontend-design`](frontend-design.md) —— 超出預設 shadcn 視覺的美學方向

## Canonical SKILL.md

完整指示見
[skills/vendor/fullstack-nextjs/shadcn/SKILL.md](https://github.com/daviddwlee84/agent-skills/blob/main/skills/vendor/fullstack-nextjs/shadcn/SKILL.md)。
Upstream 來源：
[vercel/vercel-plugin](https://github.com/vercel/vercel-plugin)
（shadcn 已被 Vercel 收購；這是同樣的 canonical 指引在 Vercel plugin
下重新散布）。
