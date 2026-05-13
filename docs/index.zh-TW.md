# Agent Skills

!!! note "Terminology rule (zh-TW pages)"
    技術名詞首次出現以「中文 (English original)」格式呈現，例：依賴注入
    (dependency injection)。**不自創翻譯**——若無公認譯名直接保留英文
    （如 `embedding`、`tokenizer`）。代碼、API 名、CLI flag、套件名、檔名一律不翻。

個人收藏的 [agent skills](https://agentskills.io/home) —— 包含自製的 skill 與從
upstream repo 精選 (cherry-picked) 過來的 skill —— 可作為單一套件 (package) 安裝。

## 安裝 (Install)

--8<-- "_snippets/install.md"

## 內容概覽

`skills/` 底下有兩種 skill：

- **`skills/local/`** —— 在這個 repo 內自製維護的 skill。索引請看
  [Skills 總覽](skills/index.md)。
- **`skills/vendor/`** —— 透過
  [`vendor.yaml`](https://github.com/daviddwlee84/agent-skills/blob/main/vendor.yaml)
  manifest 從 upstream repo 同步過來的第三方 skill。詳見
  [Adding vendor skills](workflows/adding-vendor-skills.md)。

這個 repo 同時也是
[`project-knowledge-harness`](skills/project-knowledge-harness.md) skill 套用在
自己身上的活範例：[`TODO.md`](https://github.com/daviddwlee84/agent-skills/blob/main/TODO.md)、
[`backlog/`](https://github.com/daviddwlee84/agent-skills/tree/main/backlog)、
[`pitfalls/`](https://github.com/daviddwlee84/agent-skills/tree/main/pitfalls)
位於 repo 根目錄，搭配 [`scripts/`](reference/scripts.md) 包裝
validator / promoter / inbox 工具組。

## 接下來去哪？

| 你的目的 | 該讀的頁面 |
|---|---|
| 安裝並試用這些 skill | [Getting Started](getting-started.md) |
| 了解命名 / 佈局規則 | [Conventions](conventions.md) |
| 加入第三方 skill | [Adding vendor skills](workflows/adding-vendor-skills.md) |
| 自己寫一個 local skill | [Creating local skills](workflows/creating-local-skills.md) |
| 在你的 project 裡記錄 TODO 或 pitfall | [Project memory workflow](workflows/project-memory.md) |
| 瀏覽現有的 skill | [Skills 總覽](skills/index.md) |
| 瀏覽外部 skill、MCP、領域 (domain) hub | [Catalog](catalog/index.md) |
| 為自己的 project 建立 docs 站 (site) | [Downstream docs stack recipe](reference/docs-stack-recipe.md) |

## 給 AI assistant 的入口

這個站點依照 [llmstxt.org](https://llmstxt.org/) 規範提供 LLM-friendly endpoint：

- [`llms.txt`](llms.txt) —— 所有頁面的精簡索引 (index)
- [`llms-full.txt`](llms-full.txt) —— 所有頁面串接成的單一檔案
- 任何頁面在 URL 後面加上 `/index.md` 就能取得 raw Markdown
  （例如 [`getting-started/index.md`](getting-started/index.md)）。

如果你是讀這頁的 agent，建議用 `llms-full.txt` 一次拿到完整 context，
或是抓特定頁面的 `*/index.md` 路徑。
