# Architecture and dependency injection

Read this when structuring a FastAPI project beyond a single file, or when wiring
`Depends()`. Covers the book's Chapter 4 in original wording.

## Table of contents

1. [How Depends resolves](#how-depends-resolves)
2. [yield dependencies and resource lifecycle](#yield-dependencies)
3. [Router / service / repository layering](#layering)
4. [Composition root](#composition-root)
5. [Where dependencies attach](#where-dependencies-attach)
6. [Gotchas](#gotchas)

---

## How Depends resolves

`Depends(callable)` tells FastAPI to call `callable` to produce a value before the
handler runs, recursively resolving the callable's own dependencies first. Within
a **single request**, FastAPI **caches** each dependency by its callable: if five
dependencies all `Depends(get_settings)`, `get_settings` runs once and the result
is shared. Caching is per-request, not per-process — so an expensive but
request-stable dependency still runs once per request unless you make it a
process-level singleton (e.g. `@lru_cache` on `get_settings`, or store it on
`app.state` in `lifespan`).

This is the mechanism that makes DI in FastAPI cheap: declare what a handler needs
as parameters, and the framework assembles them.

## yield dependencies

A dependency that `yield`s runs setup before the handler and teardown after — the
correct pattern for **per-request database sessions**:

```python
def get_db():
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()
```

The `finally` runs even if the handler raises, so the session is always closed and
(with the right pattern) the transaction rolled back on an unhandled exception. A
plain (non-yield) dependency can't clean up after the response. This is why
session-per-request is built on a yield dependency.

## Layering

For anything beyond a toy app, separate three responsibilities:

- **Router (handler)** — HTTP concerns only: parse/validate input (Pydantic),
  call a service, map domain results/exceptions to status codes. Thin.
- **Service** — business logic: rules, orchestration, domain exceptions. Knows
  nothing about HTTP (no `Request`, no `HTTPException`) so it's unit-testable
  without a client.
- **Repository** — data access: encapsulates the ORM/queries behind an interface
  the service calls. Lets you test the service with a fake repository and swap the
  store later.

The payoff is the test pyramid (see `testing.md`): thin routers mean integration
tests only cover translation; logic lives where fast unit tests reach it.

Skip the repository layer for genuinely trivial CRUD where the indirection buys
nothing — but introduce it the moment a query is reused or business logic starts
leaking into handlers.

## Composition root

Centralize the wiring — which concrete implementation satisfies each dependency —
in one place (a `dependencies.py` / providers module) rather than constructing
services inline inside every handler. Constructing inline couples every handler to
concrete classes, duplicates setup, and makes swapping implementations (or
overriding them in tests) a find-and-replace across the codebase. A composition
root makes `dependency_overrides` (see below) a one-line change.

## Where dependencies attach

The same dependency can attach at three scopes — pick by blast radius:

| Scope | Use for |
|---|---|
| Handler-level (`Depends` in the signature) | Per-endpoint needs (current user, DB session) |
| Router-level (`APIRouter(dependencies=[...])`) | Cross-cutting for a group (auth on all `/admin/*`) |
| App-level / middleware | Truly global concerns (request IDs, base auth) |

For authentication specifically: a router-level dependency enforces auth on every
route in the router uniformly (harder to forget than per-handler), while middleware
sits even earlier but has coarser access to typed request data.

`dependency_overrides` is a dict mapping a dependency callable to a replacement;
FastAPI checks it during resolution. It's the same seam production uses, which is
why it's the right tool for tests (see `testing.md`).

## Gotchas

- **Dependency caching is per-request, not per-process.** A request-stable but
  expensive dependency still runs once per request. Promote real singletons to
  `@lru_cache` or `app.state` set in `lifespan`.
- **Business logic in handlers forces every edge case through an HTTP round-trip.**
  The suite gets slow, so it stops being run. Keep logic in services.
- **`yield` dependency teardown runs after the response is sent.** Don't rely on it
  to mutate the response; do rely on it to release resources.
- **Importing the app to read a setting can trigger import-time side effects.**
  Keep heavy construction (engines, clients, models) in `lifespan`, not at module
  import, or tests and CLIs pay the cost.
