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
| [`vectorbt`](../../skills/vectorbt.md) | OSS／PRO library 開發、按版本同步的 XDG 文件、遷移驗證與可選 MCP。 | `quantitative-finance` group |
| [`nautilus-trader`](../../skills/nautilus-trader.md) | 辨識 v1 Cython／v2 Rust-PyO3 世代、git tag 文件快取、事件驅動回測 (event-driven backtesting)、sandbox／實盤安全關卡。 | `quantitative-finance` group |

### Vendored

| Skill | Upstream | Series |
|---|---|---|
| _暫無_ | | |

## External skills（手動安裝）

--8<-- "_snippets/external-install.md"

| Skill / Plugin | Upstream | Status | 為何此狀態 | 安裝提示 |
|---|---|---|---|---|
| VectorBT Backtesting Skills | [marketcalls/vectorbt-backtesting-skills](https://github.com/marketcalls/vectorbt-backtesting-skills) | `skipped` | 已評估 OSS 工作流程；OpenAlgo 指標預設不符合本技能的 library 使用定位。 | Upstream instructions |
| NautilusTrader docs skill | [aysuio/nt-skill](https://github.com/aysuio/nt-skill) | `skipped` | 沒有授權條款；假設官網 `latest` 文件對應已安裝版本，在 v1 → v2 RC 期間並不成立。 | Upstream instructions |
| NautilusTrader skill | [clay584/nautilus-trader-skill](https://github.com/clay584/nautilus-trader-skill) | `skipped` | 沒有授權條款；只驗證到 1.228.0，教的是 v1 `TradingNode` API。 | Upstream instructions |

## MCP servers

| 名稱 | Upstream | Status | Auth | 紀錄 |
|---|---|---|---|---|
| Financial Datasets MCP | [`docs.financialdatasets.ai/mcp-server`](https://docs.financialdatasets.ai/mcp-server) | `wishlist` | OAuth 2.1 + API key | [單一 MCP 頁面](../mcp/financialdatasets-ai.md) |

## Backlog（TODO `P?` 條目）

見 [`TODO.md` 的 `P?` 區](https://github.com/daviddwlee84/agent-skills/blob/main/TODO.md)：

- `[?/L]` **Tardis SDK skill** —— 歷史市場資料 workflow、access
  假設、範例驅動 (example-driven) 指引。
- `[?/L]` **Financial data sources skill set** —— provider 比較
  （與 [Finance](finance.md) 共用條目）。

## 另見

- [Finance](finance.md) —— 銀行、資本市場、股票研究 workflow。
- [AI/ML Research](ai-ml-research.md) —— 量化專案常會疊上去的
  experiment tracking + notebook 生態（`mlflow-tracking`、
  `marimo-batch-mlflow`）。
- [`docs/skills/quantatitive-factor-researcher.md`](../../skills/quantatitive-factor-researcher.md)、
  [`vectorbt.md`](../../skills/vectorbt.md)、[`nautilus-trader.md`](../../skills/nautilus-trader.md)
  —— local skill 頁面。
