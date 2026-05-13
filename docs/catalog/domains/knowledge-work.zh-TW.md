# Knowledge Work —— 知識工作

!!! note "Terminology rule (zh-TW pages)"
    技術名詞首次出現以「中文 (English original)」格式呈現，例：依賴注入
    (dependency injection)。**不自創翻譯**——若無公認譯名直接保留英文
    （如 `embedding`、`tokenizer`）。代碼、API 名、CLI flag、套件名、檔名一律不翻。

依工作職能 (job-function) 切分的 plugin —— 銷售 (sales) / 法務
(legal) / 客服 (customer support) / 產品 (product management) / 行銷
(marketing) / 資料 (data) 等。主要由 Anthropic 的
[Knowledge Work Plugins](https://github.com/anthropics/knowledge-work-plugins)
專案推動。本 hub 目前主要當作 registry —— 我們不在此領域 ship local
skill，但會追蹤外部 (external) 的方案以備未來使用。

## 此 repo 內的 skill

### Local

| Skill | 一句話 | 備註 |
|---|---|---|
| _暫無_ | | 本 repo 聚焦在 engineering / ML / docs 工具。Knowledge-work plugin 偏 job-function 取向，與維護者的日常重疊較少。 |

### Vendored

| Skill | Upstream | Series |
|---|---|---|
| _暫無_ | | |

## External skills（手動安裝）

--8<-- "_snippets/external-install.md"

完整的 Anthropic Knowledge Work Plugins marketplace（11 個 plugin，
MIT license）。每個都是 Cowork / Claude Code plugin，組合該職能對應
的 skill + slash command + MCP connector。

| Plugin | Upstream | Status | 為何此狀態 | 安裝提示 |
|---|---|---|---|---|
| `productivity` | [knowledge-work-plugins/productivity](https://github.com/anthropics/knowledge-work-plugins/tree/main/productivity) | `wishlist` | 通用任務 / 行事曆 / workflow plugin。Slack + Notion + Asana + Linear + Jira + Monday + ClickUp + Microsoft 365 connector。 | `claude plugin install productivity@knowledge-work-plugins` |
| `sales` | [`.../sales`](https://github.com/anthropics/knowledge-work-plugins/tree/main/sales) | `wishlist` | 潛在客戶研究 (prospect research)、call prep、pipeline review。 | `claude plugin install sales@knowledge-work-plugins` |
| `customer-support` | [`.../customer-support`](https://github.com/anthropics/knowledge-work-plugins/tree/main/customer-support) | `wishlist` | Ticket triage、escalation、KB 文章。 | `claude plugin install customer-support@knowledge-work-plugins` |
| `product-management` | [`.../product-management`](https://github.com/anthropics/knowledge-work-plugins/tree/main/product-management) | `wishlist` | Spec、roadmap、user research、競品 (competitive) 追蹤。 | `claude plugin install product-management@knowledge-work-plugins` |
| `marketing` | [`.../marketing`](https://github.com/anthropics/knowledge-work-plugins/tree/main/marketing) | `wishlist` | 內容、campaign、品牌口吻 (brand voice)、performance report。 | `claude plugin install marketing@knowledge-work-plugins` |
| `legal` | [`.../legal`](https://github.com/anthropics/knowledge-work-plugins/tree/main/legal) | `wishlist` | 合約審閱、NDA、合規 (compliance)、風險評估。 | `claude plugin install legal@knowledge-work-plugins` |
| `finance` | [`.../finance`](https://github.com/anthropics/knowledge-work-plugins/tree/main/finance) | `wishlist` | 日記帳 (journal entries)、reconciliation、財務報表 (financial statements)、稽核 (audits)。在 [Finance](finance.md) hub 也有交叉引用。 | `claude plugin install finance@knowledge-work-plugins` |
| `data` | [`.../data`](https://github.com/anthropics/knowledge-work-plugins/tree/main/data) | `wishlist` | SQL query、視覺化 (visualization)、統計分析 (statistical analysis)、dashboard。Snowflake + Databricks + BigQuery connector。 | `claude plugin install data@knowledge-work-plugins` |
| `enterprise-search` | [`.../enterprise-search`](https://github.com/anthropics/knowledge-work-plugins/tree/main/enterprise-search) | `wishlist` | 跨工具搜尋 (cross-tool search)：email / chat / docs / wiki。 | `claude plugin install enterprise-search@knowledge-work-plugins` |
| `bio-research` | [`.../bio-research`](https://github.com/anthropics/knowledge-work-plugins/tree/main/bio-research) | `wishlist` | 在 [AI/ML Research](ai-ml-research.md) hub 也有交叉引用。 | `claude plugin install bio-research@knowledge-work-plugins` |
| `cowork-plugin-management` | [`.../cowork-plugin-management`](https://github.com/anthropics/knowledge-work-plugins/tree/main/cowork-plugin-management) | `wishlist` | Meta plugin —— 企業要建立自家 plugin 用。 | `claude plugin install cowork-plugin-management@knowledge-work-plugins` |

Marketplace bootstrap（一次性，之後可裝上述任一 plugin）：

```bash
claude plugin marketplace add anthropics/knowledge-work-plugins
```

## MCP servers

| 名稱 | Upstream | Status | Auth | 紀錄 |
|---|---|---|---|---|
| _尚未調查_ —— knowledge-work plugin 多在 `.mcp.json` 內直接綁 MCP connector | | | | |

## Backlog（TODO `P?` 條目）

- _暫無 —— 想評估特定 plugin 的話請開 TODO `P?`。_

## 另見

- [Finance](finance.md) —— 與 `finance`、`data` plugin 重疊。
- [AI/ML Research](ai-ml-research.md) —— `bio-research` 交叉列在那。
- Upstream README：[`anthropics/knowledge-work-plugins`](https://github.com/anthropics/knowledge-work-plugins)
  —— 完整 plugin 矩陣 + connector 清單。
