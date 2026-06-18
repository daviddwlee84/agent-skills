# Testing FastAPI applications

Read this when writing tests for a FastAPI service. Covers the book's Chapter 7 in
original wording.

## Table of contents

1. [TestClient and dependency overrides](#testclient-and-overrides)
2. [Two-tier test database strategy](#test-database-strategy)
3. [Unit vs integration](#unit-vs-integration)
4. [Testing auth and the authz matrix](#testing-auth)
5. [Time, leaks, and contract assertions](#time-leaks-contracts)
6. [Coverage, honestly](#coverage)
7. [Gotchas](#gotchas)

---

## TestClient and overrides

`TestClient` speaks ASGI directly — it constructs the request in-process and calls
your app as a coroutine, exercising middleware, routing, validation, and handlers
**without a running server or sockets**.

Override dependencies instead of monkeypatching:

```python
app.dependency_overrides[get_db] = lambda: test_session
```

This works at the declared interface — the same seam production wiring uses — so
tests don't depend on import paths or module structure (a `patch("app.x.SessionLocal")`
breaks when someone moves an import; an override doesn't). Overrides are scoped,
discoverable (one dict), and composable (override auth, DB, and an LLM client
independently). Clear them in fixture teardown.

Use `with TestClient(app) as client:` (the context-manager form) whenever the app
relies on `lifespan` startup — model loading, pool creation, `app.state` — because
bare `TestClient(app)` **skips lifespan events** and anything reading `app.state`
will fail or use stale state.

## Test database strategy

Two tiers, route tests to the right one:

- **Tier 1 (default): SQLite in-memory** with a `StaticPool`, created/dropped per
  test. Milliseconds per test, perfect isolation; covers the 80–90% of tests where
  the DB is incidental (business logic, contracts, serialization).
- **Tier 2 (marked, e.g. `-m pg`): real Postgres** via testcontainers/CI service,
  for dialect-sensitive behavior — JSONB operators, `FOR UPDATE` locking, deferred
  constraints, sequences, and **migration replay** (run Alembic, not `create_all`,
  so the migration chain itself is tested).

"Test what you fly" is answered by routing, not by paying Postgres latency on every
assertion. If tier 2 grows past ~20% of the suite, dialect concerns are leaking out
of the repository layer.

## Unit vs integration

- **Unit tests** target the service layer directly with fake repositories — no HTTP,
  no DB. Numerous, sub-millisecond. They cover business rules and edge cases.
- **Integration tests** go through `TestClient` and assert the **contract**:
  routing, 422 shapes, `response_model` filtering, status-code mapping of domain
  exceptions, auth enforcement. Few per endpoint because routers are thin.

The split is downstream of the layered architecture (see `architecture-di.md`):
thin routers make integration tests cheap; logic in services makes unit tests fast.

## Testing auth

Build the **authorization matrix as data**: a parametrized test iterating
`(role × endpoint × ownership)` asserting allowed/denied. This is the artifact you
hand an auditor, and it catches BOLA regressions structurally. For ownership/BOLA
specifically, assert that user A gets 404 (not 403) for user B's object id.

## Time, leaks, contracts

- **Make time injectable.** A `get_now()` dependency (overridden in tests) or
  `freezegun`/`time-machine` makes token-expiry and rate-limit tests deterministic.
  Never `sleep()` in tests — it's slow and flaky.
- **Test that secrets never leak with exact-shape assertions**:
  `assert set(resp.json()) == EXPECTED_KEYS`. This fails on *new* fields too,
  unlike `"password" not in body` which only catches known names. Add a CI check
  that every route declares a `response_model`.
- **Assert on the 422 body, not just the status.** Clients depend on
  `detail[].loc` and `detail[].type`; pin those (not the human-readable `msg`).

## Coverage

Coverage measures execution, not verification — a test that asserts nothing scores
the same as one that pins the whole contract. Use it as a floor (a gate, e.g. 85%)
and a flashlight (find untested error branches), never as a quality target. Prefer
**branch coverage** for API code, where bugs live in `if`/`except` arms. When "95%
covered" code keeps breaking, the cause is weak assertions, happy-path bias, or
untestable-in-CI dimensions (concurrency, real-data shapes, provider drift) —
add mutation testing and a regression test per incident.

## Gotchas

- **Bare `TestClient(app)` skips lifespan** — model/`app.state` setup never runs.
  Use the context-manager form when production depends on startup.
- **Forgetting `dependency_overrides.clear()` leaks state between tests.** Manage
  it in a fixture.
- **Overrides bypass the real dependency**, so its own logic goes untested — cover
  the real dependency separately.
- **A 3% flake rate across a large suite means most runs have a false failure.**
  Engineers learn to distrust red and ship real regressions. Treat flakes as
  incidents: quarantine with an owner, fix by class (shared state, time, ordering,
  real network).
