# mlflow-tracking

!!! note "Terminology rule (zh-TW pages)"
    技術名詞首次出現以「中文 (English original)」格式呈現，例：依賴注入
    (dependency injection)。**不自創翻譯**——若無公認譯名直接保留英文
    （如 `embedding`、`tokenizer`）。代碼、API 名、CLI flag、套件名、檔名一律不翻。

通用 [MLflow](https://mlflow.org/docs/latest) skill (upstream
[mlflow/mlflow](https://github.com/mlflow/mlflow)) —— 涵蓋 experiment
tracking、model registry、與 LLM tracing，適用於任何 Python project。

這是 **general-purpose** 的 MLflow skill。如果要的是 marimo 專用的雙模式
(UI + batch CLI) 變體，請改用
[`marimo-batch-mlflow`](marimo-batch-mlflow.md) —— 那個是建立在 marimo
notebook 之上的特化版本。

## 三種部署模式 (寫 code 前先選一種)

| 模式 | Tracking URI | 何時選 |
|---|---|---|
| File | `file:./mlruns` (預設) | 一次性實驗、不要 UI、不要 model registry |
| **SQLite + `mlflow ui`** ⭐ | `sqlite:///mlflow.db` | 個人作業、想要 UI 但不想跑 server、需要 model registry |
| **Docker Compose stack** ⭐ | `http://host:8000` (PostgreSQL + MinIO) | 團隊使用、production、平行 job、大型 artifact |
| Databricks-managed | `databricks://` | 已經付錢給 Databricks (本 skill 範圍外) |

兩個有星號的模式涵蓋 ~95% 真實使用情境。**File 模式不支援 model
registry** —— 如果使用者要用 `register_model`，需要 SQLite 或 server。

## 出貨內容 (What ships)

- 完整的 SKILL.md
  ([skills/local/mlflow-tracking/SKILL.md](https://github.com/daviddwlee84/agent-skills/blob/main/skills/local/mlflow-tracking/SKILL.md))
  含部署模式決策表、Manual-vs-Autolog 選擇、以及對應實際 production
  失敗 calibrate 過的 gotcha 區段（`mlflow ui` 的 `--backend-store-uri`
  陷阱、autolog 順序、棄用 stage 等）。
- 六份 reference —— 按需載入：
    - [`sqlite-local.md`](https://github.com/daviddwlee84/agent-skills/blob/main/skills/local/mlflow-tracking/references/sqlite-local.md)
      —— SQLite 模式 setup、`--backend-store-uri` 陷阱、何時遷移到
      PostgreSQL。
    - [`docker-compose-server.md`](https://github.com/daviddwlee84/agent-skills/blob/main/skills/local/mlflow-tracking/references/docker-compose-server.md)
      —— production stack 維運、`.env` 客製化、AWS S3 替換、basic
      auth、備份策略。
    - [`llm-tracing.md`](https://github.com/daviddwlee84/agent-skills/blob/main/skills/local/mlflow-tracking/references/llm-tracing.md)
      —— 依供應商 autolog (OpenAI、Anthropic、LangChain、LlamaIndex、
      DSPy、AutoGen、CrewAI、LiteLLM、Bedrock、Gemini、…)、
      `@mlflow.trace`、span 類型、`search_traces`、與
      Weave/LangSmith/Langfuse 的比較。
    - [`model-registry.md`](https://github.com/daviddwlee84/agent-skills/blob/main/skills/local/mlflow-tracking/references/model-registry.md)
      —— **alias** (現行 API：Champion / Challenger) vs 棄用的 stage、
      註冊 pattern、webhook。
    - [`autologging-by-framework.md`](https://github.com/daviddwlee84/agent-skills/blob/main/skills/local/mlflow-tracking/references/autologging-by-framework.md)
      —— 每個官方支援的框架及 per-library 陷阱 (sklearn、pytorch、
      lightning、tensorflow、keras、xgboost、lightgbm、catboost、
      statsmodels、spark、fastai、paddle、transformers、…)。
    - [`mlflow-widgets-anywidget.md`](https://github.com/daviddwlee84/agent-skills/blob/main/skills/local/mlflow-tracking/references/mlflow-widgets-anywidget.md)
      —— 在 marimo / Jupyter 中使用
      [mlflow-widgets](https://github.com/daviddwlee84/mlflow-widgets)
      做即時圖表，無需啟動完整 UI。
- 三個 script：
    - [`init-mlflow-sqlite.sh`](https://github.com/daviddwlee84/agent-skills/blob/main/skills/local/mlflow-tracking/scripts/init-mlflow-sqlite.sh)
      —— idempotent 的 SQLite 模式 setup；印出帶正確
      `--backend-store-uri` 的 `mlflow ui` 指令 (SQLite 第一名陷阱)。
    - [`start-mlflow-server.sh`](https://github.com/daviddwlee84/agent-skills/blob/main/skills/local/mlflow-tracking/scripts/start-mlflow-server.sh)
      —— 把 bundled docker-compose stack 複製到目標目錄、產生帶
      rotate 過隨機 secret 的 `.env`、跑 `docker compose up -d`、
      等 healthcheck、印出 URL 與 client 端要 export 的 env var。
    - [`tail-runs.sh`](https://github.com/daviddwlee84/agent-skills/blob/main/skills/local/mlflow-tracking/scripts/tail-runs.sh)
      —— PEP 723 inline-deps Python script (透過 `uv run` 跑、
      無需 env setup)，包裝 `mlflow.search_runs` 並提供 JSON 或 CSV
      輸出供終端使用。
- vendored 在 `assets/docker-compose-stack/` 的 production stack：
    - [`docker-compose.yaml`](https://github.com/daviddwlee84/agent-skills/blob/main/skills/local/mlflow-tracking/assets/docker-compose-stack/docker-compose.yaml)
      —— PostgreSQL + MinIO + tracking server + bucket bootstrap，
      含 healthcheck 與 `depends_on` 順序。
    - [`Dockerfile`](https://github.com/daviddwlee84/agent-skills/blob/main/skills/local/mlflow-tracking/assets/docker-compose-stack/Dockerfile)
      —— 鎖定 (pin) 過的 MLflow image + `psycopg2-binary` + `boto3`。
    - [`.env.example`](https://github.com/daviddwlee84/agent-skills/blob/main/skills/local/mlflow-tracking/assets/docker-compose-stack/.env.example)
      —— 所有旋鈕都文件化；預設 port 8000 避開 macOS AirPlay 的 5000。
    - [`README.md`](https://github.com/daviddwlee84/agent-skills/blob/main/skills/local/mlflow-tracking/assets/docker-compose-stack/README.md)
      —— 快速開始、疑難排解、何時超出這個 stack 的能力。

## 為什麼跟 `marimo-batch-mlflow` 共存

| 關注點 | `mlflow-tracking` (這個) | `marimo-batch-mlflow` |
|---|---|---|
| Scope | 任何 Python project、任何 trainer | 專門針對 marimo notebook |
| 焦點 | Tracking server setup、registry、LLM trace、autolog | 雙模式 notebook pattern (UI + CLI) 使用 MLflow |
| 含 Docker stack？ | 是，從 production vendor | 否 |
| 含 LLM tracing？ | 是，完整 reference | 否 |

當使用者要用 MLflow 作為通用 tracking backend 時用這個 skill。
當他們特別在寫需要同時當互動 UI 跟 batch CLI 跑的 marimo notebook
時用 `marimo-batch-mlflow`。

## 快速開始

**SQLite (個人)**：

```bash
bash skills/local/mlflow-tracking/scripts/init-mlflow-sqlite.sh
# → 印出精確的 `mlflow ui --backend-store-uri sqlite:///mlflow.db --port 5001`
```

**Docker Compose stack (團隊)**：

```bash
bash skills/local/mlflow-tracking/scripts/start-mlflow-server.sh \
  --target-dir infra/mlflow
# → 複製 stack、在 .env 中 rotate secret、啟動、等 healthcheck、
#   印出 client 機器要 export 的 env var
```

**在你的訓練 code 中** (任何模式都通用)：

```python
import mlflow

mlflow.set_tracking_uri("http://localhost:8000")    # 或 "sqlite:///mlflow.db"
mlflow.set_experiment("my-project")
mlflow.autolog()                                    # zero-touch logging

with mlflow.start_run():
    model.fit(X, y)                                 # params、metrics、model 全部 logged
```

## Cross-references

- 官方文件：[mlflow.org/docs/latest](https://mlflow.org/docs/latest) ——
  永遠連這個。MLflow 每 4–6 週出貨；LLM tracing 特別是個移動標靶。
- Upstream repo：[github.com/mlflow/mlflow](https://github.com/mlflow/mlflow)。
- [`mlflow-widgets`](https://github.com/daviddwlee84/mlflow-widgets) ——
  anywidget-based 的圖表 / 表格，把即時 MLflow 資料嵌進 marimo /
  Jupyter cell。Demo：
  [daviddwlee84.github.io/mlflow-widgets](https://daviddwlee84.github.io/mlflow-widgets/)。
- [`marimo-batch-mlflow`](marimo-batch-mlflow.md) —— 給雙模式 (UI + batch
  CLI) notebook 用的 marimo 專屬變體。
