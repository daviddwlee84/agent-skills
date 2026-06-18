# Chapter 9 — FastAPI for AI, ML, RAG, and LLM applications

Read this when prepping the AI-serving questions — the heart of the role. Questions
are original; topics follow the book.

### Q1. Why must ML models load in the lifespan handler, and what breaks with lazy per-request or import-time loading?

Per-request loading re-reads weights every call (seconds of disk/GPU transfer) and
OOMs as concurrent requests each load copies. Import-time loading couples loading to
module import, so tests, linters, and CLI tools pay the cost or crash without a GPU.
Lifespan loading runs once per worker before traffic, integrates with readiness probes
(ready only when warm), and supports clean shutdown. Senior note: N workers hold N
copies — size by memory or use a dedicated inference server.

### Q2. Design the streaming architecture for an LLM chat endpoint end to end.

Use SSE over `StreamingResponse` for one-way token flow (WebSocket only if mid-stream
client→server interaction is needed); frames are `data:` JSON chunks ending in
`[DONE]`. Run input guardrails pre-flight; moderate output incrementally or post-hoc
since you can't unsay streamed tokens. Wrap the generator in `try/finally` so metering,
logging, and upstream cancellation run on the constant client disconnects.
Infrastructure: disable proxy buffering, raise LB idle timeouts, monitor TTFT
separately, and cap per-user concurrent streams.

### Q3. A RAG system gives confidently wrong answers. Walk through your diagnosis.

RAG failures are usually retrieval failures in disguise. (1) Retrieval: inspect the
retrieved chunks for failing queries — right docs present? If not, fix chunking,
embedding-domain mismatch, or missing metadata filters; measure recall@k on a labeled
set. (2) Ranking: right doc retrieved but below the cutoff → add a reranker.
(3) Prompt assembly: truncated/poorly-ordered context or weak instructions.
(4) Generation: model ignoring context → stronger grounding + citation-required
validation. (5) Systemic: add a nightly eval harness so regressions are metrics, not
incidents.

### Q4. How do you make a stochastic LLM safe to use as a typed component?

Contract it: request structured output (JSON/function-calling), parse into a Pydantic
model (the same validation boundary as any untrusted input, with field constraints
encoding business rules), and on `ValidationError` retry once with the error appended
(fixes most cases). On a second failure raise a typed error to a defined fallback —
human review, a deterministic extractor, or 502 — never pass malformed data downstream.
Log validation-failure rate per model/prompt version as a quality and upstream-drift
signal.

### Q5. Compare pgvector against a dedicated vector DB, and give migration triggers.

pgvector keeps vectors beside relational metadata: one system, transactional ingest,
SQL filters for ACL in the same query, and HNSW serving up to millions of vectors at
tens of ms. Dedicated engines (Qdrant, Weaviate, Pinecone, Milvus) add horizontal
scale, faster ANN at 10M–1B, and richer hybrid search — at the cost of a second
datastore (dual writes, consistency, ops). Migrate when recall/latency degrades
despite HNSW tuning, vectors exceed one node, or you need hybrid search SQL can't do.
Hide it behind a repository so migration is a swap.

### Q6. Why does an embedding API need the model version in its response, and what's the upgrade consequence?

Cosine similarity between vectors from different models is noise, so consumers must
store the producing model alongside the vectors. Upgrading the embedding model means
re-embedding the entire corpus: build a new index alongside the old, dual-write during
transition, validate, cut reads over, then drop the old. Version tags on every stored
vector and API response make this trackable and reversible.

### Q7. What is prompt injection, and which defenses actually work for an endpoint that processes user documents?

Prompt injection embeds instructions in user content ("ignore previous instructions"),
directly or indirectly via ingested documents (the RAG attack surface). No complete
defense exists; effective layers: privilege separation (the model gets least-privilege
tools; the system never executes model output with user trust — ACL filtering happens
in SQL, not by asking the model), input screening, instruction/content demarcation
(helpful, insufficient alone), output validation so a hijacked generation can't emit
secrets, and tool-call allowlisting with human confirmation. Treat "the model saw
attacker text" as "the model may be compromised."

### Q8. Your LLM bill doubled month-over-month with flat traffic. Where do you look?

Decompose cost per request into input/output tokens by endpoint and feature (if you
didn't meter, that's finding zero). Usual suspects: context growth (RAG retrieving
more/larger chunks, unbounded conversation history), a prompt-template change that
ballooned the system prompt, retry/validation loops re-calling the model (check call
count vs request count), agent loops without an iteration cap, a model-routing shift
to the expensive model, cache hit-rate collapse, and provider price changes. Fix with
per-feature budgets, max-token caps, caching, and routing.

### Q9. When does batch inference beat real-time, and how do you expose each through an API?

Batch wins when latency is non-critical and throughput/cost dominate (offline scoring,
nightly re-embedding) — GPUs process 64 inputs for nearly the cost of one. Expose
real-time as a synchronous `POST /predict` (small payloads, cap input). Expose batch
as a job API: submit returns 202 + job id, workers process, client polls or gets a
webhook. Dynamic micro-batching bridges them by holding requests a few ms to batch
through the GPU.

### Q10. Design the human-in-the-loop component for an AI document-extraction service. Why is it an engineering problem, not a UI problem?

Below a confidence threshold or on guardrail triggers, route outputs to a review queue
API (`GET /reviews/pending`, `POST /reviews/{id}/decision`) and feed corrections back
as training/eval data. It's an engineering problem because the human is a component
with an SLA: you must track reviewer latency and throughput (capacity planning via
Little's Law), inter-reviewer agreement (quality), routing logic, idempotent decisions,
and a feedback loop into evals — not just a screen.
