# SQLite local mode (recommended for solo experiments)

> Authoritative source: https://mlflow.org/docs/latest/tracking/backend-stores.html

The "DVC-like but more flexible" sweet spot: one local file (`mlflow.db`), full
UI, model registry support, no Docker. Trade-off: serialized writes — single-user only.

## Setup

```bash
# In your project root:
bash skills/local/mlflow-tracking/scripts/init-mlflow-sqlite.sh
```

What the script does (you can also do it manually):

1. Touches `mlflow.db` if missing
2. Adds `mlflow.db`, `mlruns/`, `mlartifacts/` to `.gitignore`
3. Prints the tracking URI and the `mlflow ui` command

## In your code

```python
import mlflow

mlflow.set_tracking_uri("sqlite:///mlflow.db")        # 3 slashes = relative path
# mlflow.set_tracking_uri("sqlite:////abs/path.db")   # 4 slashes = absolute path
mlflow.set_experiment("my-project")

with mlflow.start_run():
    mlflow.log_params({"lr": 1e-3})
    mlflow.log_metric("acc", 0.92)
```

Or via env var (preferred):

```bash
export MLFLOW_TRACKING_URI=sqlite:///mlflow.db
```

## Launching the UI — the #1 gotcha

`mlflow ui` does **not** read `MLFLOW_TRACKING_URI` automatically. You must
pass `--backend-store-uri` matching what your code uses, or you'll see an
empty UI (because it's looking at the default `./mlruns/` instead of your DB).

```bash
mlflow ui --backend-store-uri sqlite:///mlflow.db --port 5001
```

The init script prints this exact line. **Don't paraphrase.**

Why port 5001? Because macOS uses 5000 for AirPlay Receiver. On Linux you
can use 5000.

## Where do artifacts go?

By default, artifacts (models, plots, anything `log_artifact`'d) land in
`./mlartifacts/<experiment_id>/<run_id>/artifacts/`. SQLite stores only
metadata (params, metrics, tags, run lifecycle).

To put artifacts elsewhere:

```python
mlflow.create_experiment("my-project", artifact_location="s3://my-bucket/mlartifacts")
```

Or set globally with `mlflow ui --artifacts-destination s3://...`. For most
solo work, the local `mlartifacts/` directory is fine — just remember to
`.gitignore` it.

## Migrating to a server later

A SQLite database can be pointed at by an MLflow server too:

```bash
mlflow server \
  --backend-store-uri sqlite:///mlflow.db \
  --artifacts-destination ./mlartifacts \
  --host 0.0.0.0 --port 8000
```

But once you need parallelism, **migrate to PostgreSQL**. SQLite is fine for
~10k runs and 1 writer. Beyond that, expect `database is locked` errors.

The migration path:

1. `pip install mlflow[extras] psycopg2-binary`
2. Spin up the Docker stack from `assets/docker-compose-stack/`
3. Use `mlflow.MlflowClient` to copy runs from the SQLite DB to the new server
   (no built-in migration tool; loop over `client.search_runs()` and re-create
   on the new endpoint, or accept losing history)

In practice, most users start fresh on the new server.

## Backup

Just copy the file:

```bash
cp mlflow.db mlflow.db.$(date +%Y%m%d).bak
# or rsync mlflow.db + mlartifacts/ to backup storage
```

## Common pitfalls

- **Empty UI with no error** — Used the wrong `--backend-store-uri`. Check it
  matches your code's `set_tracking_uri()` exactly.
- **`sqlite3.OperationalError: database is locked`** — More than one process
  is writing. Time to migrate to PostgreSQL.
- **Run shows up in code but not in UI** — Different working directory.
  `sqlite:///mlflow.db` is relative; if your script runs in a subdir, it
  creates a new DB there. Use an absolute path or set `MLFLOW_TRACKING_URI`
  to an absolute URI.
- **`mlflow ui` opens but model registry tab is empty** — Registry exists
  per-backend. Make sure the same `--backend-store-uri` is used by the UI
  and the code that called `register_model`.
