# AI/ML Research —— AI/ML 研究

!!! note "Terminology rule (zh-TW pages)"
    技術名詞首次出現以「中文 (English original)」格式呈現，例：依賴注入
    (dependency injection)。**不自創翻譯**——若無公認譯名直接保留英文
    （如 `embedding`、`tokenizer`）。代碼、API 名、CLI flag、套件名、檔名一律不翻。

實驗追蹤 (experiment tracking)、模型生命週期 (model lifecycle)、
資料版本管理 (data versioning)、notebook、fine-tuning、agent framework
與更廣的 research-engineering 工具 stack。

## 此 repo 內的 skill

### Local

| Skill | 一句話 | 備註 |
|---|---|---|
| [`mlflow-tracking`](../../skills/mlflow-tracking.md) | 通用 MLflow —— 單機 sqlite + `mlflow ui`、團隊用 PostgreSQL + MinIO docker；附 LLM tracing、registry、autolog。 | |
| [`dvc-ml-workflow`](../../skills/dvc-ml-workflow.md) | DVC pipeline + queued experiment，metrics 自動綁到臨時 commit。 | |
| [`marimo-batch-mlflow`](../../skills/marimo-batch-mlflow.md) | marimo 雙模式（UI + batch CLI）notebook，搭配 Tyro + MLflow。 | |

### Vendored

| Skill | Upstream | Series |
|---|---|---|
| [`marimo-notebook`](../../skills/marimo-notebook.md) | [`marimo-team/skills`](https://github.com/marimo-team/skills/tree/main/skills/marimo-notebook) | flat |
| [`streamlit-to-marimo`](../../skills/streamlit-to-marimo.md) | [`marimo-team/skills`](https://github.com/marimo-team/skills/tree/main/skills/streamlit-to-marimo) | flat |
| [`anywidget`](../../skills/anywidget.md) | [`marimo-team/skills`](https://github.com/marimo-team/skills/tree/main/skills/anywidget) | flat |
| [`deep-research`](https://github.com/199-biotechnologies/deep-research) | `199-biotechnologies/deep-research` | `deep-research` series |

## External skills（手動安裝）

--8<-- "_snippets/external-install.md"

| Skill / Plugin | Upstream | Status | 為何此狀態 | 安裝提示 |
|---|---|---|---|---|
| `AI-research-SKILLs`（完整 library） | [`Orchestra-Research/AI-research-SKILLs`](https://github.com/Orchestra-Research/AI-research-SKILLs) | `wishlist` | 跨 23 個分類的 98 個 skill —— 從 architecture（LitGPT、Mamba、NanoGPT）、fine-tuning（Axolotl、LLaMA-Factory、PEFT）到 inference（vLLM、TensorRT-LLM）的完整研究生命週期。範圍太廣不會整批 vendor，會精選 (cherry-pick)。 | `npx @orchestra-research/ai-research-skills`（他們的 npm wrapper）或瀏覽後 `npx skills@latest add Orchestra-Research/AI-research-SKILLs/<category>/<skill>`。 |
| `bio-research` plugin | [`anthropics/knowledge-work-plugins/bio-research`](https://github.com/anthropics/knowledge-work-plugins/tree/main/bio-research) | `wishlist` | PubMed、BioRender、bioRxiv、ChEMBL、Benchling、Open Targets connector。本身不直接適用，但作為 life-sciences research workflow 的參考 (reference) 有價值。 | `claude plugin install bio-research@knowledge-work-plugins` |

## MCP servers

| 名稱 | Upstream | Status | Auth | 紀錄 |
|---|---|---|---|---|
| _尚未調查_ | | | | |

## Backlog（TODO `P?` 條目）

見 [`TODO.md` 的 `P?` 區](https://github.com/daviddwlee84/agent-skills/blob/main/TODO.md)：

- `[?/L]` **LangChain / LangSmith / LangServe / LangGraph / Langfuse**
  —— 把 orchestration + observability stack 包成一組 skill。
- `[?/L]` **LLM fine-tuning skill** —— 監督式 (supervised) fine-tuning
  與 adapter-based tuning 的實作 workflow。
- `[?/M]` **Build MCP skill** —— 建立、測試、記錄 MCP server 的最小
  workflow（注意：`mcp-builder` 已 vendored —— 若已涵蓋則重新評估）。
- `[?/M]` **Hugging Face Spaces + Gradio skill** —— demo app 部署、
  secret 處理、本機到託管 (hosted) 的交接。
- `[?/M]` **Data visualization skill** —— Matplotlib + Seaborn + Plotly
  用於探索性 (exploratory) + 報告級 (report-ready) 圖表。

## 另見

- [`docs/reference/deep-research-landscape.md`](../../reference/deep-research-landscape.md)
  —— 深度研究 (deep research) 工具與 persona 的 survey。
- [`docs/reference/llm-wiki-pattern.md`](../../reference/llm-wiki-pattern.md)
  —— Karpathy 的個人研究筆記 LLM Wiki 樣式 (pattern)。
- [Quant Research](quant-research.md) —— experiment tracking + notebook
  stack 的重疊部分。
