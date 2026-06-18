# Chapter 2 — Typing, Pydantic, and data validation

Read this when prepping Pydantic v2, validation, and schema design. Questions are
original; topics follow the book.

### Q1. Python type hints aren't enforced by the interpreter. How does Pydantic make them enforceable, and at what cost?

Pydantic builds a validator from the model's annotations and runs it at
construction time, coercing/validating each field and raising a structured error on
mismatch. The cost is per-request validation CPU (v2 moved the core to Rust to
shrink it) and the discipline of modeling your data. Senior signal: validation is
not free on large nested payloads — it shows up in p99.

### Q2. Why keep separate request, storage, and response models even though it triples class count?

Each has a different contract: the request model excludes server-set fields
(`id`, `created_at`); the storage model maps to the DB (and holds secrets like
`hashed_password`); the response model defines exactly what may leave the service.
Conflating them is the direct cause of internal-field leaks and of accepting fields
clients shouldn't set.

### Q3. Explain Pydantic v2 lax vs strict modes. When is coercion dangerous?

Lax (default) coerces compatible types (`"5"` → `5`); strict rejects anything not
already the right type. Coercion is dangerous when it silently masks a bug — e.g.
a truthy string becoming a bool, or a float id becoming an int — so use strict mode
or strict field types on inputs where a wrong type should be a hard error.

### Q4. An endpoint returns the SQLAlchemy `User` and the response includes `hashed_password`. Walk through the layers of defense.

(1) Declare a `response_model` (or typed return) that lists only public fields, so
serialization is allowlist-based. (2) Use a separate response schema, never the ORM
model. (3) Add a CI/lint check that every route declares a `response_model`. (4) In
tests, assert the exact key set so any new field fails the test. Defense in depth:
design makes the leak unrepresentable, tests catch regressions.

### Q5. How do nested validation errors surface, and why does the error structure matter?

Pydantic returns a list of errors each with a `loc` path into the nested structure,
a `type` code, and a message; FastAPI serves them as the 422 body. The structure
matters because clients parse `loc`/`type` to map errors to form fields and localize
messages — so the error body is part of your contract, not just debug output.

### Q6. Required vs optional vs nullable field — what's the difference?

Required: `x: int` (must be present). Optional with default: `x: int = 0` (may be
omitted, gets the default). Nullable: `x: int | None` (may be `null`). They compose:
`x: int | None = None` is optional-and-nullable. Conflating "omitted" with "null" is
a common API bug (see PATCH semantics).

### Q7. What does `Field(default_factory=list)` solve, and why not `tags: list[str] = []`?

A bare mutable default is created once at class definition and shared across all
instances, so appends leak between objects. `default_factory=list` produces a fresh
list per instance. Same rule for dicts/sets and any mutable default.

### Q8. How do Pydantic field constraints interact with OpenAPI docs?

Constraints like `Field(ge=0, le=1, max_length=4000)` both enforce at runtime and
emit into the OpenAPI schema (min/max, lengths, patterns), so the docs and any
generated client see the same rules. For AI endpoints these constraints double as
cost controls (input length caps, `max_tokens` ceilings).

### Q9. When would you use `@model_validator` instead of `@field_validator`?

Use `@field_validator` for single-field rules (normalize/validate one value). Use
`@model_validator` for cross-field invariants that need multiple values at once —
e.g. `end_date > start_date`, or "exactly one of A/B must be set." Cross-field logic
can't live in a field validator because it can't see the other fields reliably.

### Q10. Your p99 budget is 50ms and payloads are 2MB nested JSON. How do you keep validation from blowing the budget?

Cap payload size at the proxy and via field limits; avoid unnecessarily deep/large
nested models; don't re-validate the same data at multiple layers; consider lazy or
partial validation for huge optional sub-trees; and measure — validation cost is
real in v2 but usually dwarfed by I/O, so profile before optimizing.
