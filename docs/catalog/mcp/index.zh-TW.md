# MCP wiki —— MCP 知識庫

!!! note "Terminology rule (zh-TW pages)"
    技術名詞首次出現以「中文 (English original)」格式呈現，例：依賴注入
    (dependency injection)。**不自創翻譯**——若無公認譯名直接保留英文
    （如 `embedding`、`tokenizer`）。代碼、API 名、CLI flag、套件名、檔名一律不翻。

針對 [Model Context Protocol](https://modelcontextprotocol.io/) server
的個人知識區，記錄已評估、使用中、或想追蹤的 MCP。仿照
[Karpathy 的 LLM Wiki 樣式 (pattern)](../../reference/llm-wiki-pattern.md)
—— 每筆條目是策展 (curated) 後的紀錄，不是 vendor 安裝目標。

## 條目 (entries)

| 名稱 | 領域 | Status | Auth | Hosting |
|---|---|---|---|---|
| [Financial Datasets MCP](financialdatasets-ai.md) | [Finance](../domains/finance.md) / [Quant Research](../domains/quant-research.md) | `wishlist` | OAuth 2.1 + API key | Hosted (`mcp.financialdatasets.ai`) |

## 為何採 wiki，不採 registry？

Registry 需要對每個 MCP 有意見、需要策展 (curation) 團隊。Wiki 只是
維護者想保留的筆記。價值在於**記錄決策**（用、跳過、延後、為什麼），
讓未來的自己不必重新研究同個 MCP。

本 wiki 刻意對齊
[LLM Wiki pattern](../../reference/llm-wiki-pattern.md) —— 目前頁面是
手寫（量小），frontmatter 讓未來的自動化能夠 parse 並重建索引表。

## 單筆條目慣例 { #per-entry-conventions }

每筆 MCP 條目是 `docs/catalog/mcp/<slug>.md` 一個 markdown 檔，
必填的 YAML frontmatter：

```yaml
---
name: <human-readable name>
slug: <kebab-case slug, matches filename>
upstream_url: <docs URL>
transport: HTTP | stdio | SSE | mixed
auth: <one-line description>
hosting: Hosted (<host>) | Local | Self-hosted
domain: <one of the domain hub slugs>
status: vendored | deferred | skipped | evaluated | wishlist
license: <SPDX or "Proprietary">
last_verified: <YYYY-MM-DD>
---
```

頁面主體採一致結構：

1. **TL;DR**（兩句話）
2. **Tools / capabilities**（表格，~6-12 列）
3. **Auth & install**（每個 host 一段：Claude Code、Claude Desktop、Cursor、Managed Agents）
4. **When to use it / When NOT to use it**（成對 bullet）
5. **Related skills in this repo**（交叉連結到 `docs/skills/*` 或 domain hub）
6. **Upstream sources**（1-3 個連結 —— docs / GitHub / blog post）

`status` 欄位使用與
[external skill 條目](../skill-collections.md)同一個 enum —— 完整 enum
表格在每個 catalog 頁首的 snippet 內。

## 另見

- [LLM Wiki pattern](../../reference/llm-wiki-pattern.md) —— 本 wiki
  仿照的 Karpathy 樣式 (pattern)。
- [Domains](../domains/index.md) —— 每個 domain hub 列出相關 MCP。
- 上游 MCP 目錄：
  [modelcontextprotocol.io/servers](https://github.com/modelcontextprotocol/servers)。
