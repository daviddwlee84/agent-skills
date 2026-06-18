# Deployment, scaling, and observability

Read this when deploying or operating a FastAPI service. Covers the book's Chapter
10 in original wording.

## Table of contents

1. [Servers and workers](#servers-and-workers)
2. [Dockerizing](#dockerizing)
3. [Liveness vs readiness probes](#probes)
4. [Observability: logs, metrics, traces](#observability)
5. [Caching and the stampede](#caching)
6. [Load testing](#load-testing)
7. [Graceful degradation](#graceful-degradation)
8. [Production checklist](#production-checklist)
9. [Gotchas](#gotchas)

---

## Servers and workers

Uvicorn is the ASGI server; for multiple worker processes you either run Uvicorn
with `--workers`, run Gunicorn with the Uvicorn worker class, or run one process
per pod and scale pods (often cleanest on Kubernetes, where the orchestrator owns
process supervision).

Worker-count rule of thumb:

- **CPU-bound** (in-process inference): worker count ≈ core count; scale pods
  horizontally on CPU utilization.
- **I/O-bound** (LLM/DB calls): a few async workers per node sustain high
  concurrency; scale on latency/queue depth, not CPU.

Remember each worker holds its own copy of any in-memory model — N workers = N
copies of the weights. Size by memory.

## Dockerizing

- Multi-stage build: install deps in a builder, copy only what's needed into a slim
  runtime image. Pin the Python base image.
- Run as a non-root user; set `PYTHONUNBUFFERED=1` so logs flush.
- One concern per image; pass config via environment variables (12-factor), never
  bake secrets into the image.
- Add a container `HEALTHCHECK` hitting your liveness endpoint.

## Probes

Liveness and readiness answer **different questions** and need different
implementations:

| Probe | Question | Fails → | Implementation |
|---|---|---|---|
| Liveness | Is the process wedged? | Restart the pod | Trivially cheap, no dependencies |
| Readiness | Can it serve traffic now? | Remove from the LB pool | Checks deps (DB, model warm, upstreams) |

Conflating them is dangerous: if the liveness check verifies the database and the
DB blips, Kubernetes **restarts** healthy pods (worsening the outage) instead of
just taking them out of rotation. Keep `/health` (liveness) cheap; put dependency
checks in `/ready` (readiness). A model server should report ready only after the
model is warm, so rolling deploys don't send traffic to a cold pod.

## Observability

The three pillars, and what each answers:

- **Logs** — structured (JSON), with a request/correlation id, route, status,
  latency, and user/tenant id. **Never** log secrets, tokens, passwords, full
  payloads, or PII.
- **Metrics** — request rate, error rate, latency histograms (p50/p95/p99), plus
  AI-specific ones (TTFT, tokens/sec, cost). Drive SLO-based alerts.
- **Traces** — distributed spans across services to find where latency accrues.

Diagnostic pattern: when **p99 tripled but p50 is unchanged**, the median path is
fine and a subset is slow — look at tail-affecting causes (a slow dependency for
some keys, pool contention, GC pauses, an N+1 for certain inputs, a blocked event
loop under specific load) using traces and per-route latency, not averages.

Alert on **SLOs/symptoms** (error budget burn, latency SLO breach), not on causes
like "CPU > 80%" — high CPU may be perfectly healthy, and paging on it creates
alarm fatigue while missing real user-facing failures.

## Caching

Cache-aside with a TTL is the default, but two hard parts:

- **Stampede / thundering herd:** when a hot key expires, many concurrent requests
  all miss and recompute at once. Mitigate with a lock/single-flight (one request
  recomputes, others wait), early/probabilistic refresh, or serving slightly stale
  data while one worker refreshes.
- **Invalidation is harder than caching.** Prefer short TTLs plus event-driven
  invalidation on writes; be explicit about staleness tolerance per cache.

For LLMs, response caching for repeated queries is the highest-ROI cost lever (see
`ai-ml-serving.md`).

## Load testing

Test the realistic path, not a trivial one. Naive load tests get it wrong by
hitting a single cached endpoint, ignoring think-time and payload-size
distribution, and reusing one auth token. For a RAG/LLM service specifically:
exercise realistic query diversity (so caches behave realistically), include the
full retrieval+generation path, and measure TTFT and tail latency under
concurrency, not just average throughput.

## Graceful degradation

When a hard dependency (e.g. your primary LLM provider) fails, degrade instead of
falling over: fail over to a secondary provider/model, serve cached or lower-quality
results, queue work for later, or return an honest "temporarily unavailable" with a
fallback action — never a confidently wrong answer. Decide these fallbacks before
the outage, and rehearse them.

## Production checklist

Before going live:

- [ ] `response_model` (or typed return) on every route; no field leaks
- [ ] Auth on every non-public route; object-level authz enforced in queries
- [ ] Input size/token caps and rate limiting
- [ ] Models loaded in `lifespan`; `/health` cheap, `/ready` checks deps
- [ ] Timeouts + bounded retries + circuit breakers on every upstream call
- [ ] Structured logs without secrets; metrics + SLO alerts; tracing
- [ ] Migrations tested in CI and run as a deploy step (zero-downtime where needed)
- [ ] Graceful degradation paths for critical dependencies
- [ ] Load tested on the realistic path; concurrency limits set

## Gotchas

- **Liveness that checks dependencies causes restart storms** when a dep blips —
  keep liveness dependency-free; check deps in readiness.
- **Paging on CPU/memory thresholds instead of SLOs** creates alarm fatigue and
  misses real failures. Alert on symptoms users feel.
- **Averages hide tail problems** — a tripled p99 with flat p50 is a subset issue;
  use percentiles and traces.
- **TTL caches stampede on hot-key expiry** — add single-flight/locking for hot keys.
- **OOM-killed-every-few-hours under steady traffic** usually means a slow leak or
  unbounded buffer/cache (or N model copies exceeding memory) — check growth over
  time, not a single snapshot.
- **Secrets in logs** are a breach waiting to be discovered — scrub structured logs
  and never log full request bodies.
