# Warp Oz skills

!!! note "Terminology rule (zh-TW pages)"
    技術名詞首次出現以「中文 (English original)」格式呈現。**不自創翻譯**——
    若無公認譯名直接保留英文（如 `MCP`、`SKILL.md`、`gh`、`AGPL`）。
    代碼、API 名、CLI flag、套件名、檔名一律不翻。

[Warp](https://github.com/warpdotdev/warp)（57k⭐）是一個從 terminal 演化成
「agentic development environment（agent 開發環境）」的產品。2026 年 5 月 Warp
把主程式碼以 **AGPL-3.0** 授權開源。除了主 repo，團隊也維護
[`warpdotdev/oz-skills`](https://github.com/warpdotdev/oz-skills)（764⭐）——
給他們 **Oz** 雲端 agent 平台用的 skill 集合。

## 為什麼 oz-skills 可以 vendor 進來

oz-skills 是 **MIT 授權**，且遵守
[agentskills.io specification](https://agentskills.io/specification)，所以
這些 skill 可以在任何相容的 agent 使用：Claude Code、Codex、OpenCode、Cursor、
Gemini CLI。Warp agent 只是其中一個 host——skill 本身是可攜帶的 markdown。

Warp 主 repo 是 AGPL-3.0（viral copyleft）；那個 license **不**傳染到
oz-skills（它是另外 MIT 授權的）。把 oz-skills vendor 進這個 repo 完全安全。

## 我們 vendor 的 6 個（共 15 個）

我們挑的是能填補現有 skill 空缺的。跳過的：`mcp-builder`（與
`anthropics/mcp-builder` 重複）、`webapp-testing`（與 `fullstack-nextjs` series
的 `anthropics/webapp-testing` 重複）、`scheduler`（太窄——只做本地提醒）、
`slack-qa-investigate`（Slack 依賴）、`dbt-model-index` / `analysis-artifacts`
（針對 Warp 內部 BigQuery 設計）、`terraform-style-check`（太窄）、
`seo-aeo-audit`（太主觀）、`docs-update`（與 `doc-coauthoring` 跟 CLAUDE.md 的
doc-update pattern 重疊）。

### `github-workflow` plugin — 4 個 skill

| Skill | 描述 |
|---|---|
| `ci-fix` | 診斷 GitHub Actions 失敗：用 `gh` 查 log、找 root cause、做最小修正、push 到專屬 fix branch。前提：`gh auth status` 通過。 |
| `create-pull-request` | 依照專案慣例建立結構化 PR——commit 分析、branch 管理、用 `gh pr create` 寫 PR body。 |
| `github-bug-report-triage` | 評估 GitHub bug issue 是否有足夠資訊。找專案的 bug-report template、檢查必填欄位、為不完整的 issue 草擬建設性回覆。 |
| `github-issue-dedupe` | 用多策略語義 + 關鍵字搜尋偵測重複 issue。可手動執行或接入 GitHub Actions workflow。 |

這四個跟 `engineering-fundamentals/triage`（mattpocock）互補——那個比較通用，
Oz 的這些更聚焦在 GitHub 工作流程並使用 `gh` CLI 自動化。

### `web-quality` plugin — 2 個 skill

| Skill | 描述 |
|---|---|
| `web-accessibility-audit` | WCAG 2.0/2.1/2.2 合規稽核——依 POUR 原則分類找 violation，並提供修正步驟。不需要 MCP 依賴。 |
| `web-performance-audit` | Core Web Vitals + Lighthouse 稽核，使用 `chrome-devtools` MCP。需要在 `.mcp.json` 設定 `chrome-devtools-mcp@latest`。沒設定的話 skill 會告訴你怎麼加。 |

`web-accessibility-audit` 不需要 MCP，到處都能用。`web-performance-audit` 需要
Chrome DevTools MCP——沒有設定時 skill 會 gracefully 告知，不會靜默失敗。

## 安裝

```bash
# 透過這個 repo 安裝全部 6 個
npx skills@latest add daviddwlee84/agent-skills

# 或直接從 upstream
npx skills@latest add warpdotdev/oz-skills/.agents/skills/ci-fix
npx skills@latest add warpdotdev/oz-skills/.agents/skills/web-accessibility-audit
# ...
```

## Warp AGPL-3.0 注意事項

Warp terminal 本身是 AGPL-3.0。如果你把 Warp 嵌入一個 ship 給使用者的產品，
AGPL 要求你開源你的修改。把 Warp 當本地開發工具使用不觸發 AGPL。把 oz-skills
（MIT）單獨使用跟 Warp 完全無關，沒有 AGPL 問題。

## 延伸閱讀

- [Browser automation skills](browser-automation-skills.zh-TW.md) — 用真實瀏覽器
  測試 web app；跟上面的 web-quality skill 互補
- [`fullstack-nextjs/webapp-testing`](../skills/webapp-testing.zh-TW.md) — 已
  vendor 的 Anthropic Playwright 測試 skill
- [Agent skill compatibility](agent-skill-compatibility.zh-TW.md) — 所有這些
  skill 都遵守的 portable `SKILL.md` 規範
