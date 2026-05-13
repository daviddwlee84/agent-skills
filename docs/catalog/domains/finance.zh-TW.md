# Finance —— 金融

!!! note "Terminology rule (zh-TW pages)"
    技術名詞首次出現以「中文 (English original)」格式呈現，例：依賴注入
    (dependency injection)。**不自創翻譯**——若無公認譯名直接保留英文
    （如 `embedding`、`tokenizer`）。代碼、API 名、CLI flag、套件名、檔名一律不翻。

銀行 (banking)、資本市場 (capital markets)、股票研究 (equity research)、
財富管理 (wealth management)、基金管理 (fund admin)、會計 (accounting)
相關的 workflow。交易策略 (trading strategy) / 因子研究 (factor research) /
回測 (backtesting) 請改看 [Quant Research](quant-research.md) hub。

## 此 repo 內的 skill

### Local

| Skill | 一句話 | 備註 |
|---|---|---|
| _暫無直接相關_ | | [`quantatitive-factor-researcher`](../../skills/quantatitive-factor-researcher.md) 最接近，但偏量化口味 —— 詳見 [Quant Research](quant-research.md) hub。 |

### Vendored

| Skill | Upstream | Series |
|---|---|---|
| _暫無_ | | |

## External skills（手動安裝）

--8<-- "_snippets/external-install.md"

| Skill / Plugin | Upstream | Status | 為何此狀態 | 安裝提示 |
|---|---|---|---|---|
| `claude-for-financial-services`（完整 marketplace） | [`anthropics/financial-services`](https://github.com/anthropics/financial-services) | `wishlist` | 規模龐大的 marketplace（11 個命名 agent + 7 個 vertical plugin + 合作夥伴 plugin）。要逐 plugin 評估 —— 多數假設部署在 Cowork / Managed Agents，並非單機 Claude Code。 | `claude plugin marketplace add anthropics/financial-services` 後挑選 plugin（例如 `financial-analysis`、`equity-research`、`investment-banking`）。 |
| `financial-analysis` plugin（子集） | [`anthropics/financial-services/plugins/vertical-plugins/financial-analysis`](https://github.com/anthropics/financial-services/tree/main/plugins/vertical-plugins/financial-analysis) | `wishlist` | 核心 skill（DCF、LBO、comps、3-statement）+ 11 個 MCP connector。若決定挑子集 vendor，這是最高價值的入口。 | `claude plugin install financial-analysis@claude-for-financial-services` |
| `Awesome-finance-skills` 收錄 | [`RKiding/Awesome-finance-skills`](https://github.com/RKiding/Awesome-finance-skills) | `wishlist` | 八個 skill 組合（news、stock data、sentiment、forecasting、signal tracking、viz、reporting、web search）。即插即用 (plug-and-play)。獨立作者 —— 需確認 license 與維護狀態。 | 檢視 upstream `SKILL.md` 結構後 `npx skills@latest add RKiding/Awesome-finance-skills`。 |
| 六個 skill（Claude for Financial Services） | [Claude tutorial](https://claude.com/resources/tutorials/claude-for-financial-services-skills) | `evaluated` | 在 Settings → Capabilities → Skills 中啟用（無手動安裝）。教學文件而已 —— 僅限 Claude for Financial Services 帳號。文件描述六個官方 skill：Comps Analysis、DCF、Initiating Coverage Research、Strip Profile、Due Diligence Data Pack、Earnings Analysis。 | 無法用 `npx skills` 安裝；FSI 帳號的官方 Claude UI 內可見。 |

## MCP servers

| 名稱 | Upstream | Status | Auth | 紀錄 |
|---|---|---|---|---|
| Financial Datasets MCP | [`docs.financialdatasets.ai/mcp-server`](https://docs.financialdatasets.ai/mcp-server) | `wishlist` | OAuth 2.1 + API key | [單一 MCP 頁面](../mcp/financialdatasets-ai.md) |
| LSEG、S&P Global、FactSet 等 | 隨 `anthropics/financial-services/financial-analysis/.mcp.json` 一起 | `wishlist` | 各家 provider 不同 | _暫無單一 MCP 紀錄 —— 評估後再加_ |

## Backlog（TODO `P?` 條目）

見 [`TODO.md` 的 `P?` 區](https://github.com/daviddwlee84/agent-skills/blob/main/TODO.md)：

- `[?/L]` **Financial data sources skill set** —— 比較免費 vs 付費市場資料 (market data) 提供者、區域涵蓋、依 provider 還是依 workflow 組織 skill。 → [`backlog/financial-data-sources.md`](https://github.com/daviddwlee84/agent-skills/blob/main/backlog/financial-data-sources.md)

## 另見

- [Quant Research](quant-research.md) —— 交易策略、回測、因子研究。
- [MCP wiki: Financial Datasets](../mcp/financialdatasets-ai.md) ——
  wiki 中第一個有完整內容的 MCP 紀錄。
- [`docs/reference/llm-wiki-pattern.md`](../../reference/llm-wiki-pattern.md)
  —— Karpathy 的個人知識庫 (personal knowledge base) 樣式（在策展
  provider-specific 筆記時相當相關）。
