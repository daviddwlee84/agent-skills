# mlflow-tracking

Generic [MLflow](https://mlflow.org/docs/latest) skill (upstream
[mlflow/mlflow](https://github.com/mlflow/mlflow)) — covers experiment
tracking, model registry, and LLM tracing for any Python project.

This is the **general-purpose** MLflow skill. For the marimo-specific
dual-mode (UI + batch CLI) variant, see
[`marimo-batch-mlflow`](marimo-batch-mlflow.md) instead — that one is a
specialization built on top of marimo notebooks.

## Three deployment modes (pick one before writing code)

| Mode | Tracking URI | When to choose |
|---|---|---|
| File | `file:./mlruns` (default) | One-off experiments, no UI, no model registry |
| **SQLite + `mlflow ui`** ⭐ | `sqlite:///mlflow.db` | Solo work, want UI without running a server, model registry support |
| **Docker Compose stack** ⭐ | `http://host:8000` (PostgreSQL + MinIO) | Team use, production, parallel jobs, large artifacts |
| Databricks-managed | `databricks://` | Already paying for Databricks (out of scope) |

The two starred modes cover ~95% of real use. **File mode does NOT support
the model registry** — if the user wants `register_model`, they need SQLite
or a server.

## What ships

- The full SKILL.md
  ([skills/local/mlflow-tracking/SKILL.md](https://github.com/daviddwlee84/agent-skills/blob/main/skills/local/mlflow-tracking/SKILL.md))
  with the deployment-mode decision table, the Manual-vs-Autolog choice,
  and a gotchas section calibrated to actual production failures (the
  `mlflow ui` `--backend-store-uri` trap, autolog ordering, deprecated
  stages, etc.).
- Six references — read on demand:
    - [`sqlite-local.md`](https://github.com/daviddwlee84/agent-skills/blob/main/skills/local/mlflow-tracking/references/sqlite-local.md)
      — SQLite mode setup, the `--backend-store-uri` gotcha, when to migrate
      to PostgreSQL.
    - [`docker-compose-server.md`](https://github.com/daviddwlee84/agent-skills/blob/main/skills/local/mlflow-tracking/references/docker-compose-server.md)
      — production stack ops, `.env` customization, AWS S3 swap, basic auth,
      backup strategy.
    - [`llm-tracing.md`](https://github.com/daviddwlee84/agent-skills/blob/main/skills/local/mlflow-tracking/references/llm-tracing.md)
      — autolog by provider (OpenAI, Anthropic, LangChain, LlamaIndex, DSPy,
      AutoGen, CrewAI, LiteLLM, Bedrock, Gemini, …), `@mlflow.trace`, span
      types, `search_traces`, comparison vs Weave/LangSmith/Langfuse.
    - [`model-registry.md`](https://github.com/daviddwlee84/agent-skills/blob/main/skills/local/mlflow-tracking/references/model-registry.md)
      — **aliases** (current API: Champion / Challenger) vs deprecated stages,
      registration patterns, webhooks.
    - [`autologging-by-framework.md`](https://github.com/daviddwlee84/agent-skills/blob/main/skills/local/mlflow-tracking/references/autologging-by-framework.md)
      — every officially-supported framework with per-library gotchas
      (sklearn, pytorch, lightning, tensorflow, keras, xgboost, lightgbm,
      catboost, statsmodels, spark, fastai, paddle, transformers, …).
    - [`mlflow-widgets-anywidget.md`](https://github.com/daviddwlee84/agent-skills/blob/main/skills/local/mlflow-tracking/references/mlflow-widgets-anywidget.md)
      — using [mlflow-widgets](https://github.com/daviddwlee84/mlflow-widgets)
      for live charts inside marimo / Jupyter without launching the full UI.
- Three scripts:
    - [`init-mlflow-sqlite.sh`](https://github.com/daviddwlee84/agent-skills/blob/main/skills/local/mlflow-tracking/scripts/init-mlflow-sqlite.sh)
      — idempotent SQLite-mode setup; prints the exact `mlflow ui` command
      with the right `--backend-store-uri` (the #1 SQLite gotcha).
    - [`start-mlflow-server.sh`](https://github.com/daviddwlee84/agent-skills/blob/main/skills/local/mlflow-tracking/scripts/start-mlflow-server.sh)
      — copies the bundled docker-compose stack into a target dir, generates
      `.env` with rotated random secrets, runs `docker compose up -d`, waits
      for the healthcheck, prints the URLs and client env vars to export.
    - [`tail-runs.sh`](https://github.com/daviddwlee84/agent-skills/blob/main/skills/local/mlflow-tracking/scripts/tail-runs.sh)
      — PEP 723 inline-deps Python script (runs via `uv run`, no env setup)
      that wraps `mlflow.search_runs` with JSON or CSV output for terminal use.
- The vendored production stack in `assets/docker-compose-stack/`:
    - [`docker-compose.yaml`](https://github.com/daviddwlee84/agent-skills/blob/main/skills/local/mlflow-tracking/assets/docker-compose-stack/docker-compose.yaml)
      — PostgreSQL + MinIO + tracking server + bucket bootstrap, with
      healthchecks and `depends_on` ordering.
    - [`Dockerfile`](https://github.com/daviddwlee84/agent-skills/blob/main/skills/local/mlflow-tracking/assets/docker-compose-stack/Dockerfile)
      — pinned MLflow image + `psycopg2-binary` + `boto3`.
    - [`.env.example`](https://github.com/daviddwlee84/agent-skills/blob/main/skills/local/mlflow-tracking/assets/docker-compose-stack/.env.example)
      — all knobs documented; default port 8000 to dodge macOS AirPlay on 5000.
    - [`README.md`](https://github.com/daviddwlee84/agent-skills/blob/main/skills/local/mlflow-tracking/assets/docker-compose-stack/README.md)
      — quick-start, troubleshooting, when to outgrow this stack.

## Why this exists alongside `marimo-batch-mlflow`

| Concern | `mlflow-tracking` (this) | `marimo-batch-mlflow` |
|---|---|---|
| Scope | Any Python project, any trainer | marimo notebooks specifically |
| Focus | Tracking server setup, registry, LLM traces, autolog | Dual-mode notebook pattern (UI + CLI) using MLflow |
| Includes Docker stack? | Yes, vendored from production | No |
| Includes LLM tracing? | Yes, full reference | No |

Use this skill when the user wants MLflow as a general tracking backend.
Use `marimo-batch-mlflow` when they're specifically writing marimo notebooks
that need to run as both an interactive UI and a batch CLI.

## Quick start

**SQLite (solo)**:

```bash
bash skills/local/mlflow-tracking/scripts/init-mlflow-sqlite.sh
# → prints the exact `mlflow ui --backend-store-uri sqlite:///mlflow.db --port 5001`
```

**Docker Compose stack (team)**:

```bash
bash skills/local/mlflow-tracking/scripts/start-mlflow-server.sh \
  --target-dir infra/mlflow
# → copies stack, rotates secrets in .env, launches, waits for healthcheck,
#   prints the env vars to export on client machines
```

**In your training code** (works for any of the modes):

```python
import mlflow

mlflow.set_tracking_uri("http://localhost:8000")    # or "sqlite:///mlflow.db"
mlflow.set_experiment("my-project")
mlflow.autolog()                                    # zero-touch logging

with mlflow.start_run():
    model.fit(X, y)                                 # params, metrics, model all logged
```

## Cross-references

- Official docs: [mlflow.org/docs/latest](https://mlflow.org/docs/latest) —
  always link these. MLflow ships every 4–6 weeks; LLM tracing especially
  is a moving target.
- Upstream repo: [github.com/mlflow/mlflow](https://github.com/mlflow/mlflow).
- [`mlflow-widgets`](https://github.com/daviddwlee84/mlflow-widgets) —
  anywidget-based charts/tables for embedding live MLflow data in marimo /
  Jupyter cells. Demo:
  [daviddwlee84.github.io/mlflow-widgets](https://daviddwlee84.github.io/mlflow-widgets/).
- [`marimo-batch-mlflow`](marimo-batch-mlflow.md) — the marimo-specific
  variant for dual-mode (UI + batch CLI) notebooks.
