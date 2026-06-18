# Chapter 1 — FastAPI, ASGI, and modern API development

Read this when prepping the fundamentals: what FastAPI is, ASGI vs WSGI, REST,
OpenAPI, and why type hints are load-bearing. Questions are original; topics
follow the book.

### Q1. What is FastAPI, and which two libraries does it compose?

FastAPI is an ASGI Python framework for building typed HTTP APIs. It is a thin
layer over Starlette (the ASGI toolkit: routing, middleware, WebSockets,
background tasks) and Pydantic (type-driven parsing and validation), adding a
dependency-injection system and automatic OpenAPI generation. Senior signal:
note the practical consequence — bugs often live in Starlette or Pydantic, so
debugging means knowing which layer owns a behavior (middleware order = Starlette,
validation errors = Pydantic, `Depends()` = FastAPI).

### Q2. Explain WSGI vs ASGI, and why WSGI cannot support WebSockets.

WSGI is a synchronous contract: one worker is occupied per request for its full
duration. ASGI is an async event protocol (`scope`/`receive`/`send`) so one event
loop multiplexes many requests. WebSockets need a long-lived bidirectional channel
where either side sends at any time; the WSGI request-then-response contract has no
place for the server to deliver later messages or for the handler to push multiple
frames. ASGI's receive/send message pairs model exactly that.

### Q3. A `sync def` handler spends 200ms on CPU; an `async def` handler awaits a 200ms upstream call. How does FastAPI schedule each?

The plain `def` handler runs in Starlette's threadpool, so it occupies a thread but
doesn't block the event loop; throughput is bounded by threadpool size (and the GIL
for true CPU work). The `async def` handler runs on the loop; awaiting suspends it
and frees the loop to serve others, so thousands can be in flight. The classic trap:
`async def` with a blocking call inside freezes the whole loop.

### Q4. How does FastAPI generate interactive docs, and why is that more reliable than hand-written docs?

At startup it introspects every route — paths, methods, parameter annotations,
Pydantic models, status codes, security deps — and compiles an OpenAPI document
served at `/openapi.json`; Swagger UI and ReDoc just render it. Reliability comes
from provenance: the schema is derived from the executing code, so it can't drift
like a wiki page. Senior addition: the OpenAPI artifact also feeds contract tests
and SDK generation in CI, making doc accuracy a build guarantee.

### Q5. Why are Python type hints "executed" in FastAPI rather than stylistic?

In most code, hints are passive metadata. In FastAPI, an annotation like
`item_id: int` drives request parsing, coercion, validation (structured 422),
the OpenAPI schema, and docs rendering — one declaration, five behaviors. The
annotation is the single source of truth for the request contract, eliminating the
validation-code + docs + serializer duplication other stacks need.

### Q6. What is Uvicorn, and why does FastAPI need a separate server?

A FastAPI app is an ASGI application — a callable consuming ASGI events; it can't
open sockets, parse HTTP, or run the loop. Uvicorn is the ASGI server that does
those things and invokes the app. The split mirrors WSGI's app/server divide
(Flask/Gunicorn) and lets servers and frameworks evolve independently.

### Q7. What does statelessness mean in REST, and what does it buy operationally?

Each request carries everything the server needs; the server keeps no per-client
session memory between requests. Operationally this makes horizontal scaling
trivial: any worker serves any request, no sticky sessions, instances are
add/remove/replaceable, and a crashed node loses no client state. State that must
persist moves to shared stores (DB, Redis).

### Q8. When would you choose Django over FastAPI, and vice versa?

Choose Django when you need its admin UI, mature ORM/migrations, and built-in
auth/sessions — content platforms, admin-heavy products. Choose FastAPI when the
deliverable is the API: microservices, ML/LLM serving, streaming, high-concurrency
I/O. Senior nuance: the call is rarely purely technical (team familiarity, hiring,
existing infra), and hybrids (Django admin + FastAPI inference service) are common.

### Q9. What is OpenAPI, and how does it differ from Swagger UI?

OpenAPI is the vendor-neutral specification format (a JSON/YAML document describing
paths, schemas, parameters, security). Swagger UI is one viewer that renders an
OpenAPI document as interactive docs. "Swagger" was the spec's original name before
it was donated and renamed OpenAPI v3; the tooling kept the brand, which is why the
terms get conflated.

### Q10. Your hand-maintained API docs keep drifting and partners complain. How does FastAPI change the workflow?

Move the contract into code: Pydantic models and typed signatures become the only
place the API shape is defined, and `/openapi.json` is correct by construction. In
CI, snapshot the OpenAPI document and fail the build on uncommunicated breaking
changes; optionally generate client SDKs so partners consume always-current
bindings. Documentation stops being a parallel artifact and becomes a build output.
