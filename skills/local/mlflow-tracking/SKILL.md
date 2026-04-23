---
name: mlflow-tracking
description: Set up and operate MLflow for ML experiment tracking, model registry, and LLM tracing in any Python project. Covers three deployment modes — local file (`./mlruns`), local SQLite + `mlflow ui` (recommended for solo experiments), and a production Docker Compose stack with PostgreSQL + MinIO (vendored as a ready-to-copy `assets/docker-compose-stack/`). Use whenever the user wants to log params/metrics/artifacts, manage models with aliases (Champion/Challenger), enable framework autologging (sklearn/pytorch/lightning/xgboost/transformers/etc.), trace LLM calls (OpenAI/Anthropic/LangChain/LlamaIndex/DSPy), spin up a self-hosted tracking server, or asks about `mlflow.set_tracking_uri` / `mlflow.start_run` / `mlflow.<framework>.autolog` / `mlflow ui` / `MLFLOW_TRACKING_URI`. Always references the official docs at https://mlflow.org/docs/latest and the upstream repo https://github.com/mlflow/mlflow — MLflow ships fast, prefer fetching live docs over relying on memory.
---

# MLflow Tracking

MLflow gives you experiment tracking, a model registry, and (since 2.14+) first-class LLM observability — all from one Python library + UI. Unlike DVC it **does** require a tracking backend (file / SQLite / server), but it gives you a real dashboard and multi-user collaboration in return.

This skill is opinionated about the **three deployment modes that actually get used in practice**, with a vendored production stack you can copy into any project. It defers to the official docs for everything else.

## When to use

- User wants to track ML experiments (params, metrics, artifacts) with a UI
- User mentions `mlflow.start_run`, `mlflow.log_metric`, `mlflow.set_tracking_uri`, `MLFLOW_TRACKING_URI`, `mlflow ui`
- User wants framework autologging (sklearn / PyTorch / Lightning / XGBoost / LightGBM / Keras / TensorFlow / Transformers / spark)
- User wants LLM trace observability (OpenAI, Anthropic, LangChain, LlamaIndex, DSPy, AutoGen, CrewAI, etc.)
- User wants to spin up a self-hosted tracking server with PostgreSQL + MinIO (production)
- User wants a model registry with aliases (Champion / Challenger / Production)
- User asks "how do I compare runs", "where do my logged params go", "how do I serve a logged model"

## When NOT to use

- User wants reproducible **pipelines** with data versioning → use `dvc-ml-workflow` skill
- User wants Weights & Biases specifically → MLflow is the open-source counterpart but not a drop-in replacement
- User wants DataBricks-managed MLflow → most code transfers, but auth/workspace setup is Databricks-specific; defer to Databricks docs
- User wants a single throwaway run with no UI → `print()` is fine; MLflow adds overhead

## Authoritative sources (link these, don't paraphrase from memory)

- Docs root: https://mlflow.org/docs/latest
- Tracking: https://mlflow.org/docs/latest/tracking.html
- Model Registry: https://mlflow.org/docs/latest/model-registry.html
- LLM tracing / GenAI: https://mlflow.org/docs/latest/llms/tracing/index.html
- Autologging matrix: https://mlflow.org/docs/latest/tracking/autolog.html
- Upstream repo: https://github.com/mlflow/mlflow
- PyPI: https://pypi.org/project/mlflow/
- mlflow-widgets (anywidget for live charts): https://github.com/daviddwlee84/mlflow-widgets

MLflow ships a release roughly every 4–6 weeks. **Fetch the docs page** before answering version-specific questions (especially anything about LLM tracing, which is the fastest-moving area).

## Decision: which deployment mode?

Pick **before** writing any code. Switching later means migrating runs.

| Mode | Tracking URI | When to choose | Read |
|---|---|---|---|
| **File** | `file:./mlruns` (default) | One-off experiments, no UI needed, no model registry | — |
| **SQLite + `mlflow ui`** ⭐ | `sqlite:///mlflow.db` | Solo work, small-to-medium experiment counts, want UI without running a server | `references/sqlite-local.md` |
| **Docker Compose stack** ⭐ | `http://host:8000` (PostgreSQL + MinIO) | Team use, production, parallel jobs, large artifacts, model registry across projects | `references/docker-compose-server.md` + `assets/docker-compose-stack/` |
| Databricks-managed | `databricks://` | Already paying for Databricks | (out of scope; defer to Databricks docs) |

The two starred modes cover ~95% of real use. **Default**: SQLite for quick experiments, Docker Compose stack when more than one person needs to see the same runs.

### File mode is for transient runs only

The default `file:./mlruns` mode does NOT support the model registry — `mlflow.register_model()` raises. If the user wants a registry **at all**, they need SQLite or a server backend, even for solo use.

## Workflow

### 1. Initialize the chosen mode

**SQLite (recommended for solo)**:

