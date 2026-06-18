# Async, background tasks, and external services

Read this when writing concurrent code, calling external APIs, deferring work, or
streaming. Covers the book's Chapter 8 in original wording. This is the chapter
behind the most common FastAPI production incident.

## Table of contents

1. [The event loop in one paragraph](#the-event-loop)
2. [def vs async def — the decision table](#def-vs-async-def)
3. [Calling external APIs with httpx](#httpx)
4. [Retries and circuit breakers](#retries-and-circuit-breakers)
5. [BackgroundTasks vs a real queue](#backgroundtasks-vs-queue)
6. [Webhooks, uploads, streaming, WebSockets](#webhooks-uploads-streaming)
7. [Backpressure](#backpressure)
8. [Gotchas](#gotchas)

---

## The event loop

An asyncio program runs one loop on one thread. A coroutine (`async def`) runs
until it `await`s something not ready, then yields control so the loop runs another
coroutine. Result: thousands of concurrent I/O waits on one thread, no locks, no
thread-switch overhead. The contract has exactly one clause: **never block the
loop.** A single `time.sleep(5)`, `requests.get(...)`, or heavy CPU computation
inside a coroutine freezes *every* request in the process for its duration.

## def vs async def

The most important table in FastAPI work:

| Workload | Correct form |
|---|---|
| Async-capable I/O (`httpx`, `asyncpg`, async redis) | `async def` + `await` |
| Blocking-only library (`requests`, classic ORM, `boto3`) | plain `def` (runs in threadpool) |
| Light CPU (< a few ms) | either |
| Heavy CPU (inference, parsing, crypto) | plain `def`, or offload (`anyio.to_thread`, process pool, worker queue) |

`async def` handlers run on the loop and must `await` only non-blocking calls;
plain `def` handlers are dispatched to a threadpool (~40 threads) where blocking is
safe, at thread cost.

**The deadliest bug:** `async def` handler → blocking call inside. It passes tests
(single requests look fine), then under load p99 explodes for *all* endpoints at
once because the one loop is monopolized. Detect with a **loop-lag monitor**: a
watchdog coroutine that sleeps 100ms and alerts when actual wake-up drifts. Fixes,
in order of correctness: make the call truly async; switch the handler to `def`
(threadpool); offload heavy CPU to a queue.

## httpx

External calls dominate modern API latency. Three non-negotiables:

1. **A shared client** (connection pooling) created in `lifespan`, not per request.
2. **Explicit timeouts** — the default "wait forever" is an outage waiting to happen.
3. **Bounded retries with jitter**, only on idempotent operations.

```python
@asynccontextmanager
async def lifespan(app):
    app.state.http = httpx.AsyncClient(
        timeout=httpx.Timeout(connect=2.0, read=5.0, write=5.0, pool=2.0),
        limits=httpx.Limits(max_connections=100, max_keepalive_connections=20),
    )
    yield
    await app.state.http.aclose()
```

A per-request client pays TCP+TLS handshakes (1–3 RTTs) on every call and leaks
connections; the lifespan-scoped client amortizes handshakes to near-zero and
enforces global concurrency limits. The same per-process-singleton logic applies to
DB engines, Redis clients, and model handles.

## Retries and circuit breakers

Naive retries amplify load exactly when an upstream is least able to absorb it:
3 retries can turn 100% load into 400% during a brownout, converting a slow service
into a dead one. Discipline:

- Retry only **transient** classes: connect/read timeouts, 502/503/504, connection
  reset. **Never** retry 4xx.
- Retry only **idempotent** operations (or idempotency-keyed POSTs).
- **Exponential backoff with full jitter** (`sleep(uniform(0, base * 2**attempt))`)
  — synchronized retries across workers are a self-inflicted thundering herd.
- **Total deadline below your caller's timeout**, so retries don't outlive the
  request.
- A **circuit breaker** fails fast after a failure threshold and probes
  periodically, so you stop hammering a dead dependency. Honor `Retry-After`.

## BackgroundTasks vs queue

| | `BackgroundTasks` | Celery / RQ / arq / Dramatiq |
|---|---|---|
| Runs | In-process, after the response | Separate worker processes |
| Durability | None (lost on crash/deploy) | Durable (broker-backed) |
| Retries/scheduling | No | Yes |
| Use for | Fire-and-forget, tolerable to lose (audit log, cache warm) | Must-complete, long, heavy, or bursty work |

The rule: **if losing the task on a pod restart is a bug, it does not belong in
`BackgroundTasks`.** The durable pattern: API enqueues a job, returns `202 Accepted`
+ a job id, workers process independently, client polls `GET /jobs/{id}` or gets a
webhook. This is also the backbone of batch inference (see `ai-ml-serving.md`).
Choosing wrong is silent: order-confirmation emails in `BackgroundTasks` vanish on
every deploy. (Middle ground: arq/RQ for lighter-weight durable queues; the
transactional-outbox pattern when the enqueue must be atomic with a DB commit.)

## Webhooks, uploads, streaming

- **Receiving webhooks:** verify the HMAC signature over the **raw** body with
  `hmac.compare_digest` *before* parsing; include a timestamp in the signed payload
  and reject stale ones (replay defense); dedupe by event id (delivery is
  at-least-once, so handlers must be idempotent); never assume ordering; return 2xx
  immediately and process via queue (senders time out fast).
- **Uploads:** `UploadFile` streams to a spooled temp file; copy in chunks to object
  storage (S3/GCS), never to pod-local disk. Cap size at the proxy *and* in the
  handler by counting bytes while streaming — `Content-Length` is a client claim,
  absent under chunked encoding and trivially falsified. Validate content type by
  sniffing magic bytes, not the client's header.
- **Streaming:** `StreamingResponse` wraps an (async) generator and writes chunks as
  produced — constant memory, immediate first byte. Mandatory when payloads exceed
  sane memory, when time-to-first-byte matters (LLM token streams), or when the
  source is itself a stream. Caveat: status and headers commit before generation, so
  a mid-stream error can't become a clean 500 — design in-band error signaling.
- **WebSockets:** `accept()` then loop on receive/send — a long-lived bidirectional
  channel. Authenticate at the handshake, expect `WebSocketDisconnect`, and remember
  each connection is held state: LBs need long idle timeouts, deploys must drain
  connections, and horizontal scale needs a Redis pub/sub backplane. Choose the
  weakest primitive that works — most "we need WebSockets" requirements are
  SSE-shaped (one-way push).

## Backpressure

Async makes it trivial to *accept* unbounded work (every request is a cheap
coroutine) while downstreams (DB pool, upstream limits, memory) are finite. Without
limits, bursts become timeouts, pool exhaustion, and OOM kills instead of graceful
queuing. Bound every buffer: bounded pools naturally queue waiters,
`asyncio.Semaphore` caps in-flight fan-out, queue `maxsize` makes producers wait,
`uvicorn --limit-concurrency` and gateway rate limits cap intake, and load shedding
(fast 429/503 + `Retry-After`) protects latency for admitted requests. **Every
unbounded buffer is a deferred outage.**

## Gotchas

- **`async def` + any blocking call freezes the whole process**, degrading endpoints
  that share nothing with it (including `/health`). The #1 FastAPI prod incident.
- **A per-request `httpx.AsyncClient` defeats connection pooling** and leaks
  connections — construct once in `lifespan`.
- **Retrying non-idempotent POSTs duplicates side effects** (double charges, double
  emails). Retry only idempotent or idempotency-keyed operations.
- **Streaming responses can't retroactively set an error status** — once bytes flow,
  the status is committed. Signal errors in-band.
- **`Content-Length` is not a trustworthy size limit.** Enforce by counting bytes
  while reading, plus a proxy cap.
- **Health checks must not share the event loop with heavy work** — a blocked loop
  makes `/health` time out and triggers restart storms.
