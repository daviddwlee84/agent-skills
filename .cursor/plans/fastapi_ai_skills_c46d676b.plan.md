---
name: FastAPI AI Skills
overview: 將《FastAPI for AI Engineers》一書萃取為三個獨立的 local agent skill（生產 pattern 指南、專案 scaffolder、面試題庫），全書 10 章範圍，內容以原創表述重寫並標註來源，並依本 repo 慣例掛載到 marketplace + docs。
todos:
  - id: patterns-skill
    content: "Scaffold + author fastapi-ai-patterns: SKILL.md (decision tables + top gotchas + reference routing) and 8 references covering all 10 chapters, original wording with source attribution; lint."
    status: completed
  - id: scaffold-skill
    content: "Scaffold + author fastapi-ai-scaffold: new-fastapi-ai-service.sh (bash 3.2, --help/--dry-run/JSON) + assets/ template tree (router/service/repo, lifespan, guardrails, SSE, tests, Docker, probes); lint."
    status: completed
  - id: interview-skill
    content: "Scaffold + author fastapi-ai-interview-prep: SKILL.md + 10 per-chapter reference files with self-written equivalent Q&A, optional quiz.py; lint."
    status: completed
  - id: marketplace
    content: Add 'fastapi-ai' plugin group with the 3 skills to skills/.claude-plugin/marketplace.json; run make marketplace.
    status: completed
  - id: docs
    content: Add bilingual docs (en + zh-TW) for each skill, index.md/index.zh-TW.md rows, mkdocs.yml nav, README table rows.
    status: completed
  - id: todo-1781761855920-v14686r0w
    content: git commit changes
    status: completed
isProject: false
---

## 目標與評估結論

書評：`FastAPI for AI Engineers` 是一本高品質、面向資深工程師的生產級參考書（89 頁、10 章，每章含正文、程式碼、Production Case Study、Cost Model 公式、System Design 情境、10 道面試題）。其 **AI serving 專屬的生產 pattern 與 gotchas** 正是高價值 skill 素材；通用 FastAPI（REST/CRUD/Pydantic 基礎）stock agent 已做得好，會以精簡 gotchas 帶過、不重複造輪子。

依你的決定：**三個獨立 skill，各自涵蓋全 10 章**。

## 硬限制：著作權（必讀）

書本版權頁為 "All rights reserved"。三個 skill 一律：
- 以**自己的話重寫**概念、決策表、pattern、gotchas（idea/fact 不受著作權保護，verbatim expression 受保護）。
- **不**逐字複製散文、程式碼 listing、或 100 題面試原文。
- 程式碼範例自行撰寫（功能等價即可）。
- 面試題 skill 以書中**主題**為骨架、撰寫等價問答，非複製。
- 在每個 SKILL.md 與 docs 頁標註 "Inspired by *FastAPI for AI Engineers* (AI Engineering Insider, 2026)" 作為來源致謝。

## 三個 skill 設計

全部放 `skills/local/`，用 [`skills/local/skill-author/scripts/new-skill.sh`](skills/local/skill-author/scripts/new-skill.sh) `--local` 模式 scaffold（自動建立 `.agents/skills/` 與 `.claude/skills/` 探索 symlink）。命名共用 `fastapi-ai-` 前綴。

### 1. `fastapi-ai-patterns` — 生產 pattern 與 gotchas 指南（知識型）
- 觸發：建構/審查 FastAPI 服務，尤其 AI/ML serving。
- `SKILL.md`：核心心智模型（endpoint = typed contract）、**def vs async def 決策表**、最高價值 gotchas（async handler 內阻塞 event loop、模型只在 `lifespan` 載入、`response_model` 防敏感欄位外洩、BOLA 授權要在 SQL 而非 prompt、generate→Pydantic validate→重試的 LLM 契約化 loop），以及「遇到 Y 時讀 references/X」的路由。
- `references/`（對應全書 10 章，分 8 檔）：`api-design.md`(Ch1-3)、`architecture-di.md`(Ch4)、`database.md`(Ch5)、`security.md`(Ch6)、`testing.md`(Ch7)、`async-and-external.md`(Ch8)、`ai-ml-serving.md`(Ch9)、`deployment-observability.md`(Ch10)。每檔含該主題 pattern + gotchas + cost/容量心法（公式自行重述）。

### 2. `fastapi-ai-scaffold` — 生產級專案 scaffolder（腳本型）
- 觸發：使用者要「新建一個生產級 FastAPI AI/ML 服務」。
- `scripts/new-fastapi-ai-service.sh`（bash 3.2、`--help`/`--dry-run`、JSON stdout，遵循 [`references/script-design.md`](skills/local/skill-author/references/script-design.md)）：依 clean architecture 生成專案樹。
- `assets/` 模板樹：`app/`（router/service/repository 分層）、Pydantic v2 分離式 schema、`lifespan` 載入模型 + 共用 `httpx.AsyncClient`、JWT current-user 依賴、SQLModel + Alembic、guardrails + validation-loop helper、SSE streaming endpoint、`tests/`（`dependency_overrides`）、`Dockerfile`、gunicorn+uvicorn 設定、`/health` + `/ready` 探針、結構化 logging、`pyproject.toml`。
- `SKILL.md`：何時用、生成什麼、如何擴充。

### 3. `fastapi-ai-interview-prep` — 面試題庫（知識型）
- 觸發：FastAPI / AI 工程面試準備、模擬面試、自我測驗。
- `SKILL.md`：使用方式（mock interview / 主題抽題 / senior nuance 評分）、主題地圖。
- `references/`：`ch01-intro.md` … `ch10-deployment.md`（10 檔），每檔 10 題**自撰**等價問答含資深要點。
- 選配 `scripts/quiz.py`（PEP 723 + `uv run`）：隨機抽題、先藏答案的自測 CLI。

## 掛載步驟（每個 skill 都要做，依本 repo 慣例）

來源：[`this-repo-conventions.md`](skills/local/skill-author/references/this-repo-conventions.md)。

1. `new-skill.sh --local <name>` scaffold（建 dir + symlink）。
2. 撰寫 `SKILL.md` + `references/` + `scripts/` + `assets/`。
3. `lint-skill.sh <skill-dir>` 通過（frontmatter、description ≤1024 且含觸發語、script `--help`、reference 可達）。
4. `skills/.claude-plugin/marketplace.json` 新增 plugin group `fastapi-ai`（category `Web`），列入三個 skill 路徑 `./local/fastapi-ai-*`；跑 `make marketplace`。
5. docs（雙語）：每個 skill 建 `docs/skills/<name>.md` + `<name>.zh-TW.md`；於 `docs/skills/index.md` 與 `index.zh-TW.md` 各加一列；`mkdocs.yml` 加 nav；`README.md` "What's in here" 加列。
6. `make kanban` 前置：用 [`scripts/promote-todo.sh`](scripts/promote-todo.sh) 或 add-todo 記錄（若有對應 TODO 項）。

## 風險與順序建議

- 工作量大（3 skill × ~10 reference + scaffold 模板 + 6 docs 頁 + marketplace + nav）。建議**分階段**：先做 `fastapi-ai-patterns`（價值最高、純文字）→ 再 `fastapi-ai-scaffold`（模板最耗時）→ 最後 `fastapi-ai-interview-prep`。
- 三 skill 內容有重疊（patterns vs scaffold 都涉及生產 pattern）；以交叉連結處理，不複製。
- 需切換到 agent 模式才能實際建檔。