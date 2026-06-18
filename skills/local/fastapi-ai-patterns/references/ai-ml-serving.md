# Serving AI: ML, RAG, and LLM applications

Read this when serving ML models, embeddings, RAG, or wrapping an LLM behind a
FastAPI endpoint. Covers the book's Chapter 9 in original wording — the highest-
value material in this skill.

## Table of contents

1. [What makes an ML service different](#what-makes-it-different)
2. [Model loading and inference endpoints](#model-loading)
3. [Batch and dynamic batching](#batching)
4. [LLM gateways and token streaming](#llm-gateways)
5. [Embeddings, vector DBs, and RAG](#embeddings-rag)
6. [Guardrails and the validation loop](#guardrails)
7. [Versioning, monitoring, humans in the loop](#versioning-monitoring)
8. [LLM cost model](#llm-cost-model)
9. [Gotchas](#gotchas)

---

## What makes it different

An ML inference service is an ordinary FastAPI app with three unusual properties:

1. **A heavy startup artifact** — weights take seconds to minutes to load. Load
   once, never per request.
2. **CPU/GPU-bound hot paths** — everything in `async-and-external.md` about not
   blocking the loop applies doubly.
3. **Probabilistic outputs** — correctness is a distribution, so monitoring must
   track quality, not just errors.

## Model loading

Load in `lifespan`, serve from memory, offload the CPU/GPU work off the loop, and
**echo the model version in every response**:

```python
@asynccontextmanager
async def lifespan(app):
    app.state.model = load_model("models/sentiment-v3.onnx")
    app.state.model_version = "sentiment-v3.2.1"
    yield
    app.state.model = None

class PredictOut(BaseModel):
    label: str
    confidence: float = Field(ge=0, le=1)
    model_version: str  # always identify the model

@app.post("/v1/predict", response_model=PredictOut)
async def predict(req: PredictIn):
    label, conf = await anyio.to_thread.run_sync(app.state.model.predict, req.text)
    return PredictOut(label=label, confidence=conf,
                      model_version=app.state.model_version)
```

Why lifespan (not per-request, not import-time): per-request loading re-reads
weights every call and OOMs under concurrency; import-time loading makes tests,
linters, and CLIs pay the cost (or crash without a GPU). Lifespan runs once per
worker before traffic and lets the readiness probe report ready only after the
model is warm. With N workers you hold N model copies — size worker count by
memory, or front a dedicated inference server (Triton, vLLM) for large models.

## Batching

GPUs are throughput machines — predicting 64 inputs costs little more than one. Two
modes:

- **Offline batching** — the client sends an array (cap its length), or a job-queue
  pipeline (see `async-and-external.md`) handles large corpora.
- **Dynamic micro-batching** — the server holds requests for a few milliseconds,
  batches them through the GPU, and fans results back. A ~5–10ms added wait buys
  multiples of throughput. This is the core trick of dedicated servers (Triton,
  vLLM); reach for them rather than hand-rolling it for serious load.

## LLM gateways

Wrap hosted APIs (OpenAI, Anthropic) or a self-hosted engine (vLLM) in your own
FastAPI service — an **LLM gateway**. One place for authentication, prompt
templates, guardrails, caching, cost metering, provider failover, and model swaps
without touching clients. This pattern pays for itself quickly.

Stream tokens over SSE so first tokens arrive in hundreds of ms instead of waiting
tens of seconds for the full completion:

```python
@app.post("/v1/chat/stream")
async def chat_stream(req: ChatIn, user: CurrentUser):
    await guardrails.check_input(req.message)  # pre-flight
    async def tokens():
        usage = {"out": 0}
        try:
            async for chunk in llm.stream(user=req.message, max_tokens=req.max_tokens):
                usage["out"] += 1
                yield f"data: {chunk.json()}\n\n"
            yield "data: [DONE]\n\n"
        finally:                       # runs even on disconnect
            await metering.record(user.id, usage)
    return StreamingResponse(tokens(), media_type="text/event-stream")
```

Two non-obvious details: the `finally` ensures metering survives the constant
mid-stream disconnects, and `max_tokens` validated with a Pydantic ceiling is
literally a spending limit.

## Embeddings and RAG

Design embedding APIs **batch-first** (`texts: list[str]` with caps) and **version
the model** in responses — vectors from different models are incomparable, so a
model upgrade means re-embedding the whole corpus.

RAG grounds answers in your documents. Ingestion (chunk → embed → store in a vector
DB) runs offline; the query path: embed the question → retrieve top-k → optionally
rerank → assemble a context-stuffed prompt → generate → return the answer **with
citations**.

Vector store choice: start with **pgvector** (vectors beside your relational
metadata — one system, transactional ingest, and SQL `WHERE` filters for ACL in the
same query; HNSW serves up to millions of vectors at tens of ms). Migrate to a
dedicated engine (Qdrant, Weaviate, Pinecone, Milvus) only when you hit sustained
recall/latency degradation at scale, vector counts past one node, or need hybrid
search the SQL side can't express. Hide the store behind a repository interface so
migration is an implementation swap.

## Guardrails

Validate both ends of the stochastic system.

- **Input side:** length/token caps (cost), prompt-injection screening (patterns +
  a small classifier on high-stakes routes), PII detection/redaction before text
  reaches third-party APIs, topic-policy checks.
- **Output side:** schema enforcement (parse the LLM's JSON into a Pydantic model),
  citation verification for RAG (every cited chunk id must exist in the retrieved
  set), content-policy screening, and PII/secret scanning before anything reaches
  the client.

**The validation loop** — the single most useful LLM-engineering pattern — turns a
stochastic generator into a typed component:

```python
async def extract_invoice(text: str) -> ExtractedInvoice:
    prompt = EXTRACT_PROMPT.format(text=text)
    for _ in range(2):
        raw = await llm.complete(prompt, json_mode=True)
        try:
            return ExtractedInvoice.model_validate_json(raw)
        except ValidationError as e:
            prompt = f"{prompt}\n\nYour previous output failed validation:\n{e}\nReturn corrected JSON only."
    raise HTTPException(502, "Model output failed validation")
```

Generate → validate with Pydantic → feed the error back → retry once (fixes most
cases) → on second failure raise a typed error to a defined fallback (human review,
a cheaper deterministic extractor, or 502). Never silently pass malformed data
downstream. Treat the LLM exactly like untrusted user input behind a validation
boundary; encode business rules as field constraints (`total >= 0`, enum currency).

## Versioning, monitoring

- **Model versioning:** artifacts are immutable, semantically versioned deployables
  (registry: MLflow/W&B or object storage + manifest). Expose stable routes with the
  version in the response, canary new models on a traffic slice, keep instant
  rollback (previous artifact warm). Version prompts in git and A/B-test them too.
- **Monitoring adds two layers** beyond standard API metrics: **AI performance**
  (time-to-first-token, tokens/sec, token usage and cost per request/user/feature,
  cache hit rate) and **quality** (sampled-traffic evals / LLM-as-judge, retrieval
  relevance, output-validation failure rate, guardrail trigger rate, user feedback,
  input-distribution drift).
- **Human-in-the-loop:** below a confidence threshold (or on guardrail triggers),
  route outputs to a review API (`GET /reviews/pending`, `POST /reviews/{id}/decision`)
  feeding corrections back as training/eval data. Design the human as a component
  with an SLA (track reviewer latency, inter-reviewer agreement), not an afterthought.

## LLM cost model

Per hosted-LLM request, cost ≈ `(input_tokens × price_in + output_tokens ×
price_out) / 1e6`. Input (context) usually dominates: RAG that stuffs 8K tokens of
chunks quadruples input cost, so **retrieval precision is a cost lever, not just a
quality lever**. Levers by typical ROI: response caching for repeated queries
(hit rate `h` scales cost by `1 − h`), prompt/context compression, output caps
(`max_tokens`), model routing (cheap model for easy queries, escalate hard ones),
and batch APIs (often discounted) for offline work. Always meter per user/feature —
one runaway agent loop can spend a month's budget in a day.

## Gotchas

- **Loading the model anywhere but `lifespan`** is the canonical AI-serving mistake
  — per-request OOMs under load, import-time breaks tests/CLIs.
- **Forgetting `model_version` in responses** makes "which model produced this bad
  output?" unanswerable during canary rollouts.
- **Trusting LLM output without a validation boundary** passes malformed/unsafe data
  downstream — parse into Pydantic and retry-then-fallback.
- **Enforcing RAG access control in the prompt** instead of the retrieval query lets
  prompt injection exfiltrate restricted chunks — filter by ACL in SQL.
- **No `finally` around a streaming generator** loses cost metering and keeps paying
  for generations the client already abandoned.
- **SSE behind a buffering proxy never streams.** Disable proxy buffering (e.g.
  nginx `X-Accel-Buffering: no`) and raise LB idle timeouts, or tokens arrive all at
  once at the end.
- **Re-embedding is mandatory on an embedding-model upgrade** — old and new vectors
  are incomparable. Version every stored vector and dual-write during migration.
- **Each active stream holds a worker slot for tens of seconds** — add concurrency
  limits and per-user stream caps so a few chatty clients can't starve the service.
