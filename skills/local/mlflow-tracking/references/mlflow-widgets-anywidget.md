# mlflow-widgets (anywidget for MLflow)

> Source: https://github.com/daviddwlee84/mlflow-widgets
> Demo: https://daviddwlee84.github.io/mlflow-widgets/

A small [anywidget](https://anywidget.dev/) library that renders MLflow data
inside marimo / Jupyter cells. Use it when you want **live charts in a
notebook** without spinning up the full `mlflow ui`.

## When to use

- You're iterating in marimo or Jupyter and want a live training-curve chart
  next to your training cell
- You want a quick comparison of a few runs without context-switching to a
  separate browser tab
- You're embedding MLflow viz into a custom marimo dashboard

## When NOT to use

- You want full search / filter / parallel coordinates → use `mlflow ui`
- You want the model registry tab → use `mlflow ui`
- You're not in a notebook → use `mlflow ui`

## Install

```bash
pip install mlflow-widgets
# or
uv add mlflow-widgets
```

Works with marimo and Jupyter (anywidget bridges both).

## Quick start

```python
import mlflow
from mlflow_widgets import MlflowChart

mlflow.set_tracking_uri("sqlite:///mlflow.db")
# (point at your active MLflow backend — same URI you'd use for mlflow ui)

MlflowChart(experiment_name="my-project", metric="val_loss")
```

The widget reads runs from the configured tracking URI and renders the
metric over time, auto-refreshing when new metric values land.

## Common patterns

### Live training curve next to the trainer cell (marimo)

```python
# Cell 1 — start training (background or sync):
with mlflow.start_run() as run:
    for epoch in range(50):
        ...
        mlflow.log_metric("val_loss", loss, step=epoch)

# Cell 2 — render the curve, auto-refreshes:
MlflowChart(run_id=run.info.run_id, metric="val_loss")
```

### Compare a small set of runs

```python
runs = mlflow.search_runs(experiment_names=["my-project"], max_results=5)
MlflowChart(run_ids=runs.run_id.tolist(), metric="val_acc")
```

### Multiple charts in one cell (marimo grid)

```python
import marimo as mo

mo.hstack([
    MlflowChart(experiment_name="my-project", metric="train_loss"),
    MlflowChart(experiment_name="my-project", metric="val_loss"),
])
```

## Configuration

The widget honors `MLFLOW_TRACKING_URI` (env var) and the URI set via
`mlflow.set_tracking_uri()` in the same kernel. For a remote server, ensure
your notebook environment has the same auth env vars:

```bash
export MLFLOW_TRACKING_URI=http://your-server:8000
# AWS_ACCESS_KEY_ID / AWS_SECRET_ACCESS_KEY too if you want to load artifacts
```

## Common pitfalls

- **Widget renders empty** — Tracking URI mismatch. Run `mlflow.get_tracking_uri()`
  in another cell to confirm what the widget sees.
- **No live updates** — The widget polls; long polling intervals are normal.
  Refresh manually or restart the cell after a long training run.
- **Doesn't show in non-notebook environments** — anywidget requires Jupyter
  / marimo / VSCode notebook. Plain Python script will get an `<HTMLWidget>`
  repr but no rendering.
- **Version compatibility** — `mlflow-widgets` tracks the MLflow REST API.
  If the widget breaks after an MLflow upgrade, check the widget's GitHub
  issues / pin to a known-good MLflow version.

## Authoritative source

The widget is small enough that the README + demo site are the full docs.
For API changes and embedding examples, **read the README** at the GitHub
URL above — don't paraphrase from this file as the canonical reference.