```bash
bash skills/local/mlflow-tracking/scripts/init-mlflow-sqlite.sh
# Creates mlflow.db, .gitignore entries, prints the URL to launch `mlflow ui`
```

**Docker Compose stack (recommended for team)**:

```bash
bash skills/local/mlflow-tracking/scripts/start-mlflow-server.sh --target-dir infra/mlflow
# Copies assets/docker-compose-stack/ into infra/mlflow/, customizes .env,
# runs `docker compose up -d`, waits for the healthcheck, prints the URL.
```

### 2. Set the tracking URI in your code

```python
import mlflow

# SQLite mode:
mlflow.set_tracking_uri("sqlite:///mlflow.db")

# Server mode:
mlflow.set_tracking_uri("http://localhost:8000")
```

Or via env var (preferred for subprocess / CI consistency):

```bash
export MLFLOW_TRACKING_URI=sqlite:///mlflow.db
# or
export MLFLOW_TRACKING_URI=http://localhost:8000
```

`set_tracking_uri()` only affects the current process. Subprocesses MUST use the env var.

### 3. Log a run

Two equally-valid styles. **Pick one**, don't mix in the same script.

**Manual logging** (full control):

```python
mlflow.set_experiment("my-project")           # creates if missing

with mlflow.start_run(run_name="baseline"):
    mlflow.log_params({"lr": 1e-3, "epochs": 25})
    for epoch in range(25):
        loss = train_step()
        mlflow.log_metric("train_loss", loss, step=epoch)
    mlflow.log_artifact("config.yaml")
    mlflow.sklearn.log_model(model, "model")
```

**Autologging** (zero-touch — preferred for supported frameworks):

```python
import mlflow
mlflow.autolog()                              # detects framework at first .fit()
# OR explicit:
mlflow.sklearn.autolog()
mlflow.pytorch.autolog()
mlflow.transformers.autolog()

with mlflow.start_run():
    model.fit(X, y)                           # params, metrics, model all logged
```

For per-framework caveats and the full list of supported libraries, **read** `references/autologging-by-framework.md`.

### 4. View results

```bash
# SQLite mode — must pass the same URI explicitly:
mlflow ui --backend-store-uri sqlite:///mlflow.db --port 5001

# Server mode — already has a UI at http://localhost:8000
```

For programmatic access:

```python
runs = mlflow.search_runs(experiment_names=["my-project"])    # pandas DataFrame
best = runs.sort_values("metrics.val_acc", ascending=False).iloc[0]
```

The bundled `scripts/tail-runs.sh` wraps `mlflow.search_runs` for terminal use.

### 5. Promote a model with the registry

```python
mlflow.set_registry_uri(mlflow.get_tracking_uri())   # usually unnecessary; auto-inherits

# Register from a logged run:
result = mlflow.register_model(
    f"runs:/{run_id}/model",
    name="my-model",
)

# Set an alias (replaces deprecated stages):
client = mlflow.MlflowClient()
client.set_registered_model_alias("my-model", "Champion", version=result.version)

# Load by alias:
model = mlflow.pyfunc.load_model("models:/my-model@Champion")
```

For aliases vs deprecated stages, model versioning, and webhooks, **read** `references/model-registry.md`.

### 6. (Optional) Trace LLM calls

MLflow 2.14+ ships an OpenTelemetry-style tracing system that competes with W&B Weave / LangSmith / LangFuse:

```python
import mlflow
mlflow.openai.autolog()         # auto-trace every OpenAI SDK call
# also: mlflow.anthropic / langchain / llama_index / dspy / autogen / crewai / litellm

# Or manual spans:
@mlflow.trace
def my_chain(query):
    return rag(query)
```

Traces show in the MLflow UI under the "Traces" tab. For provider matrix and trace querying, **read** `references/llm-tracing.md`.

### 7. (Optional) Live charts in marimo / Jupyter

Use `mlflow-widgets` (your own anywidget) for live-updating charts inside notebooks without spinning up the UI:

```python
from mlflow_widgets import MlflowChart
MlflowChart(experiment_name="my-project", metric="val_loss")
```

See `references/mlflow-widgets-anywidget.md` for installation and embedding patterns.

## Available scripts

- **`scripts/init-mlflow-sqlite.sh`** — Idempotent SQLite-mode init: touches `mlflow.db` if missing, adds `.gitignore` entries (`mlflow.db`, `mlruns/`, `mlartifacts/`), prints the exact `mlflow ui` command and `MLFLOW_TRACKING_URI` value to export.
  - Flags: `--db-path PATH` (default `mlflow.db`), `--port N` (default 5001), `--dry-run`, `--help`
- **`scripts/start-mlflow-server.sh`** — Copy `assets/docker-compose-stack/` into a target directory, generate `.env` from template (with secret rotation prompt), `docker compose up -d`, wait for healthcheck, print URLs.
  - Flags: `--target-dir DIR` (default `infra/mlflow`), `--port N` (default 8000), `--no-rotate-secrets`, `--dry-run`, `--help`
