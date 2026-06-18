# Chapter 7 — Testing FastAPI applications

Read this when prepping testing strategy. Questions are original; topics follow the
book.

### Q1. How do FastAPI dependency overrides work, and why are they superior to monkeypatching?

`app.dependency_overrides` maps a dependency callable to a replacement, checked during
resolution, so one line redirects every endpoint's DB session (or auth, or LLM
client). It operates at the declared interface — the seam production uses — so tests
don't break when imports move, it's scoped and discoverable (one dict, cleared in
teardown), and it composes across multiple dependencies. Monkeypatching couples tests
to module paths.

### Q2. Design a test-database strategy for a Postgres-in-prod team. Defend SQLite-in-memory against "test what you fly."

Two tiers: default SQLite in-memory (milliseconds, perfect isolation) for the 80–90%
of tests where the DB is incidental, and a marked Postgres tier for dialect-sensitive
behavior (JSONB, `FOR UPDATE`, deferred constraints, migration replay). "Test what you
fly" is satisfied by routing the dialect-dependent tests to Postgres, not by paying
its latency on every assertion. If the Postgres tier exceeds ~20%, dialect concerns
are leaking out of the repository.

### Q3. What belongs in a unit test vs an integration test for a FastAPI endpoint, and how does layering decide?

Unit tests hit the service layer with fake repositories — business rules, edge cases,
no HTTP/DB, numerous and fast. Integration tests go through `TestClient` and assert
the contract — routing, 422 shapes, `response_model` filtering, status mapping, auth.
Thin routers (layered architecture) make integration tests few and cheap; logic in
services makes unit tests reach the edge cases.

### Q4. How would you test that an endpoint never leaks sensitive fields, in a way that survives refactors?

Assert the exact key set: `set(resp.json()) == EXPECTED` so new fields fail too
(unlike `"password" not in body`). Derive the expected set from the public schema so
intentional changes update it deliberately. Add a CI gate that every route declares a
`response_model`, and optionally a staging canary scanning responses for secret-like
keys.

### Q5. Your CI suite has a 3% flake rate across 2,000 tests. Quantify the damage and remediate.

At suite scale a 3% per-test flake rate means most runs contain a false failure, so
engineers retry (doubling CI cost/latency) and learn to distrust red — which is how
real regressions ship (alarm fatigue). Remediate: measure rerun-to-green to name
flaky tests; quarantine them in a non-blocking job with an owner and a deadline (never
delete silently); fix by class (shared state, time, ordering, real network, async
races); gate new tests by running them many times before they join. Track flake rate
as an SLO.

### Q6. Why does `TestClient` not require a running server, and what are its limits?

It speaks ASGI directly — constructs the request and calls the app as a coroutine
in-process, exercising middleware, routing, validation, and handlers without sockets.
It doesn't test the ASGI server config, TLS, reverse-proxy behavior, HTTP/2, real
network latency, or cross-process concerns (pool sizing across workers). Those belong
to a thin staging smoke layer.

### Q7. How do you test code that depends on the current time (token expiry, rate limits)?

Make time injectable — a `get_now()` dependency overridden in tests, or
`freezegun`/`time-machine` to freeze the clock — so you issue a token, advance past
the TTL, and assert 401 deterministically. Never `sleep()`; it's slow and flaky. For
JWT libraries that check real time, freeze it for the verification or mint tokens with
already-past expiry.

### Q8. What does `with TestClient(app) as client` do that bare `TestClient(app)` does not?

The context-manager form runs the app's `lifespan` events — startup (model loading,
pool creation, `app.state` init) before requests and shutdown on exit. Bare
construction skips them, so anything reading `app.state` or startup-initialized
resources fails or uses stale state. Use the context form whenever production behavior
depends on lifespan.

### Q9. Why is asserting on the 422 body (not just the status) worth the brittleness?

The error body is part of the public contract: clients parse `detail[].loc` and
`detail[].type` to map errors to fields and localize. A Pydantic upgrade or a custom
handler can change the structure while status-only tests stay green, silently breaking
consumers. Pin the parts clients rely on (`loc`, `type`), not the human-readable
message.

### Q10. Coverage is 95% but production incidents keep coming from "tested" code. Diagnose.

Coverage measures execution, not assertion strength. Likely causes: weak assertions
(status only, no body), happy-path bias (the uncovered 5% is the error handling where
incidents live — check branch coverage), untestable-in-CI dimensions (concurrency,
pool exhaustion, real-data shapes, provider drift), and assertion rot after refactors.
Remedies: mutation testing, a regression test per incident, branch-coverage gates on
error handlers, and contract tests against recorded real payloads.
