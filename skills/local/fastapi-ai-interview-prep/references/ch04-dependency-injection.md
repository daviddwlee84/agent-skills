# Chapter 4 — Dependency injection and application structure

Read this when prepping `Depends()`, layering, and project structure. Questions are
original; topics follow the book.

### Q1. How does FastAPI resolve `Depends()` for a request, including chaining and caching?

It resolves each dependency callable, recursively resolving that callable's own
dependencies first, then injects the result into the handler. Within one request it
caches by callable, so a dependency declared in several places runs once and the
value is shared. Caching is per-request, not per-process.

### Q2. Why do `yield`-based dependencies matter for DB sessions, and what happens on an unhandled exception?

A `yield` dependency runs setup before the handler and teardown after, so a session
opened before `yield` is closed in the `finally` after the response — even when the
handler raises. That guarantees no leaked sessions and (with the right pattern) a
rollback on error; a plain dependency can't clean up post-response.

### Q3. Where should business logic live, and how do you keep HTTP concerns out of it? What goes wrong otherwise?

In a service layer that knows nothing about HTTP (no `Request`, no `HTTPException`),
so it's unit-testable without a client and reusable across entrypoints. If logic
lives in handlers, every edge case must be tested through an HTTP round-trip, the
suite slows down, and it stops being run.

### Q4. Defend the repository pattern, and state when you'd skip it.

It encapsulates data access behind an interface, so services are testable with fake
repositories and the store is swappable. Skip it for genuinely trivial CRUD where
the indirection buys nothing — but introduce it the moment a query is reused or
business logic starts leaking into data access.

### Q5. Compare router-level dependencies, app-level dependencies, and middleware for enforcing authentication.

A router-level dependency enforces auth uniformly on every route in a group
(`APIRouter(dependencies=[...])`) and is hard to forget. An app-level dependency
applies globally. Middleware runs even earlier and is good for cross-cutting
concerns (request IDs) but has coarser access to typed request data and can't use
the DI cache. Prefer router/handler deps for auth so you get typed user objects.

### Q6. What is a composition root, and why centralize `Depends()` wiring?

The composition root is the single place that decides which concrete implementation
satisfies each dependency. Centralizing it removes per-handler construction, makes
implementations swappable, and turns test overrides into a one-line change instead
of edits scattered across handlers.

### Q7. How does `dependency_overrides` relate to this architecture?

It's a dict mapping a dependency callable to a replacement, checked during
resolution. Because the composition root wires everything through dependencies,
tests swap the DB, auth, or an LLM client at the same declared seam production uses —
no monkeypatching of import paths.

### Q8. When does a class-based dependency beat a function-based one?

When the dependency carries configuration or state: a class can be constructed with
parameters (e.g. a `RateLimiter(max=100)` instance used as `Depends(limiter)`),
exposing `__call__`. Function dependencies are simpler for stateless resolution.
Class-based shines when you want parameterized, reusable, testable instances.

### Q9. Five dependencies in one request each `Depends(get_settings)`. How many times does `get_settings` run, and how do you make it once per process?

Once per request (per-request caching), not five times. To make it once per process,
wrap it in `@lru_cache` (or build the settings in `lifespan` and store on
`app.state`), so every request reuses the same instance instead of re-reading the
environment.

### Q10. Your handlers construct services inline. List the problems and outline the migration.

Inline construction couples handlers to concrete classes, duplicates setup, makes
swapping implementations a find-and-replace, and blocks test overrides. Migrate by
extracting provider functions (`get_user_service(session) -> UserService`), declaring
them as `Annotated[..., Depends(...)]`, replacing inline construction with the
injected parameter, then overriding those providers in tests.
