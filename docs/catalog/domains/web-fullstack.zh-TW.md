# Web & Fullstack —— Web 與全端

!!! note "Terminology rule (zh-TW pages)"
    技術名詞首次出現以「中文 (English original)」格式呈現，例：依賴注入
    (dependency injection)。**不自創翻譯**——若無公認譯名直接保留英文
    （如 `embedding`、`tokenizer`）。代碼、API 名、CLI flag、套件名、檔名一律不翻。

Web app 開發 —— Next.js / React / Tailwind / shadcn / Supabase /
Vercel / Postgres / browser automation / GitHub workflow / web 品質
稽核 (audits)。本 repo 內容最完整的領域，由
[`fullstack-nextjs`](../../skills/index.md) series 撐起。

## 此 repo 內的 skill

### Local

| Skill | 一句話 | 備註 |
|---|---|---|
| _暫無直接相關_ | | local skill 主要偏 ML / docs / process 工具，少有 web framework 取向。 |

### Vendored

`fullstack-nextjs` series（9 個 skill，全來自官方 organization）：

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

GitHub workflow + web quality（Warp Oz，見
[`docs/reference/warp-oz-skills.md`](../../reference/warp-oz-skills.md)）：

| Skill | Upstream | 備註 |
|---|---|---|
| `ci-fix`、`create-pull-request`、`github-bug-report-triage`、`github-issue-dedupe` | [`warpdotdev/oz-skills`](https://github.com/warpdotdev/oz-skills) | 全部歸在 `github-workflow` plugin 分組。 |
| `web-accessibility-audit`、`web-performance-audit` | [`warpdotdev/oz-skills`](https://github.com/warpdotdev/oz-skills) | `web-performance-audit` 需要 Chrome DevTools MCP。 |

## External skills（手動安裝）

--8<-- "_snippets/external-install.md"

| Skill / Plugin | Upstream | Status | 為何此狀態 | 安裝提示 |
|---|---|---|---|---|
| `vercel/vercel-plugin` 的其他 skill | [`vercel/vercel-plugin`](https://github.com/vercel/vercel-plugin) | `evaluated` | 已從中 vendor 4 個進 `fullstack-nextjs`。其餘（如 `tailwind`、`vercel-ai-sdk` 等）有需要時再加。 | `npx skills@latest add vercel/vercel-plugin -s <skill>` |
| `vercel-labs/agent-skills` 的剩餘 skill | [`vercel-labs/agent-skills`](https://github.com/vercel-labs/agent-skills) | `evaluated` | 已 vendor `web-design-guidelines`。其餘是類似的 audit 風格 skill。 | `npx skills@latest add vercel-labs/agent-skills -s <skill>` |
| `warpdotdev/oz-skills` 跳過的 9 個 | [`warpdotdev/oz-skills`](https://github.com/warpdotdev/oz-skills) | `skipped` | 跳過理由見 [`docs/reference/warp-oz-skills.md`](../../reference/warp-oz-skills.md)：`mcp-builder`（重複）、`webapp-testing`（重複）、`scheduler`（太窄）、依賴 Slack / BigQuery 的條目等。 | （未 vendor） |

## MCP servers

| 名稱 | Upstream | Status | Auth | 紀錄 |
|---|---|---|---|---|
| `chrome-devtools` | [`@modelcontextprotocol/server-chrome-devtools`](https://www.npmjs.com/package/chrome-devtools-mcp) | `evaluated` | 本機 stdio | _暫無單一 MCP 紀錄 —— `web-performance-audit` 需要它_ |

## Backlog（TODO `P?` 條目）

見 [`TODO.md` 的 `P?` 區](https://github.com/daviddwlee84/agent-skills/blob/main/TODO.md)：

- `[?/M]` **Playwright skill** —— web automation、testing、網站
  clone 的 workflow，agent 維護起來要實際可行。
- `[?/L]` **Sibling docs-stack skills (docusaurus / vitepress / hugo /
  sphinx)** —— 與既有 `mkdocs-site-bootstrap` 對應。

## 另見

- [`docs/reference/browser-automation-skills.md`](../../reference/browser-automation-skills.md)
  —— Playwright vs agent-browser vs browser-use vs stagehand vs
  Playwright MCP 比較。
- [`docs/reference/warp-oz-skills.md`](../../reference/warp-oz-skills.md)
  —— Warp Oz GitHub-workflow + web-quality skill。
- [`docs/skills/index.md`](../../skills/index.md#fullstack-nextjs-series)
  —— 完整 Skills 總覽，含 `fullstack-nextjs` series 表格。
