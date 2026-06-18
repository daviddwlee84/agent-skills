# fastapi-ai-scaffold

!!! note "Terminology rule (zh-TW pages)"
    技術名詞首次出現以「中文 (English original)」格式呈現，例：依賴注入
    (dependency injection)。**不自創翻譯**——若無公認譯名直接保留英文
    （如 `embedding`、`tokenizer`）。代碼、API 名、CLI flag、套件名、檔名一律不翻。

從內建 skeleton 生成一個可直接跑、production 形狀的 FastAPI AI/ML 服務，
讓你不必每次重推同樣的接線。生成的目錄樹把
[`fastapi-ai-patterns`](fastapi-ai-patterns.md) 的 pattern 落成可運作的程式碼 ——
inference 服務上線前需要的那層「無聊但正確」的基線。

> 啟發自 *FastAPI for AI Engineers* (AI Engineering Insider, 2026)。所有生成的
> 程式碼皆為原創。

## 出貨內容 (What ships)

- 完整 SKILL.md
  ([skills/local/fastapi-ai-scaffold/SKILL.md](https://github.com/daviddwlee84/agent-skills/blob/main/skills/local/fastapi-ai-scaffold/SKILL.md))
  —— 何時用、生成什麼、如何把 stub 換成你的模型。
- 一個 script：
    - [`new-fastapi-ai-service.sh`](https://github.com/daviddwlee84/agent-skills/blob/main/skills/local/fastapi-ai-scaffold/scripts/new-fastapi-ai-service.sh)
      —— 複製 skeleton、去掉每個檔的 `.tmpl` 後綴、替換專案 slug。Bash 3.2；
      `--help` / `--dry-run` / `--name` / `--force`；stdout 輸出 JSON 摘要。
- 一個 44 檔的 skeleton 放在
  [`assets/project/`](https://github.com/daviddwlee84/agent-skills/tree/main/skills/local/fastapi-ai-scaffold/assets/project)
  （每檔皆 `*.tmpl`）：clean-architecture 的 `app/`（router → service →
  repository）、`lifespan` 載入模型 + 共用 `httpx.AsyncClient` + DB engine、
  `/health` + `/ready` probe、JWT 認證 (authentication)（pinned algorithm、
  bcrypt）、SQLModel + Alembic、SSE 的 LLM gateway、guardrail + Pydantic
  validation loop、結構化 JSON logging、用 `dependency_overrides` + 記憶體內
  SQLite 的 `tests/`，外加 `Dockerfile`、`gunicorn_conf.py`、`pyproject.toml`、
  `.env.example`。

## 快速開始

```bash
# 預覽，不寫檔：
bash skills/local/fastapi-ai-scaffold/scripts/new-fastapi-ai-service.sh --dry-run ./my-service

# 生成：
bash skills/local/fastapi-ai-scaffold/scripts/new-fastapi-ai-service.sh ./my-service

cd ./my-service
uv venv && source .venv/bin/activate
uv pip install -e ".[dev]"
cp .env.example .env          # 設定 JWT_SECRET、DATABASE_URL、MODEL_PATH
uvicorn app.main:app --reload # http://127.0.0.1:8000/docs
pytest -q                     # 內建測試立即通過
```

內建測試與真實 lifespan 啟動都在出貨前驗證過，所以剛生成的專案開箱即綠。

## 注意

- 生成的 package 一律是 `app`；只有專案 *metadata*（pyproject name、README
  標題、`.env` 的 `APP_NAME`）用 slug。
- `app/ml/model.py` 裡的模型與 LLM 是 deterministic stub —— 換成你的真實
  artifact；結構與 offload 不變。

## Cross-references

- 每個生成片段的 pattern 理由：[`fastapi-ai-patterns`](fastapi-ai-patterns.md)。
- FastAPI 文件：[fastapi.tiangolo.com](https://fastapi.tiangolo.com)。
