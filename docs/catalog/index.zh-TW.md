# Catalog —— 收錄目錄

!!! note "Terminology rule (zh-TW pages)"
    技術名詞首次出現以「中文 (English original)」格式呈現，例：依賴注入
    (dependency injection)。**不自創翻譯**——若無公認譯名直接保留英文
    （如 `embedding`、`tokenizer`）。代碼、API 名、CLI flag、套件名、檔名一律不翻。

策展 (curated) 後的**外部 skill、MCP server、領域 (domain) 中樞 (hub)**
索引 —— 與 [Skills](../skills/index.md)（這裡實際 ship 的東西）以及
[Reference](../reference/scripts.md)（描述*我們自己的*工具如何運作）區分開。

Catalog 存在的理由：

- 有些 skill 值得知道但不值得 vendor（license、scope、niche、僅以
  plugin 形式提供）—— 仍希望從 docs 內找得到。
- MCP server 不太能套進 skill 的模型 —— 需要獨立的記錄區。
- 領域 (domain) 從業者（金融、ML、量化研究 …）會想要一個
  入口頁面，把該領域相關的 local + vendored + external skill +
  MCP + backlog item 一次列出。

## 內容

| 子區塊 | 用途 | 從哪裡開始 |
|---|---|---|
| [Domains](domains/index.md) | 每個專業領域 (professional domain) 一頁 hub —— 從該領域視角整合 skill + MCP + backlog。 | [Finance](domains/finance.md) 是內容最完整的範例。 |
| [External skills](skill-collections.md) | 收整 upstream skill collection 與相關閱讀的單一索引。取代過去的 `Collections.md` 與 README「Resources」段落。 | 頁首的完整表格。 |
| [MCP wiki](mcp/index.md) | MCP server 的個人知識區 —— 一個 MCP 一頁，附 frontmatter 供未來自動化使用。 | [Financial Datasets MCP](mcp/financialdatasets-ai.md) 是第一筆完整條目。 |

## Catalog 的 status 機制

每筆外部條目帶一個 `status:`（`vendored / deferred / skipped /
evaluated / wishlist`），同時也是 vendoring 決策的紀錄。完整 enum 定義
在 [`docs/_snippets/external-install.md`](https://github.com/daviddwlee84/agent-skills/blob/main/docs/_snippets/external-install.md)，
並在每個列出外部條目的 catalog 頁首被 include。

狀態變更的 workflow —— 見
[Adding catalog entries](../workflows/adding-catalog-entries.md)。

## 另見 (See also) —— Reference 內的 landscape 頁面

[Reference](../reference/scripts.md) 區段已經放了我們*消費*但不*ship*
的工具的 landscape 頁：

- [Browser automation skills & MCPs](../reference/browser-automation-skills.md)
  —— Playwright vs agent-browser vs browser-use vs stagehand vs
  Playwright MCP 比較。
- [Deep Research landscape](../reference/deep-research-landscape.md) ——
  深度研究 (deep research) 工具與 persona 的 survey。
- [SDD frameworks & agent harnesses](../reference/sdd-and-harnesses.md)
  —— spec-kit / GSD / GSD-2 / OpenClaw / Pi SDK 比較。在
  [Agent Harness](domains/agent-harness.md) hub 中也有交叉引用 (cross-listed)。
- [Warp Oz skills](../reference/warp-oz-skills.md) —— Warp Oz skill 的
  vendoring 取捨理由。
- [Karpathy's LLM Wiki pattern](../reference/llm-wiki-pattern.md) ——
  [MCP wiki](mcp/index.md) 採用的設計樣式 (pattern)。

這些頁面留在 `Reference`（不放進 `Catalog`），因為它們記錄的是
*我們遵循*的慣例，不是*我們追蹤的外部條目*。Catalog 在相關處交叉
連結 (cross-link) 它們。
