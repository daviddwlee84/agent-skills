# Quant Research —— 量化研究

!!! note "Terminology rule (zh-TW pages)"
    技術名詞首次出現以「中文 (English original)」格式呈現，例：依賴注入
    (dependency injection)。**不自創翻譯**——若無公認譯名直接保留英文
    （如 `embedding`、`tokenizer`）。代碼、API 名、CLI flag、套件名、檔名一律不翻。

量化交易 (quant trading)、因子研究 (factor research)、回測 (backtesting)、
實盤執行 (live execution) 的 workflow。和 [Finance](finance.md) hub
（涵蓋銀行 / 資本市場 / 股票研究 / 基金管理）區分 —— 重疊的部分主要
在資料來源 (data source) 端。

## 此 repo 內的 skill

### Local

| Skill | 一句話 | 備註 |
|---|---|---|
| [`quantatitive-factor-researcher`](../../skills/quantatitive-factor-researcher.md) | Python 量化研究 persona，做 factor engineering、backtesting、cross-validation，附 Sharpe / IR / Tracking Error 指標 (metrics)。 | 此 hub 的核心 skill。 |

### Vendored

| Skill | Upstream | Series |
|---|---|---|
| _暫無_ | | |

## External skills（手動安裝）

--8<-- "_snippets/external-install.md"

| Skill / Plugin | Upstream | Status | 為何此狀態 | 安裝提示 |
|---|---|---|---|---|
| _尚未調查 —— 量化工具多為 Python library，目前還沒有 agent skill 包裝_ | | | | |

## MCP servers

| 名稱 | Upstream | Status | Auth | 紀錄 |
|---|---|---|---|---|
| Financial Datasets MCP | [`docs.financialdatasets.ai/mcp-server`](https://docs.financialdatasets.ai/mcp-server) | `wishlist` | OAuth 2.1 + API key | [單一 MCP 頁面](../mcp/financialdatasets-ai.md) |

## Backlog（TODO `P?` 條目）

見 [`TODO.md` 的 `P?` 區](https://github.com/daviddwlee84/agent-skills/blob/main/TODO.md)：

- `[?/M]` **VectorBT skill** —— 因子研究、回測、結果檢視的最小 workflow。
- `[?/L]` **VectorBT Pro skill** —— 評估付費版 skill 是否能可靠地把
  agent 指引到正確的 documentation 頁面與付費版的 workflow 細節。
- `[?/M]` **Nautilus Trader skill** —— 事件驅動 (event-driven) 交易
  workflow、回測、實盤交易護欄 (guardrails)。
- `[?/L]` **Tardis SDK skill** —— 歷史市場資料 workflow、access
  假設、範例驅動 (example-driven) 指引。
- `[?/L]` **Financial data sources skill set** —— provider 比較
  （與 [Finance](finance.md) 共用條目）。

## 另見

- [Finance](finance.md) —— 銀行、資本市場、股票研究 workflow。
- [AI/ML Research](ai-ml-research.md) —— 量化專案常會疊上去的
  experiment tracking + notebook 生態（`mlflow-tracking`、
  `marimo-batch-mlflow`）。
- [`docs/skills/quantatitive-factor-researcher.md`](../../skills/quantatitive-factor-researcher.md)
  —— 該 local skill 頁面。
