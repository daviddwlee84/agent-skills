# Chapter 3 — Building core API endpoints

Read this when prepping verbs, status codes, pagination, and versioning. Questions
are original; topics follow the book.

### Q1. Explain idempotency for each HTTP verb, and how you'd make POST safe to retry.

GET/PUT/DELETE are idempotent (repeating converges to the same state; a second
DELETE may 404). PATCH depends on its semantics. POST is not — each call typically
creates a new resource. Make POST retry-safe with an idempotency key: the client
sends a unique key, the server records it, and a replay returns the original result
instead of creating a duplicate.

### Q2. Offset vs cursor pagination: trade-offs and failure modes.

Offset/limit is simple and supports jump-to-page but degrades on deep pages (the DB
scans skipped rows) and can skip/duplicate rows when the set changes mid-paging.
Cursor/keyset is stable under inserts and fast at any depth but has no random page
access. Use cursor for large/fast-changing data and infinite scroll; offset for
small admin tables.

### Q3. A client PATCHes `{"description": null}`. How do you distinguish "clear it" from "not provided"?

Use Pydantic's `exclude_unset` / `model_fields_set` so a missing key and an explicit
`null` are different: present-and-null means clear the field; absent means leave it.
A naive optional-with-default model collapses both into the same value and can't
express "clear."

### Q4. Choose status codes: duplicate signup email, expired token, valid token wrong role, malformed JSON, schema-valid but business-rule violation, deleted resource.

Duplicate email → 409; expired token → 401; valid token but wrong role → 403;
malformed JSON / wrong types → 422 (FastAPI default); schema-valid but business-rule
violation → 422 or 409 (be consistent); deleted/absent resource → 404 (also 404 for
unauthorized object access to avoid leaking existence).

### Q5. How would you evolve an API from v1 to v2 without breaking consumers?

Run both behind a version prefix (`/api/v2`), announce a deprecation timeline,
instrument v1 usage, and remove v1 only after consumers migrate. Snapshot the
OpenAPI document in CI and fail on uncommunicated breaking changes; consider
generated client SDKs so partners track changes automatically.

### Q6. Why must list-endpoint `limit` parameters have a server-enforced maximum?

Without a cap, one caller can request the whole table — a latency and DoS hazard,
and a memory risk for the server. Enforce a max server-side (clamp or reject), so
the contract bounds resource consumption regardless of what the client asks for.

### Q7. What belongs in a path parameter vs a query parameter, and why does it matter?

Path parameters identify a specific resource and are part of its identity
(`/orders/{id}`); query parameters filter/sort/paginate a collection or toggle
options (`?status=open`). Getting it wrong hurts cacheability and makes URLs and
docs misleading about what's a resource vs a filter.

### Q8. PUT vs PATCH for an update endpoint?

PUT replaces the whole resource (idempotent; omitted fields are cleared/defaulted).
PATCH applies a partial change (only provided fields). Choose PATCH when clients
update a subset without resending the whole object, and handle the present-null vs
absent distinction explicitly.

### Q9. How do tags, summaries, and descriptions on endpoints affect more than aesthetics?

They structure the generated OpenAPI: tags group routes in Swagger/ReDoc and in
generated SDKs (often becoming client class/namespace boundaries), and
summaries/descriptions become the docstrings consumers and codegen read. Good
metadata improves discoverability and the shape of generated clients.

### Q10. A list endpoint is p95-slow only for consumers paginating to page 4,000. What are your options?

Switch those consumers to cursor/keyset pagination (deep offset is the cause); add a
covering index for the sort key; cap maximum offset and steer heavy exports to a
bulk/async job endpoint; or expose a streaming export. The root issue is deep-offset
scans, so eliminate the offset rather than tuning around it.
