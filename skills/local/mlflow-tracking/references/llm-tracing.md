# LLM tracing (MLflow GenAI)

> Authoritative source: https://mlflow.org/docs/latest/llms/tracing/index.html
>
> This is MLflow's fastest-moving area. **Fetch the docs before answering
> version-specific questions** — APIs change between minor releases.

MLflow 2.14+ added OpenTelemetry-style tracing for LLM apps. It captures
prompts, completions, token counts, latencies, and arbitrary span attributes,
and renders them in a "Traces" tab in the UI. Comparable to W&B Weave,
LangSmith, Langfuse, Arize Phoenix.

## Two ways to instrument

### Autolog by provider (preferred)

One line, instruments every call from the SDK:

```python
import mlflow
mlflow.openai.autolog()
mlflow.anthropic.autolog()
mlflow.langchain.autolog()
mlflow.llama_index.autolog()
mlflow.dspy.autolog()
mlflow.autogen.autolog()
mlflow.crewai.autolog()
mlflow.litellm.autolog()
mlflow.bedrock.autolog()
mlflow.gemini.autolog()
mlflow.mistral.autolog()
mlflow.groq.autolog()
mlflow.ollama.autolog()
mlflow.smolagents.autolog()
mlflow.pydantic_ai.autolog()
```

(The exact set varies by version. **Check the autologging docs** for the
current list before claiming a provider isn't supported.)

After autolog, every SDK call generates a trace automatically — no code
changes to the app.

### Manual `@mlflow.trace` decorator

For custom code paths that aren't covered by autolog (your own RAG, your
own router, custom evaluators):

```python
import mlflow

@mlflow.trace
def retrieve(query: str) -> list[str]:
    return vector_db.search(query)

@mlflow.trace
def rag(query: str) -> str:
    docs = retrieve(query)                # nested as a child span
    return llm.complete(make_prompt(query, docs))
```

Spans nest based on Python call stack. Add attributes:

```python
@mlflow.trace(span_type="RETRIEVER")
def retrieve(query):
    docs = vector_db.search(query)
    span = mlflow.get_current_active_span()
    span.set_attribute("num_docs", len(docs))
    span.set_attribute("query_len", len(query))
    return docs
```

`span_type` standard values: `LLM`, `CHAIN`, `AGENT`, `TOOL`, `CHAT_MODEL`,
`RETRIEVER`, `RERANKER`, `EMBEDDING`, `PARSER`, `UNKNOWN`. Custom strings work too.

## Configuring tracking destination

Traces go to whatever `MLFLOW_TRACKING_URI` points at — the same SQLite DB or
server you use for runs. They show under the "Traces" tab of an experiment.

```python
mlflow.set_tracking_uri("http://localhost:8000")
mlflow.set_experiment("rag-prod")
mlflow.openai.autolog()                    # all subsequent OpenAI calls traced
```

You don't need `start_run()` for traces — they're standalone records.

## Searching traces

```python
import mlflow
client = mlflow.MlflowClient()

traces = client.search_traces(
    experiment_ids=["123"],
    filter_string="tags.session_id = 'abc' AND attributes.status = 'OK'",
    max_results=100,
)
for t in traces:
    print(t.info.trace_id, t.info.execution_time_ms)
```

UI search works on the same syntax.

## Token usage and cost

Autolog populates `usage` attributes on `LLM` spans automatically for major
providers (OpenAI, Anthropic, Bedrock, Gemini). Costs are NOT computed by
MLflow — you'd add them as a custom span attribute or post-hoc with a script
that walks `client.search_traces()`.

## Production gotchas

- **Trace volume**: every LLM call writes to the tracking backend. For high-QPS
  apps, this is real load. Use `mlflow.disable_traces_for_function(fn)` or
  conditional autolog (only enable in dev/staging).
- **PII in prompts/completions**: traces store the full prompt and response.
  Sanitize before logging if your data has PII. There is no built-in PII
  scrubber.
- **Timeouts**: trace export is sync by default. If your tracking server is
  slow, your LLM calls slow down too. For prod, run the tracking server on the
  same VPC as your inference workers.
- **Mixed autolog**: enabling both `mlflow.openai.autolog()` and
  `mlflow.langchain.autolog()` when LangChain calls OpenAI internally creates
  duplicate spans. Pick the highest-level instrumentation (LangChain) and
  rely on its sub-spans.
- **Nested with `start_run`**: traces and runs are independent record types.
  You can have one inside the other; the UI links them. But don't try to
  "log a trace as a metric" — they're not interchangeable.

## Evaluating traces

`mlflow.evaluate()` works on traces too — pass a list of trace IDs and a
function that scores each. See https://mlflow.org/docs/latest/llms/llm-evaluate/index.html.

```python
results = mlflow.evaluate(
    data=traces,
    extra_metrics=[
        mlflow.metrics.genai.relevance(),
        mlflow.metrics.genai.faithfulness(),
    ],
)
```

For LLM-as-judge metrics, MLflow ships `genai` metric helpers backed by
GPT-4 / Claude / etc. — configure with `mlflow.metrics.genai.<metric>(model="openai:/gpt-4")`.

## Comparison to alternatives

| Concern | MLflow Tracing | LangSmith | Langfuse | W&B Weave |
|---|---|---|---|---|
| Open source | Yes (Apache 2.0) | No | Yes | Partially |
| Self-hosted | Yes (this skill) | No | Yes | Yes |
| Co-located with experiment tracker | Yes (same UI) | No | No | Yes |
| Provider coverage (autolog) | Broad and growing | LangChain-first | Manual SDK | Broad |

For users already on MLflow for experiments, the answer is almost always
"use MLflow tracing too" — same backend, same UI, no extra service.
