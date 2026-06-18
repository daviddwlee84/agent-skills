# Chapter 8 — Async, background tasks, and external services

Read this when prepping concurrency, external calls, and deferred work. Questions
are original; topics follow the book.

### Q1. Precisely what happens when an `async def` handler makes a blocking call, and why does it degrade unrelated endpoints?

The handler is a coroutine on the process's single event loop. A blocking call
(`requests.get`, `time.sleep`, heavy CPU) never yields, so for its duration no other
coroutine runs — not other handlers, not keepalive, not health checks — because they
share the loop, which is the monopolized resource. Under concurrency, k blocked
requests serialize and latency becomes k×T for everyone. Fix: make it async, switch
to `def` (threadpool), or offload.

### Q2. Design a retry policy for a flaky upstream. What can naive retries do, and what are the safeguards?

Naive retries amplify load when the upstream is weakest — 3 retries can turn 100%
into 400% during a brownout (retry storm), and synchronized backoff adds thundering
herd. Safeguards: retry only transient errors (timeouts, 502/503/504, conn reset),
never 4xx; only idempotent ops; exponential backoff with full jitter; a retry budget;
a total deadline below your caller's timeout; and a circuit breaker that fails fast and
probes. Honor `Retry-After`.

### Q3. BackgroundTasks vs Celery: decision criteria and the failure modes of choosing wrong.

`BackgroundTasks` runs in-process after the response: zero infra but no persistence,
retries, scheduling, or isolation. Celery (broker-backed) gives durability, retries,
scheduling, and independent scaling. Criteria: tolerable-to-lose + short + light →
BackgroundTasks; must-complete or long/heavy/bursty → queue. Wrong direction 1:
confirmation emails in BackgroundTasks vanish on every deploy. Wrong direction 2:
Celery for a 5ms log write is pure operational overhead.

### Q4. How do you receive webhooks safely (authenticity, replay, ordering, timeout)?

Verify an HMAC signature over the raw body with `hmac.compare_digest` before parsing.
Include a timestamp in the signed payload and reject stale ones; dedupe by event id
(delivery is at-least-once, so handlers must be idempotent). Never assume ordering —
design for out-of-order via versioned upserts/sequence numbers. Senders time out
fast, so validate, persist/enqueue, return 2xx immediately, and process async.

### Q5. When does WebSocket beat SSE/polling, and what operational complexity does it add?

WebSockets win for genuinely bidirectional, low-latency interaction (chat with typing
indicators, collaborative editing). SSE wins for one-way server push (notifications,
LLM token streams) and is plain HTTP, so proxies/auth/reconnect just work. Polling
fits low-frequency checks. WebSocket cost: per-connection server state, LB config for
long-lived connections, deploy draining, a Redis pub/sub backplane for scale-out, and
handshake-time auth. Most "we need WebSockets" needs are SSE-shaped.

### Q6. Why must a shared `httpx.AsyncClient` live in the lifespan handler?

Client construction sets up TLS context and an empty connection pool, so per-request
clients pay TCP+TLS handshakes on every call and leak connections. A lifespan-scoped
client reuses keepalive connections (handshake amortized to ~zero), enforces global
limits, and closes cleanly on shutdown. The same singleton logic applies to DB
engines, model handles, and Redis clients.

### Q7. `StreamingResponse` vs building the full response in memory — and when is streaming mandatory?

A buffered response materializes the whole payload (memory ∝ size; time-to-first-byte
= full generation) then sends. `StreamingResponse` writes chunks from a generator as
produced: constant memory, immediate first byte, connection-driven backpressure.
Mandatory for large exports, when TTFB matters (LLM token streams), or when the source
is itself a stream. Caveat: status/headers commit before generation, so design in-band
error signaling.

### Q8. How do you enforce an upload size limit robustly, and why is `Content-Length` insufficient?

`Content-Length` is a client claim — absent under chunked encoding and trivially
falsified. Enforce in layers: a reverse-proxy cap rejects the bulk cheaply, and the
handler counts bytes while streaming (`await file.read(chunk)` in a loop, abort past
the cap). Also validate content type by sniffing magic bytes, not the client header.

### Q9. Your Celery queue depth is growing without bound. Walk through diagnosis and the levers.

Compare arrival rate λ to service rate (workers × 1/job-time): if λ exceeds capacity,
backlog grows by Little's Law. Check for slow/stuck jobs, poison messages retrying
forever, a downstream dependency throttling workers, and under-provisioned workers.
Levers: add workers (sized by λ·job-time), shed/deprioritize low-value jobs, fix slow
jobs, add a dead-letter queue for poison messages, and autoscale on queue depth.

### Q10. Explain backpressure in an async API. Where does it come from, and why is unbounded concurrency dangerous?

Backpressure is a slower downstream limiting a faster upstream's intake. Async makes
accepting work trivial (cheap coroutines) while downstreams (DB pool, upstream limits,
memory) are finite, so without bounds, bursts become timeouts, pool exhaustion, and
OOM instead of graceful queuing. Bound every buffer: connection pools, semaphores for
fan-out, queue maxsizes, server concurrency limits, and load shedding (429/503 +
`Retry-After`). Every unbounded buffer is a deferred outage.
