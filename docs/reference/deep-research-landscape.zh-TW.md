# Deep Research landscape — Deep Research 生態盤點

!!! note "Terminology rule (zh-TW pages)"
    技術名詞首次出現以「中文 (English original)」格式呈現。**不自創翻譯**——
    若無公認譯名直接保留英文（如 `harness`、`SKILL.md`、`MCP`、`citation`）。
    代碼、API 名、CLI flag、套件名、檔名一律不翻。

這頁盤點主要 AI 廠商的 **Deep Research** 商業產品，以及試圖在本地復現
類似能力的 open-source skill / framework。同時說明本 repo 為何只 vendor
**一個** skill (`deep-research/`)，並記錄哪些相關選項刻意**不**納入。

## 商業 Deep Research 產品（2024–2026）

五大廠商最後都收斂到類似的形狀——multi-agent 規劃、平行檢索、citation
化合成——但在瀏覽範圍、模型大小、定價上的預設值不同。

| 廠商 | 產品 | 推出 | 架構 | 備註 |
|---|---|---|---|---|
| **OpenAI** | ChatGPT Deep Research（`o3-deep-research`、`o4-mini-deep-research`） | 2025-02 | 規劃 → 多步搜尋 → 帶引用報告 | Plus 25/月、Pro 250/月；2026-02 加上 scoped sites + 協同規劃 + 即時進度 |
| **Google** | Gemini Deep Research（Interactions API） | 2024-12 | Lead agent + 平行 sub-agents + 合成 agent | 串接 Gmail/Drive/Chat；1M token 上下文；Canvas 視覺化；2026-04 加入 MCP 工具連接 |
| **xAI** | Grok DeepSearch / DeeperSearch / Grok 4 Heavy | 2024-Q2 → 2025-07 | 多 agent 平行推理、即時 X + web 搜尋 | 256k token 上下文；目前無正式 citation；強調效能而非可驗證性 |
| **Anthropic** | Claude Research | 2025-06（工程部落格） | LeadResearcher + sub-agents + CitationAgent | 比 single-agent (Opus 4) 提升約 90%（Opus 4 lead + Sonnet 4 sub）；嚴格企業 privacy |
| **Meta** | （無第一方 DR 產品） | — | — | LLaMA 4 Scout/Maverick 是多模態 foundation model；deep research 須自組 LangChain / LlamaIndex / vector DB |

四個有出貨的產品共通 pattern：

1. **規劃** — 把 query 拆成 sub-question
2. **平行檢索** — 派 sub-agent 打 web search / docs / files
3. **迭代** — 根據找到的東西重新規劃、追 citation
4. **合成** — 組合成帶引用的報告（markdown / HTML / PDF）

典型 wall time 2–20 分鐘；成本由訂閱層級或 API 計費控制。

## 在本地復現 Deep Research——六層分工

agent CLI 想做出真正的「deep research」**不是一個 skill 能搞定的事**。
拆成六層，每層挑一個工具：

