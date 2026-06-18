# API design: REST, ASGI, and Pydantic contracts

Read this when designing routes, choosing status codes, paginating/versioning a
list endpoint, or modeling request/response schemas with Pydantic v2. Covers the
book's Chapters 1–3 in original wording.

## Table of contents

1. [ASGI vs WSGI — why the server interface matters](#asgi-vs-wsgi)
2. [REST semantics and idempotency](#rest-semantics-and-idempotency)
3. [Path vs query vs body](#path-vs-query-vs-body)
4. [Status codes that mean what they say](#status-codes)
5. [Pagination, filtering, sorting](#pagination)
6. [Versioning](#versioning)
7. [Pydantic v2 contracts](#pydantic-v2-contracts)
8. [Gotchas](#gotchas)

---

## ASGI vs WSGI

WSGI (the older sync contract) occupies one worker thread/process for a request's
full duration: if a handler waits 2s on a database or upstream LLM, that worker
does nothing for 2s. ASGI replaces the blocking call with an async event protocol,
so one event loop interleaves thousands of in-flight requests — while one awaits a
row, the loop serves others. ASGI also enables protocols WSGI structurally can't:
WebSockets, server-sent events, HTTP/2 streaming — all needed for LLM token streams.

The performance win is specifically for **I/O-bound** work (waiting on DBs, caches,
upstream APIs). For CPU-bound work (in-process inference, image processing) the
loop does not help and actively hurts if you block it. This distinction is the
root of the most common FastAPI production mistake (see `async-and-external.md`).

FastAPI is an ASGI *application*; it needs an ASGI *server* (Uvicorn) to open
sockets, parse HTTP, and drive the loop. Same app/server split as Flask/Gunicorn.

## REST semantics and idempotency

Resources at URLs, manipulated with verbs: `GET` reads, `POST` creates, `PUT`
replaces, `PATCH` partially updates, `DELETE` removes. What matters in practice is
consistency: predictable URLs, correct verbs, correct status codes, stable schemas.

Idempotency (same request repeated = same server state) by verb:

| Verb | Idempotent? | Notes |
|---|---|---|
| GET | yes | Safe (no state change) |
| PUT | yes | Full replace converges to the same state |
| DELETE | yes | Deleting twice ends in the same state (2nd may 404) |
| PATCH | not inherently | Depends on the patch semantics |
| POST | no | Each call typically creates a new resource |

Make `POST` safe to retry with an **idempotency key**: the client sends a unique
key, the server records it, and a replay returns the original result instead of
creating a duplicate. Essential for payments and any "create" a flaky client may
retry.

## Path vs query vs body

- **Path parameter** — identifies a specific resource (`/orders/{id}`). Required,
  part of the resource's identity.
- **Query parameter** — filters/sorts/paginates a collection, or toggles options
  (`?status=open&limit=50`). Optional, doesn't change which resource.
- **Body** — the payload for create/update; validated against a Pydantic model.

Getting this wrong makes URLs that don't cache well and docs that mislead.

## Status codes

Pick the code that tells the client what to do next:

| Situation | Code |
|---|---|
| Created a resource | 201 |
| Accepted async work (job queued) | 202 |
| Success, no body | 204 |
| Malformed JSON / wrong types | 422 (FastAPI's validation default) |
| Unauthenticated | 401 |
| Authenticated but not allowed | 403 |
| Resource missing (or hidden by authz) | 404 |
| Duplicate (e.g. signup email exists) | 409 |
| Schema-valid but business-rule violation | 422 or 409 (be consistent) |
| Rate limited | 429 (+ `Retry-After`) |

A login that returns 401 with a generic message for both "email not found" and
"wrong password" avoids leaking account existence (see `security.md`).

## Pagination

- **Offset/limit** (`?offset=80&limit=20`) — simple, supports jump-to-page, but
  degrades for deep pages (the DB still scans skipped rows) and can skip/duplicate
  rows when the underlying set changes mid-paging.
- **Cursor/keyset** (`?after=<opaque>`) — stable under inserts, O(1)-ish deep
  paging, but no random page access. Prefer for large or fast-changing datasets
  and for infinite-scroll UIs.

Always enforce a **server-side maximum** on `limit`. An unbounded `limit` lets one
caller request the whole table and is both a performance and a DoS hazard.

## Versioning

Put the version in the path (`/api/v1/...`) for the clearest contract boundary.
Evolve v1 → v2 by running both during a deprecation window: add v2 routes,
announce a timeline, monitor v1 usage, and remove v1 only after consumers migrate.
Snapshot the OpenAPI document in CI and fail the build on uncommunicated breaking
changes so docs can't drift from reality.

## Pydantic v2 contracts

- **Separate request, storage, and response models** even though it triples the
  class count. The request model defines what callers may send (no server-set
  fields like `id`/`created_at`); the storage model maps to the DB; the response
  model controls exactly what leaves the service. Conflating them is how internal
  fields leak.
- **Lax vs strict coercion.** v2 coerces by default (`"5"` → `5`). Convenient, but
  dangerous where silent coercion hides bugs (e.g. a bool from `"false"`). Use
  strict mode or strict field types on inputs where coercion would mask errors.
- **Field constraints document and enforce at once.** `Field(min_length=1,
  max_length=4000)` both validates and appears in OpenAPI. For AI endpoints these
  caps are cost controls (max input length, `max_tokens` ceiling).
- **Required vs optional vs nullable are three different things.** `x: int` is
  required; `x: int = 0` is optional with a default; `x: int | None` is nullable.
  Use `Field(default_factory=list)` for mutable defaults — `tags: list[str] = []`
  shares one list across instances.
- **`@field_validator` vs `@model_validator`.** Field validators check one field;
  model validators check across fields (e.g. `end_date > start_date`).
- **PATCH with explicit null.** To distinguish "set this field to null" from
  "field not provided", use `model_fields_set` / `exclude_unset` so a missing key
  and an explicit `null` are handled differently.

## Gotchas

- **Returning an ORM object without a `response_model` serializes every column**,
  including secrets. Declare a response model (or a typed return) on every route.
- **422 is FastAPI's validation default, not 400.** Clients parse `detail[].loc`
  and `detail[].type`; treat that error body as part of your contract.
- **Large nested-JSON validation has a latency cost.** For tight p99 budgets on
  big payloads, cap sizes, avoid over-deep nesting, and don't re-validate the same
  data at multiple layers.
- **`limit` without a server cap is a footgun** — a deep-paginating or
  whole-table-requesting client degrades the endpoint for everyone.
