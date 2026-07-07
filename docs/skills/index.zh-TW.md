# Skills overview — Skill 總覽

!!! note "Terminology rule (zh-TW pages)"
    技術名詞首次出現以「中文 (English original)」格式呈現，例：依賴注入
    (dependency injection)。**不自創翻譯**——若無公認譯名直接保留英文
    （如 `embedding`、`tokenizer`）。代碼、API 名、CLI flag、套件名、檔名一律不翻。

這頁列出這個 repo 打包的所有 skill。

- **Local skill** (`skills/local/`) 在這裡撰寫與維護。
- **Vendored skill** (`skills/vendor/`) 從 upstream repo 精選 (cherry-pick)
  過來，透過
  [`vendor.yaml`](https://github.com/daviddwlee84/agent-skills/blob/main/vendor.yaml)
  manifest 同步 —— 詳見 [Adding vendor skills](../workflows/adding-vendor-skills.md)。
  **不要**在本機編輯 vendored 的 SKILL.md 檔；變更會在下次 `make sync`
  被蓋掉。

## Local skills

自製、依本 repo 慣例維護（詳見 [Conventions](../conventions.md)）。

| Skill | 一行描述 | 詳細頁面 |
|---|---|---|
| [`project-knowledge-harness`](project-knowledge-harness.md) | TODO + backlog + pitfalls 結構，附帶 validator/init/promote 工具組 | [docs](project-knowledge-harness.md) |
| [`quantatitive-factor-researcher`](quantatitive-factor-researcher.md) | 給 Python 策略開發用的量化因子研究 persona | [docs](quantatitive-factor-researcher.md) |
| [`skill-author`](skill-author.md) | 依 agentskills.io best practices 撰寫新 skill；附 `new-skill.sh` 與 `lint-skill.sh` | [docs](skill-author.md) |
| [`verifiable-surfaces`](verifiable-surfaces.md) | 設計可驗證的 CLI/tool/service surface (`--help`/`--dry-run`/`--print-config`/isolated smoke)，並用 app-native loader 驗證 config 變更 | [docs](verifiable-surfaces.md) |
| [`demo-evidence`](demo-evidence.md) | 把驗收證據(截圖/錄影/HTTP log)歸檔到受 gitignore 保護的 `.evidence/` bundle，關聯 git branch/commit + agent session，供非同步「Demos over diffs」驗收 | [docs](demo-evidence.md) |
| [`mkdocs-site-bootstrap`](mkdocs-site-bootstrap.md) | 啟動 MkDocs Material 站 + GitHub Pages 部署；以 `.skills/preferences.yaml` consent-gate | [docs](mkdocs-site-bootstrap.md) |
| [`marimo-batch-mlflow`](marimo-batch-mlflow.md) | marimo 雙模式 (UI + batch CLI) notebook，搭配 Tyro + MLflow | [docs](marimo-batch-mlflow.md) |
| [`dvc-ml-workflow`](dvc-ml-workflow.md) | DVC pipeline + queued experiment，metrics 自動繫結到 ephemeral commit；附 init/queue/lint helper | [docs](dvc-ml-workflow.md) |
| [`mlflow-tracking`](mlflow-tracking.md) | 通用 MLflow skill —— sqlite + `mlflow ui`、附帶 PostgreSQL + MinIO docker stack、LLM tracing、registry、autolog | [docs](mlflow-tracking.md) |
| [`agent-history-hygiene`](agent-history-hygiene.md) | 把 SpecStory transcript + plan 檔跟功能 diff 一起 commit；初始化 pre-commit + gitleaks + redactor；rotate-first 洩漏處理流程 | [docs](agent-history-hygiene.md) |
| [`pueue-job-queue`](pueue-job-queue.md) | 驅動 Nukesor/pueue 做佇列 (queued) / 平行 / 排程的 shell job；submit-one + DAG submitter + JSON-summary waiter；對應 pueue 4.0.2 schema | [docs](pueue-job-queue.md) |
| [`clash-proxy-api`](clash-proxy-api.md) | 探索並操作 Clash/mihomo external-controller：status/模式/TUN/切節點/重載/連線 + 作業系統系統代理開關；多用戶端（Verge Rev、ClashX、mihomo CLI）並附啟用 API 的引導 | [docs](clash-proxy-api.md) |
| [`fastapi-ai-patterns`](fastapi-ai-patterns.md) | AI/ML/LLM serving 的 production FastAPI pattern + gotcha；`def`/`async` 決策表 + 涵蓋全 10 章的 8 份 reference | [docs](fastapi-ai-patterns.md) |
| [`fastapi-ai-scaffold`](fastapi-ai-scaffold.md) | 生成 production 形狀的 FastAPI AI 服務（clean architecture、lifespan 載入模型、JWT、SSE、probe、測試、Docker）；`new-fastapi-ai-service.sh` + 44 檔 skeleton | [docs](fastapi-ai-scaffold.md) |
| [`fastapi-ai-interview-prep`](fastapi-ai-interview-prep.md) | 100 題自撰的 FastAPI/AI 面試問答，橫跨 10 個主題 + `quiz.py` mock interview CLI | [docs](fastapi-ai-interview-prep.md) |

## Vendored skills

第三方 skill 之所以被精選進來，是因為它們填補 local skill 沒涵蓋的
缺口，或者 upstream 是該主題的 canonical 權威。連結頁面顯示每個 skill
教什麼、upstream 來源、以及 `vendor.yaml` 中追蹤的 last-sync commit。

Vendored skill 可以 **平鋪 (flat)** (`skills/vendor/<name>/`) 或被分組
進一個 **series** (`skills/vendor/<series>/<name>/`)。
series 怎麼運作見
[Adding vendor skills](../workflows/adding-vendor-skills.md#series-grouping)。

### Flat (notebooks + meta)

| Skill | Upstream | 詳細頁面 |
|---|---|---|
| [`marimo-notebook`](marimo-notebook.md) | [marimo-team/skills](https://github.com/marimo-team/skills/tree/main/skills/marimo-notebook) | [docs](marimo-notebook.md) |
| [`streamlit-to-marimo`](streamlit-to-marimo.md) | [marimo-team/skills](https://github.com/marimo-team/skills/tree/main/skills/streamlit-to-marimo) | [docs](streamlit-to-marimo.md) |
| [`anywidget`](anywidget.md) | [marimo-team/skills](https://github.com/marimo-team/skills/tree/main/skills/anywidget) | [docs](anywidget.md) |
| [`skill-creator`](skill-creator.md) | [anthropics/skills](https://github.com/anthropics/skills/tree/main/skills/skill-creator) | [docs](skill-creator.md) |

### Fullstack Next.js series

`series: fullstack-nextjs` —— Next.js (App Router) + Supabase (Postgres) +
shadcn/ui + Tailwind CSS + design / testing skill。全部來自官方組織
(Vercel、vercel-labs、Supabase、Anthropic)。

| Skill | Upstream | 詳細頁面 |
|---|---|---|
| [`nextjs`](nextjs.md) | [vercel/vercel-plugin](https://github.com/vercel/vercel-plugin/tree/main/skills/nextjs) | [docs](nextjs.md) |
| [`shadcn`](shadcn.md) | [vercel/vercel-plugin](https://github.com/vercel/vercel-plugin/tree/main/skills/shadcn) | [docs](shadcn.md) |
| [`react-best-practices`](react-best-practices.md) | [vercel/vercel-plugin](https://github.com/vercel/vercel-plugin/tree/main/skills/react-best-practices) | [docs](react-best-practices.md) |
| [`vercel-storage`](vercel-storage.md) | [vercel/vercel-plugin](https://github.com/vercel/vercel-plugin/tree/main/skills/vercel-storage) | [docs](vercel-storage.md) |
| [`supabase`](supabase.md) | [supabase/agent-skills](https://github.com/supabase/agent-skills/tree/main/skills/supabase) | [docs](supabase.md) |
| [`supabase-postgres-best-practices`](supabase-postgres-best-practices.md) | [supabase/agent-skills](https://github.com/supabase/agent-skills/tree/main/skills/supabase-postgres-best-practices) | [docs](supabase-postgres-best-practices.md) |
| [`web-design-guidelines`](web-design-guidelines.md) | [vercel-labs/agent-skills](https://github.com/vercel-labs/agent-skills/tree/main/skills/web-design-guidelines) | [docs](web-design-guidelines.md) |
| [`frontend-design`](frontend-design.md) | [anthropics/skills](https://github.com/anthropics/skills/tree/main/skills/frontend-design) | [docs](frontend-design.md) |
| [`webapp-testing`](webapp-testing.md) | [anthropics/skills](https://github.com/anthropics/skills/tree/main/skills/webapp-testing) | [docs](webapp-testing.md) |

每個 local skill 都遵守的規則（佈局、命名、scripts、references）見
[Conventions](../conventions.md)。vendor 從頭到尾怎麼運作見
[Adding vendor skills](../workflows/adding-vendor-skills.md)。
