# fastapi-ai-patterns

!!! note "Terminology rule (zh-TW pages)"
    技術名詞首次出現以「中文 (English original)」格式呈現，例：依賴注入
    (dependency injection)。**不自創翻譯**——若無公認譯名直接保留英文
    （如 `embedding`、`tokenizer`）。代碼、API 名、CLI flag、套件名、檔名一律不翻。

FastAPI 服務的 production pattern 與 gotcha 指南，重點放在 **AI/ML/LLM serving**
跟一般 CRUD 不一樣的地方。這是知識型 skill：`SKILL.md` 本體放跨領域的決策與
agent 預設會做錯的陷阱，再依主題路由到八份 reference 之一深入。

> 啟發自 *FastAPI for AI Engineers: From First Endpoint to Production-Scale AI
> Systems* (AI Engineering Insider, 2026)。所有內容以原創措辭重新表述 ——
> 取其概念與事實 (idea/fact)，非書中散文或 code listing。

## 出貨內容 (What ships)

- 完整 SKILL.md
  ([skills/local/fastapi-ai-patterns/SKILL.md](https://github.com/daviddwlee84/agent-skills/blob/main/skills/local/fastapi-ai-patterns/SKILL.md))
  含 `endpoint = typed contract` 心智模型、**`def` vs `async def` 決策表**、
  以及最高價值的 gotcha（阻塞 event loop、模型在 `lifespan` 載入、
  `response_model` 防洩漏、授權 (authorization) 寫在 query、
  LLM generate→validate→retry loop）前置呈現。
- 八份 reference，涵蓋全書 10 章 —— 按需讀取：
    - [`api-design.md`](https://github.com/daviddwlee84/agent-skills/blob/main/skills/local/fastapi-ai-patterns/references/api-design.md)
      —— ASGI vs WSGI、REST/idempotency、status code、pagination、Pydantic v2 (Ch 1–3)。
    - [`architecture-di.md`](https://github.com/daviddwlee84/agent-skills/blob/main/skills/local/fastapi-ai-patterns/references/architecture-di.md)
      —— `Depends()` 解析 + 快取、`yield` dependency、分層 (Ch 4)。
    - [`database.md`](https://github.com/daviddwlee84/agent-skills/blob/main/skills/local/fastapi-ai-patterns/references/database.md)
      —— session、N+1、SQLModel vs SQLAlchemy、Alembic、pool sizing (Ch 5)。
    - [`security.md`](https://github.com/daviddwlee84/agent-skills/blob/main/skills/local/fastapi-ai-patterns/references/security.md)
      —— 密碼雜湊、JWT algorithm pinning、CORS、rate limiting、BOLA (Ch 6)。
    - [`testing.md`](https://github.com/daviddwlee84/agent-skills/blob/main/skills/local/fastapi-ai-patterns/references/testing.md)
      —— `TestClient`、`dependency_overrides`、測試 DB 分層、coverage 誠實度 (Ch 7)。
    - [`async-and-external.md`](https://github.com/daviddwlee84/agent-skills/blob/main/skills/local/fastapi-ai-patterns/references/async-and-external.md)
      —— event loop、retry + circuit breaker、queue、webhook、streaming (Ch 8)。
    - [`ai-ml-serving.md`](https://github.com/daviddwlee84/agent-skills/blob/main/skills/local/fastapi-ai-patterns/references/ai-ml-serving.md)
      —— 模型載入、batching、LLM gateway + SSE、RAG、guardrail、成本 (Ch 9)。
    - [`deployment-observability.md`](https://github.com/daviddwlee84/agent-skills/blob/main/skills/local/fastapi-ai-patterns/references/deployment-observability.md)
      —— worker、probe、observability、caching、graceful degradation (Ch 10)。

## 唯一值得背的表

| 工作型態 | 正確 handler |
|---|---|
| 支援 async 的 I/O (`httpx`、`asyncpg`) | `async def` + `await` |
| 只有阻塞版的 library (`requests`、傳統 ORM) | 純 `def`（threadpool） |
| 輕量 CPU (< 數 ms) | 都可以 |
| 重量 CPU（inference、parsing） | 純 `def`，或 offload |

最致命的 FastAPI bug：`async def` handler 裡面做阻塞呼叫。它能通過每個單請求
測試，然後在高併發下凍結整個 event loop，所有 endpoint 的 p99 同時爆掉。

## 何時使用

建構、審查、或 debug FastAPI 服務時用 —— 尤其是 serving 模型、embedding、RAG、
或 LLM 的服務。要生成整個專案見 [`fastapi-ai-scaffold`](fastapi-ai-scaffold.md)；
要面試刷題見 [`fastapi-ai-interview-prep`](fastapi-ai-interview-prep.md)。

## Cross-references

- FastAPI 文件：[fastapi.tiangolo.com](https://fastapi.tiangolo.com) —— 連結，
  不要從記憶 paraphrase；API 表面在 minor 版間會變。
- Pydantic v2：[docs.pydantic.dev](https://docs.pydantic.dev)。