- **`scripts/tail-runs.sh`** — Wrap `mlflow.search_runs()` for terminal use. PEP 723 inline deps — runs via `uv run` with no setup. Outputs CSV/JSON to stdout.
  - Flags: `--experiment NAME`, `--top-n N`, `--sort-by METRIC`, `--format {json,csv}`, `--tracking-uri URI`, `--help`

## Bundled assets

- `assets/docker-compose-stack/` — Production-grade MLflow server: `docker-compose.yaml` (PostgreSQL + MinIO + tracking server + bucket bootstrap), `Dockerfile` (pinned MLflow image + psycopg2 + boto3), `.env.example`, `.gitignore`, `README.md`. Copy the whole folder into `<project>/infra/mlflow/`.

## Reference files

- `references/sqlite-local.md` — Read **when** the user picks SQLite mode or asks about `mlflow ui` not finding their runs. Covers the explicit `--backend-store-uri` requirement (the #1 SQLite-mode confusion).
- `references/docker-compose-server.md` — Read **when** deploying the server stack: customizing `.env`, persisting `mlflow_data/`, securing MinIO, using AWS S3 instead of MinIO, fronting with nginx + auth.
- `references/llm-tracing.md` — Read **when** the user asks about LLM observability, traces, prompts, token costs, or any of: OpenAI / Anthropic / LangChain / LlamaIndex / DSPy / AutoGen / CrewAI / LiteLLM. Covers `mlflow.<provider>.autolog`, `@mlflow.trace`, span attributes, and trace search.
- `references/model-registry.md` — Read **when** the user wants to manage model versions, promote between environments, or asks about Champion/Challenger. Covers aliases (current API) vs stages (deprecated), `MlflowClient`, webhooks.
- `references/autologging-by-framework.md` — Read **when** picking autolog for a specific library. Covers all officially-supported frameworks (sklearn, pytorch, lightning, tensorflow, keras, xgboost, lightgbm, catboost, statsmodels, spark, fastai, gluon, paddle, transformers) with per-framework gotchas.
- `references/mlflow-widgets-anywidget.md` — Read **when** the user wants live charts inside marimo or Jupyter without launching the full MLflow UI. Covers installation, the `MlflowChart` API, and embedding patterns.

## Gotchas

- **`mlflow ui` does NOT auto-pick up `sqlite:///mlflow.db`.** It defaults to `./mlruns/`. You MUST pass `--backend-store-uri sqlite:///mlflow.db` (matching what your code uses) or you'll see an empty UI. The init script prints the right command.
- **`set_tracking_uri()` is process-local.** Subprocesses (e.g., `subprocess.run`, `joblib`, `multiprocessing`) won't inherit it unless you set `MLFLOW_TRACKING_URI` in the environment first.
- **Autolog must be called BEFORE `start_run()`** (or before the first `.fit()` if you're not using a context manager). Calling it after silently logs nothing.
- **Model registry requires a database backend**. `file:./mlruns` raises on `register_model`. SQLite, PostgreSQL, and MySQL all work.
- **macOS port 5000 conflict**: AirPlay Receiver hijacks port 5000. The Docker stack uses 8000; the SQLite UI script uses 5001. If the user insists on 5000, tell them to disable AirPlay Receiver in System Settings → General → AirDrop & Handoff.
- **`AWS_ACCESS_KEY_ID` / `AWS_SECRET_ACCESS_KEY` must be set in the CLIENT environment** when using a server with S3/MinIO artifacts — the MLflow client uploads artifacts directly to S3, not via the server. Server-side env vars are not enough.
- **SQLite + parallel workers = `database is locked`.** SQLite serializes writes. Once the user is running >1 trainer at a time, migrate to the Docker stack (PostgreSQL).
- **Stages (`Staging` / `Production`) are deprecated** in MLflow ≥ 2.9. Use **aliases** (`Champion`, `Challenger`, etc.). Old code with `transition_model_version_stage()` still works but emits warnings; new code should use `set_registered_model_alias()`.
- **Run names are NOT unique** within an experiment. Two runs can both be named `"baseline"`. Identity = `run_id` (UUID). Set explicit, semantic `run_name` for human readability, but use `run_id` programmatically.
- **`MLFLOW_REGISTRY_URI` is almost never needed.** When tracking URI is HTTP / SQLite / PostgreSQL, the registry uses the same backend automatically. Setting both to different values is an advanced setup; don't do it by default.

## Cross-references

- For **marimo notebooks specifically** with a Tyro-based dual-mode (UI + batch CLI) pattern that uses MLflow, see the `marimo-batch-mlflow` skill — that one is a specialization, this skill is the general-purpose foundation.
