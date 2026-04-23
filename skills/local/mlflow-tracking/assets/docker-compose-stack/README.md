# MLflow tracking server — production stack with PostgreSQL + MinIO

> Vendored from a working production setup. Copy this entire directory into your
> project (e.g., `infra/mlflow/`), customize `.env`, and run `docker compose up -d`.

Self-contained MLflow stack:

```
PostgreSQL (tracking DB) ◄── MLflow Server ──► MinIO (S3-compatible artifacts)
   :5432                       :8000                :9000 (API) / :9001 (Console)
```

## Quick start

```bash
# 1. Copy this folder to your project
cp -r assets/docker-compose-stack /your-project/infra/mlflow
cd /your-project/infra/mlflow

# 2. Customize environment (defaults work for local dev)
cp .env.example .env
# Edit .env to change ports, credentials, bucket name

# 3. Launch
docker compose up -d

# 4. Verify
curl http://localhost:8000/health   # should print "OK"
open http://localhost:8000           # MLflow UI
open http://localhost:9001           # MinIO console (minioadmin / minioadmin)
```

## Connect from Python

```python
import mlflow

mlflow.set_tracking_uri("http://localhost:8000")
# That's it — model registry uses the same backend automatically.

with mlflow.start_run():
    mlflow.log_param("lr", 1e-3)
    mlflow.log_metric("acc", 0.92)
    mlflow.sklearn.log_model(model, "model", registered_model_name="my-model")
```

Or via env var:

```bash
export MLFLOW_TRACKING_URI=http://localhost:8000
```

## Configuration

All knobs live in `.env`. Defaults are sensible for local dev — change at minimum
`MINIO_ACCESS_KEY` / `MINIO_SECRET_ACCESS_KEY` / `PG_PASSWORD` for any non-local use.

| Variable | Default | Purpose |
|---|---|---|
| `MLFLOW_PORT` | `8000` | MLflow UI/API port (avoid 5000 — macOS uses it for AirPlay) |
| `PG_USER` / `PG_PASSWORD` / `PG_DATABASE` / `PG_PORT` | `mlflow` / `mlflow` / `mlflow` / `5432` | PostgreSQL credentials |
| `MINIO_ACCESS_KEY` / `MINIO_SECRET_ACCESS_KEY` | `minioadmin` / `minioadmin` | MinIO root credentials |
| `MINIO_API_PORT` / `MINIO_CONSOLE_PORT` | `9000` / `9001` | MinIO API and web console |
| `MLFLOW_BUCKET_NAME` | `mlflow` | S3 bucket created on first boot |

## Data persistence

Everything lives under `./mlflow_data/`:
- `db_data/` — PostgreSQL data
- `minio_data/` — Artifact storage (models, plots, anything you `log_artifact`)

Back up by copying `mlflow_data/`. Reset by `docker compose down -v` (destroys volumes).

## Common operations

```bash
# View logs
docker compose logs -f tracking_server

# Stop everything (data persists)
docker compose down

# Stop and DELETE all data (warning: irreversible)
docker compose down -v

# Rebuild MLflow image (after Dockerfile change)
docker compose build --no-cache tracking_server
docker compose up -d
```

## Why PostgreSQL + MinIO instead of SQLite + local files?

- **Concurrency**: SQLite serializes writes — multiple training jobs hit `database is locked` errors. PostgreSQL handles parallel runs cleanly.
- **Model Registry**: requires a real DB backend. SQLite works locally; PostgreSQL is the production version of the same thing.
- **Artifacts**: large model files / per-epoch plots inflate SQLite quickly and are slow to back up. MinIO (S3-compatible) is the right primitive — same API works against AWS S3 if you outgrow MinIO.

For small single-user experiments, the SQLite mode (`mlflow.set_tracking_uri("sqlite:///mlflow.db")` + `mlflow ui --backend-store-uri sqlite:///mlflow.db`) is fine. See `references/sqlite-local.md` in the parent skill.

## Registry URI is automatic

You do **not** need to set `MLFLOW_REGISTRY_URI` separately when using this stack. When tracking URI is HTTP, the registry uses the same backend.

## Troubleshooting

- **Port 5000 conflict on macOS** — AirPlay Receiver uses it. We default to 8000; change `MLFLOW_PORT` in `.env` if 8000 is also taken.
- **`Connection refused` on first boot** — Wait ~30s for the healthcheck. Watch with `docker compose ps` (status should be `healthy` not `starting`).
- **Artifact upload fails with `Access Denied`** — Check `AWS_ACCESS_KEY_ID` / `AWS_SECRET_ACCESS_KEY` are set in your **client environment** (not just the container). The MLflow client signs S3 requests directly to MinIO.

## References

- MLflow tracking server: https://mlflow.org/docs/latest/tracking.html
- Official MLflow Docker image: https://mlflow.org/docs/latest/ml/docker/
- MinIO: https://min.io/docs/minio/linux/index.html
