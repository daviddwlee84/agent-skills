---
name: fastapi-ai-patterns
description: 'Production patterns and gotchas for building FastAPI services, especially AI/ML/LLM serving. Use when you build, review, or debug a FastAPI app: choosing def vs async def, loading models in lifespan, preventing event-loop blocking, setting response_model to stop data leaks, enforcing object-level authz in queries, wrapping LLMs with streaming + Pydantic validation loops, or designing RAG/embedding endpoints.'
---

# FastAPI AI Patterns

Opinionated, production-calibrated guidance for FastAPI services — with the
focus on what makes **AI/ML/LLM serving** different from an ordinary CRUD API.
It is a knowledge skill: it teaches the decisions and the traps, then routes you
to a per-topic reference for depth.

Stock agents already write basic FastAPI well (routes, Pydantic models, simple
CRUD). This skill spends its tokens on the parts they get **wrong by default**:
the concurrency model, the lifespan/singleton lifecycle, the security boundaries,
and the discipline that turns a stochastic LLM into a typed component.

> Inspired by *FastAPI for AI Engineers: From First Endpoint to Production-Scale
> AI Systems* (AI Engineering Insider, 2026). All content here is re-expressed in
> original wording; consult the book for its worked examples and case studies.

## When to use

- Building a FastAPI service that serves ML models, embeddings, RAG, or wraps an LLM
- Reviewing or debugging a FastAPI app for production-readiness (latency, leaks, auth)
- Deciding `def` vs `async def` for a handler, or diagnosing a "p99 exploded under load" incident
- Designing inference, streaming-chat, embedding, or document-Q&A endpoints
- Hardening an endpoint: response shape, authz, rate limiting, input/output guardrails

## When NOT to use

- You want a full project skeleton generated → use `fastapi-ai-scaffold`
- You are drilling interview questions on these topics → use `fastapi-ai-interview-prep`
- Pure frontend/Next.js work, or a non-FastAPI Python web stack (Flask/Django) → different skills

## Core mental model: the endpoint is a typed contract

A FastAPI endpoint signature **is** the API contract. Parameter annotations
declare what the request must contain; the return annotation or `response_model`
declares what the response will contain. The framework enforces both at runtime
and publishes them as OpenAPI. Everything else — validation, docs, the 422 error
body, SDK generation — is derived from that one declaration.

Two consequences worth internalizing:

1. **The annotation is the single source of truth.** Don't duplicate validation
   logic that a Pydantic field constraint already expresses.
2. **FastAPI is a thin layer over Starlette + Pydantic.** When you debug, you are
   often reading Starlette (routing, middleware, `BackgroundTasks`) or Pydantic
   (validation, coercion) source. Knowing which layer owns a behavior is the
   difference between guessing and fixing.

## The single most important decision: `def` vs `async def`

FastAPI runs `async def` handlers on **one event loop**; it dispatches plain
`def` handlers to a **threadpool** (~40 threads by default). Choose by the
workload, not by habit:

| Workload | Correct handler | Why |
|---|---|---|
| Async-capable I/O (`httpx`, `asyncpg`, async redis) | `async def` + `await` | Loop interleaves thousands of in-flight waits |
| Blocking-only library (`requests`, classic ORM, `boto3`) | plain `def` | Threadpool absorbs the block; loop stays free |
| Light CPU (< a few ms) | either | Negligible either way |
| Heavy CPU (model inference, parsing, crypto) | plain `def`, or offload (`to_thread`/process pool/queue) | Never run multi-ms CPU on the loop |

The deadliest FastAPI production bug: an `async def` handler that makes a
**blocking** call inside it (`requests.get`, `time.sleep`, a sync model
`.predict()`, a CPU-heavy parse). It passes every single-request test, then under
concurrency it freezes the entire loop — and p99 explodes for **every** endpoint
at once, including `/health`. See `references/async-and-external.md`.

## Top gotchas (read before you write the handler)

These are the corrections an agent most often needs. They are environment facts
that defy reasonable assumptions, so they live here, not in a reference.

- **`async def` + blocking call = whole-process stall.** One non-cooperating
  coroutine starves every other request on the loop. If a call isn't truly
  async, use plain `def` or offload it. Detect with a loop-lag watchdog.
- **Load ML models once, in the `lifespan` handler — never per request, never at
  import time.** Per-request loading re-reads weights on every call (and OOMs
  under concurrency); import-time loading makes tests, linters, and CLI tools pay
  the cost (or crash without a GPU). Lifespan loading runs once per worker before
  traffic and integrates with readiness probes. With N workers you hold N copies
  — size worker count by memory, or front a dedicated inference server.
- **Every response needs a `response_model` (or explicit return type).** Returning
  an ORM object directly serializes *all* its columns — that is how
  `hashed_password` ends up in a JSON response. Separate request / storage /
  response schemas; the response schema is a structural leak-prevention boundary.
- **Object-level authorization must be enforced in the query, not by review.**
  BOLA (broken object-level authorization) tops the OWASP API list because
  `GET /orders/{id}` that trusts the path id leaks other users' data. Filter by
  owner in the data layer (`WHERE owner_id = current_user.id`), so an unauthorized
  fetch returns 404 by construction — don't rely on a reviewer remembering.