| 層 | 做什麼 | 代表工具 |
|---|---|---|
| 1. **規劃 / 分解** | 把問題拆成 sub-question、evidence 需求、研究計畫 | `199-biotechnologies/claude-deep-research-skill`（已 vendor）、`langchain-ai/deepagents`（Python framework，**不是** skill） |
| 2. **檢索** | Web / news / GitHub / PDF 搜尋 | [`tavily-ai/skills/tavily-search`](https://github.com/tavily-ai/skills)、[`firecrawl/cli/skills/firecrawl-search`](https://github.com/firecrawl/cli) |
| 3. **抽取** | 從 fetch 來的 URL 拉出主文、表格、多頁文字 | `firecrawl-scrape`、`firecrawl-crawl`、`firecrawl-parse` |
| 4. **瀏覽器互動** | 登入牆、JS render、動態 UI、下載 | [`vercel-labs/agent-browser`](https://github.com/vercel-labs/agent-browser)（32k⭐）、[`browser-use/browser-use`](https://github.com/browser-use/browser-use)（93k⭐） |
| 5. **Evidence 管理** | Source registry、claim ledger、citation 驗證 | `199-biotechnologies/claude-deep-research-skill`（內建） |
| 6. **合成** | 最終報告（markdown / HTML / PDF）+ 行內 citation | `199-biotechnologies/claude-deep-research-skill`、`tavily-ai/skills/tavily-research` |

最少 2 個 skill 就有可用結果：**(1) + (5) + (6)** 用一個有紀律的研究流程
skill 包辦，加 **(2)** 用一個你信任的 search backend。

## 本 repo vendor 了什麼

刻意只 vendor **一個** skill：

- **`vendor/deep-research/deep-research`**——來自
  [`199-biotechnologies/claude-deep-research-skill`](https://github.com/199-biotechnologies/claude-deep-research-skill)
  （646⭐）。純 prompt-flow skill，涵蓋規劃、evidence 管理、合成。四種
  模式：`quick`（3 phase、2–5 分鐘）、`standard`（6 phase、5–10 分鐘、
  預設）、`deep`（8 phase、10–20 分鐘）、`ultradeep`（8+ phase、20–45
  分鐘）。內建 evidence ledger + claim ledger，每個 finding 都能追回來源。

**為何只一個？** 用
[`tavily-ai/skills`](https://github.com/tavily-ai/skills)、
[`firecrawl/cli`](https://github.com/firecrawl/cli)、
[`vercel-labs/agent-browser`](https://github.com/vercel-labs/agent-browser)、
[`browser-use/browser-use`](https://github.com/browser-use/browser-use)
組出的 deep-research stack 全部都會引入**付費 API key、hosted backend、
或雲端 browser session**。本 repo 預設**不要花錢**——這樣任何人都能拿
vendor 進來的 research skill，搭配 agent 既有的工具（`WebSearch`、
`WebFetch`、MCP 等）直接跑，不必註冊第三方服務。

想要更高品質的 pipeline，把上述 skill **同時**裝起來——它們可以乾淨組合。

## 相鄰的選項——**不** vendor 的理由

記下來給未來的 agent 不要再爭：

| 選項 | Stars | 不 vendor 的原因 |
|---|---:|---|
| [`tavily-ai/skills`](https://github.com/tavily-ai/skills) | 285⭐ | 需要 Tavily 帳號 / API key。願意付費的話很好用，到時候再單獨裝。 |
| [`firecrawl/cli`](https://github.com/firecrawl/cli) | 375⭐ | 9 個 skill（search/scrape/crawl/map/extract/agent…）。有 free tier 但 production 仍需 key。比較適合 per-project 安裝。 |
| [`vercel-labs/agent-browser`](https://github.com/vercel-labs/agent-browser) | 32k⭐ | Browser automation 是重依賴（Chromium、profiles）。對 research-only stack 超出範圍；真的需要時再裝。 |
| [`browser-use/browser-use`](https://github.com/browser-use/browser-use) | 93k⭐ | Skills.sh 顯示 Gen Agent Trust Hub 安全 audit 失敗。等問題解決前先跳過。 |
| [`langchain-ai/deepagents`](https://github.com/langchain-ai/deepagents) | 22k⭐ | **不是 `SKILL.md` repo**——是 Python package / framework。**無法**當 agent skill vendor。ChatGPT 風格的整理常常誤標。 |
| [`24601/agent-deep-research`](https://github.com/24601/agent-deep-research) | 4⭐ | 真的是 Gemini Interactions API wrapper，但太小 / 太實驗。日後再評估。 |

### **看起來像** deep-research skill 但其實不是的

- [`forrestchang/andrej-karpathy-skills`](https://github.com/forrestchang/andrej-karpathy-skills)
  （124k⭐）——名字跟星數會誤導。它是**一個 `CLAUDE.md`**，把 Karpathy
  的 4 個 LLM coding pitfall 觀察整理成原則。**不是 skill、跟 research
  無關**。Karpathy **真正**發布過的個人知識庫 pattern 在他的
  [LLM Wiki gist](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f)，
  另見 [Karpathy's LLM Wiki pattern](llm-wiki-pattern.zh-TW.md)。

## 延伸閱讀

- [Karpathy's LLM Wiki pattern](llm-wiki-pattern.zh-TW.md)——跟 deep
  research 互補的持久知識庫 pattern（research 產出報告，wiki 累積它們）
- [SDD frameworks & agent harnesses](sdd-and-harnesses.zh-TW.md)——同樣
  的 skill / framework / harness 三層分類，套在 spec-driven development
- [Skill risk evaluations](skills-risk-evaluations.zh-TW.md)——一個
  workflow 該不該變成 skill 的判斷準則
