# frontend-design (vendored)

!!! note "Terminology rule (zh-TW pages)"
    技術名詞首次出現以「中文 (English original)」格式呈現，例：依賴注入
    (dependency injection)。**不自創翻譯**——若無公認譯名直接保留英文
    （如 `embedding`、`tokenizer`）。代碼、API 名、CLI flag、套件名、檔名一律不翻。

從
[anthropics/skills/skills/frontend-design](https://github.com/anthropics/skills/tree/main/skills/frontend-design)
vendor 過來（屬於 [`fullstack-nextjs`](index.md#fullstack-nextjs-series) series）。
透過 [`make sync`](https://github.com/daviddwlee84/agent-skills/blob/main/Makefile)
同步；不要在本機編輯
[`skills/vendor/fullstack-nextjs/frontend-design/SKILL.md`](https://github.com/daviddwlee84/agent-skills/blob/main/skills/vendor/fullstack-nextjs/frontend-design/SKILL.md)
—— 變更會在下次同步被蓋掉。

## Upstream frontmatter description

> Create distinctive, production-grade frontend interfaces with high design
> quality. Use this skill when the user asks to build web components, pages,
> artifacts, posters, or applications (examples include websites, landing
> pages, dashboards, React components, HTML/CSS layouts, or when
> styling/beautifying any web UI). Generates creative, polished code and
> UI design that avoids generic AI aesthetics.

## 教什麼 (What it teaches)

美學方向 (aesthetic direction) skill —— 鼓勵帶有大膽、刻意觀點
（極簡 brutally minimal、極繁 maximalist、復古未來感 retro-futuristic、
編輯風 editorial、…）以及精緻的 typography 選擇，而非預設的 Inter/Arial。
含對抗 AI-slop 的護欄。把它當作
[`web-design-guidelines`](web-design-guidelines.md) 稽核 (audit) 角色的
創作 (creative) 對應。

## 相關 fullstack-nextjs skill

- [`shadcn`](shadcn.md) —— 表達所選美學的 component
- [`web-design-guidelines`](web-design-guidelines.md) —— 視覺定調後做 a11y/perf 稽核
- [`webapp-testing`](webapp-testing.md) —— Playwright 迴圈視覺驗證結果

## 也以 Claude Code plugin 形式發布 (Also published as a Claude Code plugin)

這個 skill 同時以
[`frontend-design`](https://github.com/anthropics/claude-plugins-official/tree/main/plugins/frontend-design)
plugin 形式被重新發布在
[`claude-plugins-official`](https://github.com/anthropics/claude-plugins-official)
marketplace —— 這就是為什麼 Claude Code 啟動 tip 有時候會推薦
`/plugin install frontend-design@claude-plugins-official`。**不要在已 vendor 的
版本之上再安裝一份** —— 兩邊主體完全一樣，差別只在 frontmatter 的
`description` 行，而我們 vendor 的 `anthropics/skills` 上游版本觸發詞
(trigger phrasing) 更豐富（除了 components/pages/applications 之外，還涵蓋
artifacts、posters、landing pages、dashboards、HTML/CSS layouts）。

## Canonical SKILL.md

完整指示見
[skills/vendor/fullstack-nextjs/frontend-design/SKILL.md](https://github.com/daviddwlee84/agent-skills/blob/main/skills/vendor/fullstack-nextjs/frontend-design/SKILL.md)。
Upstream 來源：
[anthropics/skills](https://github.com/anthropics/skills)。
