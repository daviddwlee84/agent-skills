---
name: fastapi-ai-scaffold
description: 'Scaffold a production-grade FastAPI AI/ML service from a bundled, opinionated skeleton. Use when starting a new FastAPI inference/LLM/RAG backend, bootstrapping a FastAPI project with clean architecture, or setting up a model-serving API with the production basics pre-wired: router/service/repository layering, lifespan-loaded model + httpx client, /health + /ready probes, JWT auth, SQLModel + Alembic, an SSE LLM gateway, guardrails + a Pydantic validation loop, tests with dependency_overrides, Docker, and gunicorn.'
---

# FastAPI AI Scaffold

Generates a runnable, production-shaped FastAPI AI/ML service so you don't
re-derive the same wiring every time. The skeleton encodes the patterns from the
`fastapi-ai-patterns` skill as working code: nothing here is novel framework
usage, it's the boring-but-correct baseline an inference service needs before it
sees traffic.

> Inspired by *FastAPI for AI Engineers* (AI Engineering Insider, 2026). All
> generated code is original.

## When to use

- "Start/bootstrap a new FastAPI service for serving a model / LLM / RAG / embeddings"
- "Set up a FastAPI project with clean architecture (router/service/repository)"
- The user wants the production basics pre-wired (lifespan model loading, auth,
  DB, probes, tests, Docker) rather than a single-file `main.py`

## When NOT to use

- The user just wants to understand a pattern or debug an existing app → use `fastapi-ai-patterns`
- They're prepping for an interview → use `fastapi-ai-interview-prep`
- They already have a project structure and want one endpoint added → don't
  regenerate; hand-write the endpoint following `fastapi-ai-patterns`

## Workflow

### 1. Generate the project

```bash
bash skills/local/fastapi-ai-scaffold/scripts/new-fastapi-ai-service.sh ./my-service
# preview first, write nothing:
bash skills/local/fastapi-ai-scaffold/scripts/new-fastapi-ai-service.sh --dry-run ./my-service
# override the package/metadata slug:
bash skills/local/fastapi-ai-scaffold/scripts/new-fastapi-ai-service.sh --name churn-scorer ./services/churn
```

The script copies the `assets/project/` skeleton, strips each file's `.tmpl`
suffix, and substitutes the project slug. It prints a JSON summary
(`project`, `slug`, `path`, `files`, `next_steps[]`) on stdout.

### 2. Install and run

```bash
cd ./my-service
uv venv && source .venv/bin/activate
uv pip install -e ".[dev]"
cp .env.example .env          # then set JWT_SECRET, DATABASE_URL, MODEL_PATH
uvicorn app.main:app --reload # http://127.0.0.1:8000/docs
pytest -q                     # the bundled tests should pass immediately
```

### 3. Make it yours

Replace the stubs with your real implementation — the structure stays:

- `app/ml/model.py` — swap `load_model`/`Model.predict` for your real artifact;
  swap `stream_llm_tokens` for a real provider/vLLM call. Keep `predict`
  synchronous and CPU-bound; the service already offloads it off the event loop.
- `app/models/`, `app/schemas/`, `app/repositories/`, `app/services/` — add your
  domain. Keep HTTP concerns in routers and business logic in services.
- Generate the first migration once models are real:
  `alembic revision --autogenerate -m "init"` then `alembic upgrade head`.
  Review the migration before applying — autogenerate misses renames/data moves.

## What the generated project contains

Clean-architecture layout under `app/` (router → service → repository), plus:

- **`app/lifespan.py`** — model handle, shared `httpx.AsyncClient`, and DB engine
  created once at startup and stored on `app.state` (per-process singletons).
- **`app/api/v1/health.py`** — cheap `/health` (liveness) vs dependency-checking
  `/ready` (readiness), so a DB blip removes a pod from rotation instead of
  restarting it.
- **`app/api/v1/auth.py` + `app/core/security.py`** — bcrypt hashing, JWT with a
  pinned algorithm, a `get_current_user` dependency.
- **`app/api/v1/inference.py`** — a `/predict` endpoint (CPU work offloaded via
  `anyio.to_thread`) and a `/chat/stream` LLM gateway using SSE.
- **`app/ml/guardrails.py`** — input checks and the generate → validate → retry
  loop that turns LLM output into a typed Pydantic value.
- **`tests/`** — `dependency_overrides` + in-memory SQLite, exact-key-set leak
  assertions, generic-login-error assertion.
- **Ops** — `Dockerfile` (multi-stage, non-root, HEALTHCHECK), `gunicorn_conf.py`
  (Uvicorn workers), `pyproject.toml`, `.env.example`, Alembic env.

## Available scripts

- **`scripts/new-fastapi-ai-service.sh <target-dir>`** — Generate the project.
  - Flags: `--name SLUG`, `--force`, `--dry-run`, `--help`.
  - Output: JSON summary on stdout; progress on stderr.

## Bundled assets

- `assets/project/` — the skeleton. Every file ends in `.tmpl`; the script strips
  the suffix and substitutes `PROJECT_SLUG_PLACEHOLDER`. Edit these `.tmpl` files
  to change what new projects get.

## Gotchas

- **`.tmpl` is mandatory on skeleton files.** The script only strips `.tmpl` and
  substitutes the slug; a skeleton file without the suffix is copied verbatim
  (intentional, e.g. `migrations/versions/.gitkeep`). Keep real app files `.tmpl`
  so editors don't try to import their (uninstalled) dependencies.
- **The generated package is named `app`, not the slug.** Only project *metadata*
  (pyproject name, README title, `.env` `APP_NAME`) uses the slug; imports are
  always `app.*`. Don't rename the package without updating every import.
- **The bundled tests use bare `TestClient` and skip lifespan on purpose** — they
  inject `app.state` doubles + `dependency_overrides`. If you write a test that
  relies on real startup, use `with TestClient(app) as client:` instead.
- **The model and LLM in `app/ml/model.py` are deterministic stubs**, not real
  inference. Tests assert shape/behavior, not model quality. Replace before deploy.
- **`init_db` (create_all) runs only in `environment=development`.** Production
  schema must go through Alembic; don't rely on `create_all` in prod.
