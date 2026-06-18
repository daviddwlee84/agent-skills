# fastapi-ai-patterns

Production patterns and gotchas for FastAPI services, with the focus on what makes
**AI/ML/LLM serving** different from ordinary CRUD. It's a knowledge skill: the
`SKILL.md` body carries the cross-cutting decisions and traps an agent gets wrong
by default, then routes to one of eight per-topic references for depth.

> Inspired by *FastAPI for AI Engineers: From First Endpoint to Production-Scale AI
> Systems* (AI Engineering Insider, 2026). All content is re-expressed in original
> wording — ideas and facts, not the book's prose or code listings.

## What ships

- The full SKILL.md
  ([skills/local/fastapi-ai-patterns/SKILL.md](https://github.com/daviddwlee84/agent-skills/blob/main/skills/local/fastapi-ai-patterns/SKILL.md))
  with the `endpoint = typed contract` mental model, the **`def` vs `async def`
  decision table**, and the highest-value gotchas (blocking the event loop, model
  loading in `lifespan`, `response_model` leak prevention, BOLA in the query, the
  LLM generate→validate→retry loop) up front.
- Eight references covering all 10 chapters of the book — read on demand:
    - [`api-design.md`](https://github.com/daviddwlee84/agent-skills/blob/main/skills/local/fastapi-ai-patterns/references/api-design.md)
      — ASGI vs WSGI, REST/idempotency, status codes, pagination, Pydantic v2 (Ch 1–3).
    - [`architecture-di.md`](https://github.com/daviddwlee84/agent-skills/blob/main/skills/local/fastapi-ai-patterns/references/architecture-di.md)
      — `Depends()` resolution + caching, `yield` deps, layering (Ch 4).
    - [`database.md`](https://github.com/daviddwlee84/agent-skills/blob/main/skills/local/fastapi-ai-patterns/references/database.md)
      — sessions, N+1, SQLModel vs SQLAlchemy, Alembic, pool sizing (Ch 5).
    - [`security.md`](https://github.com/daviddwlee84/agent-skills/blob/main/skills/local/fastapi-ai-patterns/references/security.md)
      — password hashing, JWT pinning, CORS, rate limiting, BOLA (Ch 6).
    - [`testing.md`](https://github.com/daviddwlee84/agent-skills/blob/main/skills/local/fastapi-ai-patterns/references/testing.md)
      — `TestClient`, `dependency_overrides`, test DB tiers, coverage honesty (Ch 7).
    - [`async-and-external.md`](https://github.com/daviddwlee84/agent-skills/blob/main/skills/local/fastapi-ai-patterns/references/async-and-external.md)
      — event loop, retries + circuit breakers, queues, webhooks, streaming (Ch 8).
    - [`ai-ml-serving.md`](https://github.com/daviddwlee84/agent-skills/blob/main/skills/local/fastapi-ai-patterns/references/ai-ml-serving.md)
      — model loading, batching, LLM gateway + SSE, RAG, guardrails, cost (Ch 9).
    - [`deployment-observability.md`](https://github.com/daviddwlee84/agent-skills/blob/main/skills/local/fastapi-ai-patterns/references/deployment-observability.md)
      — workers, probes, observability, caching, degradation (Ch 10).

## The one table worth memorizing

| Workload | Correct handler |
|---|---|
| Async-capable I/O (`httpx`, `asyncpg`) | `async def` + `await` |
| Blocking-only library (`requests`, classic ORM) | plain `def` (threadpool) |
| Light CPU (< a few ms) | either |
| Heavy CPU (inference, parsing) | plain `def`, or offload |

The deadliest FastAPI bug is an `async def` handler that makes a blocking call: it
passes every single-request test, then freezes the whole event loop under load and
p99 explodes for every endpoint at once.

## When to use it

Reach for this skill when building, reviewing, or debugging a FastAPI service —
especially one serving models, embeddings, RAG, or an LLM. For generating a whole
project see [`fastapi-ai-scaffold`](fastapi-ai-scaffold.md); for interview drills
see [`fastapi-ai-interview-prep`](fastapi-ai-interview-prep.md).

## Cross-references

- FastAPI docs: [fastapi.tiangolo.com](https://fastapi.tiangolo.com) — link, don't
  paraphrase from memory; the API surface changes between minor versions.
- Pydantic v2: [docs.pydantic.dev](https://docs.pydantic.dev).
