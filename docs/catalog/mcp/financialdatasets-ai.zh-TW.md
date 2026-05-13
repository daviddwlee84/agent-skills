---
name: Financial Datasets MCP
slug: financialdatasets-ai
upstream_url: https://docs.financialdatasets.ai/mcp-server
transport: HTTP
auth: OAuth 2.1 + API key
hosting: Hosted (mcp.financialdatasets.ai)
domain: finance
status: wishlist
license: Proprietary
last_verified: 2026-05-13
---

# Financial Datasets MCP

!!! note "Terminology rule (zh-TW pages)"
    技術名詞首次出現以「中文 (English original)」格式呈現，例：依賴注入
    (dependency injection)。**不自創翻譯**——若無公認譯名直接保留英文
    （如 `embedding`、`tokenizer`）。代碼、API 名、CLI flag、套件名、檔名一律不翻。

## TL;DR

託管 (hosted) 的 MCP server，提供即時 + 歷史 (historical) 股票資料：
pricing、財報 (financial statements)、SEC filing、新聞、insider trade、
篩選 (screening)。20+ 個 tool，可由 Claude Code / Claude Desktop /
Cursor / Managed Agents 透過 OAuth 2.1（互動）或 API key（程式
存取）使用。

## Tools / capabilities

| 類別 | 範例 |
|---|---|
| Pricing | 即時 + 歷史股價 |
| 財報 | Income、balance sheet、cash flow、segmented financial |
| Metrics | P/E、market cap、enterprise value、dividend yield |
| 公司資訊 | sector、industry、員工數 |
| SEC filing | 10-K、10-Q、8-K + 可抽取段落（如 Risk Factors） |
| 市場情報 | 新聞、insider trade、earnings 資料 |
| 篩選 (screening) | 用估值 + 財務條件過濾股票 |
| 特殊 | KPI 指引、non-GAAP metrics、央行利率 |

## Auth & install

### Claude Code

```bash
claude mcp add --transport http financial-datasets https://mcp.financialdatasets.ai/
```

OAuth 流程在首次使用時於瀏覽器執行。

### Claude Desktop

Settings → Connectors → Add custom connector → 貼入
`https://mcp.financialdatasets.ai/`。OAuth 流程在 app 內執行。

### Cursor

編輯 `~/.cursor/mcp.json`：

```json
{
  "mcpServers": {
    "financial-datasets": {
      "url": "https://mcp.financialdatasets.ai/",
      "transport": "http"
    }
  }
}
```

### Managed Agents（程式存取）

對 `/api` endpoint 用 static bearer vault 憑證 (`X-API-KEY` header)。
API key 取得流程見
[upstream auth docs](https://docs.financialdatasets.ai/mcp-server)。

## When to use it（適用情境）

- 研究 / 撰稿 workflow 中快速查股票。
- SEC filing 主張對照實際 filing。
- 用估值條件做股票篩選。
- 拉時間序列做臨時圖表。

## When NOT to use it（不適用情境）

- 重時序 (time-series) 工作 —— 改用 REST API 抓原始資料 + 本地
  快取。MCP 是 per-call。
- 非股票資產類別（futures、FX、crypto）。覆蓋以股票為主。
- 回測 (backtesting)（延遲 + per-call 成本）。改用
  [Tardis](https://tardis.dev/) / vendor SDK + 本地快取。
- 需要決定性 (deterministic) snapshot 的場景（MCP 是即時資料）。

## 此 repo 內相關 skill

- [`quantatitive-factor-researcher`](../../skills/quantatitive-factor-researcher.md)
  —— 可消費此 MCP 取得 factor data 的 local skill。
- [Finance](../domains/finance.md) —— domain hub。
- [Quant Research](../domains/quant-research.md) —— domain hub。

## Upstream sources

- [Financial Datasets MCP docs](https://docs.financialdatasets.ai/mcp-server)
  —— 安裝 + tool 參照。
- [Financial Datasets API docs](https://docs.financialdatasets.ai/) ——
  MCP 包裝的底層 REST API。
