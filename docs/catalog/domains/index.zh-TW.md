# Domains —— 領域

!!! note "Terminology rule (zh-TW pages)"
    技術名詞首次出現以「中文 (English original)」格式呈現，例：依賴注入
    (dependency injection)。**不自創翻譯**——若無公認譯名直接保留英文
    （如 `embedding`、`tokenizer`）。代碼、API 名、CLI flag、套件名、檔名一律不翻。

每個專業領域 (professional domain) 的 hub 頁面。每個 hub 是單一頁面的
入口，整合該領域相關的 local skill、vendored skill、外部
（手動安裝）skill、MCP server、backlog item。

## Hubs

| Hub | 涵蓋範圍 | 狀態 |
|---|---|---|
| [Finance](finance.md) | 銀行 (banking)、資本市場 (capital markets)、股票研究 (equity research)、財富管理 (wealth management)、基金管理 (fund admin)。 | 已填入 |
| [Quant Research](quant-research.md) | 量化交易 (quant trading)、因子研究 (factor research)、回測 (backtesting)、實盤執行 (live execution)。 | 已填入 |
| [AI/ML Research](ai-ml-research.md) | 實驗追蹤 (experiment tracking)、模型生命週期 (model lifecycle)、fine-tuning、agent framework。 | 已填入 |
| [Web & Fullstack](web-fullstack.md) | Next.js / React / Tailwind / Supabase / Vercel / browser automation / web quality 稽核 (audits)。 | 已填入 |
| [Knowledge Work](knowledge-work.md) | 銷售 (sales) / 法務 (legal) / 客服 (customer support) / 產品 (product) / 行銷 (marketing) / 資料 (data) 等。 | 多數為 template |
| [Agent Harness](agent-harness.md) | SDD framework + agent harness（skill 之上的層級）。 | 僅 template |

「多數為 template」/「僅 template」hub 直白地呈現「目前大部分為空」——
這種結構先佔位，等之後內容到位即可。

## 如何新增一個 domain hub { #how-to-add-a-new-domain-hub }

1. 把 [`docs/_snippets/domain-hub-template.md`](https://github.com/daviddwlee84/agent-skills/blob/main/docs/_snippets/domain-hub-template.md) 複製到 `docs/catalog/domains/<slug>.md`。
2. 填入電梯簡介 (elevator pitch) 與四張表格（Local / Vendored / External / MCP）—— 沒有的列就保留 `_none yet_`。
3. 把新頁面加到 `mkdocs.yml` 的 nav 之 `Catalog → Domains` 下方。
4. 翻譯成 `docs/catalog/domains/<slug>.zh-TW.md`（每個 catalog 頁面都
   是雙語）。
5. 從相關 hub 的 `See also` 段落、以及任何相關的 reference landscape
   頁面交叉連結 (cross-link) 過來。
6. 跑 `make docs-build`（strict mode 會抓出缺失的翻譯與壞掉的 link）。

關於替既有 hub 新增單筆條目（skill、MCP、status 變更）的 workflow，
見 [Adding catalog entries](../../workflows/adding-catalog-entries.md)。
