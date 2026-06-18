# Chapter 10 — Deployment, scaling, and observability

Read this when prepping production operations. Questions are original; topics follow
the book.

### Q1. Liveness vs readiness probes: different questions, different implementations, and the danger of conflating them.

Liveness asks "is the process wedged?" — failure means restart the pod; it must be
trivially cheap and dependency-free. Readiness asks "can it serve traffic now?" —
failure means remove from the load-balancer pool; it checks the DB, model warmth, and
upstreams. Conflating them is dangerous: if liveness checks the database and the DB
blips, the orchestrator restarts healthy pods (deepening the outage) instead of just
pulling them from rotation.

### Q2. Walk through a zero-downtime deploy that includes a schema migration, including in-flight requests.

Use backward-compatible, expand-then-contract migrations: deploy schema changes that
the old code still tolerates (add nullable column, backfill, dual-write) before code
that depends on them, and split renames/drops across releases. Roll out with surge +
connection draining: new pods must pass readiness before old pods are removed, and old
pods finish in-flight requests during a graceful shutdown window (longer than your
slowest request, e.g. LLM streams). Keep rollback ready (previous image + reversible
migrations).

### Q3. p99 latency tripled but p50 is unchanged. Diagnose using the three pillars.

A flat median with a heavy tail means a subset of requests is slow, not everything.
Metrics: confirm with percentile histograms and segment by route/tenant/instance to
localize. Traces: sample slow requests to see where time accrues (a dependency for
some keys, pool checkout waits, GC pauses, a per-input N+1, or a blocked event loop
under specific load). Logs: correlate the slow trace ids for inputs/errors. Averages
would have hidden this — always reason in percentiles.

### Q4. Explain cache-aside with TTL, the stampede problem, and why invalidation is the hard part.

Cache-aside: on miss, compute, store with a TTL, serve. The stampede (thundering herd)
happens when a hot key expires and many concurrent requests all miss and recompute at
once, hammering the backend. Mitigate with single-flight/locking (one recomputes,
others wait), early/probabilistic refresh, or serving stale while one refreshes.
Invalidation is hard because correctness depends on knowing when source data changed —
prefer short TTLs plus event-driven invalidation on writes, with explicit per-cache
staleness tolerance.

### Q5. How do you load-test a RAG/LLM service meaningfully, and what do naive load tests get wrong?

Naive tests hammer one cached query, ignore think-time and payload-size distribution,
and reuse one auth token — so caches, retrieval, and rate limits behave nothing like
production. Do better: realistic query diversity (so cache hit rates are real), the
full retrieval+generation path, representative concurrency and arrival patterns, and
measure TTFT and tail latency under load (not just average throughput). Test against
staging with production-shaped data and watch downstream cost.

### Q6. Compare Gunicorn+Uvicorn workers, `uvicorn --workers`, and one-process-per-pod.

All achieve multi-process parallelism. Gunicorn with the Uvicorn worker class adds
mature process supervision (graceful restarts, `max_requests` recycling).
`uvicorn --workers` is simpler with fewer knobs. One-process-per-pod delegates
supervision/scaling to Kubernetes (often cleanest there: scale pods, not in-pod
workers). Whichever you pick, remember each worker holds its own in-memory model copy,
so worker count is bounded by memory.

### Q7. What belongs in structured logs, and what must never?

Include: a request/correlation id, route, method, status, latency, user/tenant id, and
domain events — as JSON, one object per line, for aggregation. Never log secrets,
tokens, passwords, full request/response bodies, PII, raw prompts/completions with
sensitive content, or full stack traces containing data. Scrub at the logging boundary;
a secret in logs is a breach waiting to be found.

### Q8. Argue for SLO/symptom-based alerting and against alerting on "CPU > 80%."

Alert on what users feel — error-budget burn, latency SLO breach, elevated 5xx —
because those map to actual harm and are actionable. "CPU > 80%" is a cause that's
often perfectly healthy (efficient utilization) or irrelevant (an I/O-bound service
can be slow at 20% CPU), so it pages on non-problems (alarm fatigue) while missing real
user-facing failures. Keep resource metrics for diagnosis dashboards, not pages.

### Q9. Your primary LLM provider has an outage. How does the service degrade gracefully instead of failing?

Decide fallbacks before the outage and rehearse them: fail over to a secondary
provider/model behind your gateway abstraction; serve cached responses for repeated
queries; fall back to a cheaper/local model or a deterministic path; queue
non-interactive work for later; or return an honest "temporarily unavailable" with a
fallback action. Never emit a confidently wrong answer. A circuit breaker prevents
hammering the dead provider and enables fast failover.

### Q10. Pods are OOM-killed every few hours under steady traffic. Walk through the investigation.

Steady traffic + periodic OOM signals growth over time, not a per-request spike. Plot
memory across the cycle: linear growth → a leak (unbounded cache/buffer, accumulating
references, a growing in-process queue, or per-request objects that aren't released);
step growth → an unbounded cache or N model copies exceeding limits. Investigate with
`tracemalloc`/heap snapshots at intervals, audit caches for max sizes and TTLs, bound
every buffer, right-size or cap model memory, and set `max_requests` worker recycling
as a stopgap while you fix the root cause.
