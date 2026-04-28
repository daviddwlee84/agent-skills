# webapp-testing (vendored)

!!! note "Terminology rule (zh-TW pages)"
    技術名詞首次出現以「中文 (English original)」格式呈現，例：依賴注入
    (dependency injection)。**不自創翻譯**——若無公認譯名直接保留英文
    （如 `embedding`、`tokenizer`）。代碼、API 名、CLI flag、套件名、檔名一律不翻。

從
[anthropics/skills/skills/webapp-testing](https://github.com/anthropics/skills/tree/main/skills/webapp-testing)
vendor 過來（屬於 [`fullstack-nextjs`](index.md#fullstack-nextjs-series) series）。
透過 [`make sync`](https://github.com/daviddwlee84/agent-skills/blob/main/Makefile)
同步；不要在本機編輯
[`skills/vendor/fullstack-nextjs/webapp-testing/SKILL.md`](https://github.com/daviddwlee84/agent-skills/blob/main/skills/vendor/fullstack-nextjs/webapp-testing/SKILL.md)
—— 變更會在下次同步被蓋掉。

## Upstream frontmatter description

> Toolkit for interacting with and testing local web applications using
> Playwright. Supports verifying frontend functionality, debugging UI
> behavior, capturing browser screenshots, and viewing browser logs.

## 教什麼 (What it teaches)

原生 Python Playwright 工作流程，附帶一個 `scripts/with_server.py`
helper 管理 server lifecycle (支援多個 server)。決策樹：靜態 HTML →
直接讀 selector；動態 webapp → 用 helper + 寫一個簡化的 Playwright
script。Black-box script 第一步先用 `--help` 跑，避免 context window
被吃掉。

## 相關 fullstack-nextjs skill

- [`nextjs`](nextjs.md) —— webapp-testing 驅動的 dev server
- [`frontend-design`](frontend-design.md) —— 閉環：build → screenshot → critique

## Canonical SKILL.md

完整指示見
[skills/vendor/fullstack-nextjs/webapp-testing/SKILL.md](https://github.com/daviddwlee84/agent-skills/blob/main/skills/vendor/fullstack-nextjs/webapp-testing/SKILL.md)。
Upstream 來源：
[anthropics/skills](https://github.com/anthropics/skills)。