- **Echo `model_version` (and embedding model version) in every AI response.**
  When quality regresses the first question is "which model produced this?", and
  canary rollouts serve multiple versions at once. Vectors from different
  embedding models are incomparable — a model upgrade means re-embedding the corpus.
- **Treat LLM output as untrusted input: generate → validate with Pydantic →
  retry with the error appended → fall back.** This loop is the single most
  useful LLM-engineering pattern: it converts a stochastic text generator into a
  typed component with an explicit failure mode. One retry fixes most cases;
  on the second failure raise a typed error to a defined fallback (human review,
  cheaper deterministic path, or 502) — never pass malformed data downstream.
- **In RAG, enforce access control in retrieval (SQL/filter), never in the
  prompt.** Never let the model see chunks the user can't access and "ask it" to
  respect permissions — prompt injection defeats that. The authorization boundary
  lives outside the model.
- **Per-process singletons (`httpx.AsyncClient`, DB engine, Redis client, model
  handle) belong in `lifespan`, injected via a dependency — not constructed per
  request.** A per-request `httpx` client pays TCP+TLS handshakes every call and
  leaks connections; a lifespan-scoped client reuses keepalive connections and
  enforces global limits.
- **Wrap streaming generators in `try/finally`.** Clients disconnect mid-stream
  constantly; token metering, logging, and upstream stream cancellation must run
  even then, or you keep paying for abandoned generations and lose usage data.
- **Keep `/health` trivially cheap; use a separate `/ready` for dependency
  readiness.** A health check that does real work (or shares the event loop with
  heavy handlers) will fail under load and trigger restart storms. Liveness and
  readiness are different questions and need different probes.
- **Retry only idempotent operations on transient errors, with backoff + jitter
  and a total deadline below your caller's timeout.** Naive retries amplify load
  exactly when an upstream is weakest (retry storm); synchronized retries are a
  self-inflicted thundering herd. Add a circuit breaker for repeated failure.
- **Validate JWTs with a pinned algorithm; hash passwords with bcrypt/argon2, not
  SHA-256.** Accepting the token's own `alg` header enables the `alg=none` forgery;
  fast hashes make password cracking cheap. See `references/security.md`.

## How to use the references

Load the one reference that matches the decision in front of you — don't preload
them all. Each is self-contained with patterns, gotchas, and capacity/cost rules
restated in original wording.

- **`references/api-design.md`** — Read when designing routes, status codes,
  pagination/versioning, or Pydantic v2 request/response schemas (Ch 1–3 scope:
  ASGI vs WSGI, REST semantics, idempotency, validation, leak prevention).
- **`references/architecture-di.md`** — Read when structuring a project or wiring
  `Depends()` (Ch 4: DI resolution + caching, `yield` deps for DB sessions,
  router/service/repository layering, composition root, `dependency_overrides`).
- **`references/database.md`** — Read when adding persistence (Ch 5: session-per-
  request, N+1 + `selectinload`/`joinedload`, SQLModel vs SQLAlchemy+Pydantic,
  Alembic, pool sizing, PgBouncer, `flush` vs `commit`).
- **`references/security.md`** — Read when adding auth or hardening (Ch 6: password
  hashing, JWT + revocation, API keys, CORS, rate limiting, OWASP API risks, BOLA).
- **`references/testing.md`** — Read when writing tests (Ch 7: `TestClient`,
  `dependency_overrides`, SQLite-in-memory tiers, authz matrix, time injection,
  coverage honesty, 422-body assertions).
- **`references/async-and-external.md`** — Read when doing concurrency or external
  calls (Ch 8: event loop model, the full `def`/`async` table, `httpx` client +
  retries + circuit breaker, `BackgroundTasks` vs Celery, webhooks, uploads,
  streaming, WebSockets, backpressure).
- **`references/ai-ml-serving.md`** — Read when serving models or LLMs (Ch 9:
  model loading, batch + dynamic micro-batching, LLM gateway + SSE streaming,
  embeddings + vector DB + RAG, guardrails, validation loop, versioning/monitoring/
  HITL, LLM cost model).
- **`references/deployment-observability.md`** — Read when deploying or operating
  (Ch 10: Uvicorn/Gunicorn workers, Docker, K8s probes, logs/metrics/traces,
  caching + stampede, load testing, graceful degradation, production checklist).

## Authoritative sources (link, don't paraphrase from memory)

FastAPI's API surface and the surrounding ecosystem change between minor
versions. When unsure of exact syntax or current behavior, fetch the docs:

- FastAPI: <https://fastapi.tiangolo.com>
- Pydantic v2: <https://docs.pydantic.dev>
- Starlette: <https://www.starlette.io>
- SQLModel: <https://sqlmodel.tiangolo.com>
- httpx: <https://www.python-httpx.org>

## Gotchas

The top, cross-cutting gotchas are in the section above (they apply before you
even pick a topic). Topic-specific traps live in each reference's own `## Gotchas`
section — for example, `flush()` vs `commit()` timing in `database.md`, the
`alg=none` attack in `security.md`, and SSE proxy-buffering in
`ai-ml-serving.md`. Load the reference for the area you're working in so you read
its gotchas **before** hitting the situation, not after.
