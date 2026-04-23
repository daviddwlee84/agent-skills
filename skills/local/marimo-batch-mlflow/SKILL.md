---
name: marimo-batch-mlflow
description: Prepare a marimo notebook to run as both an interactive UI and a scheduled batch script, using Tyro for CLI parsing (with dataclass or Pydantic params) and MLflow for experiment tracking. Use when the user wants the same marimo notebook to serve as both a UI for iteration and a CLI script for batch jobs / hyperparameter sweeps, and prefers Tyro over `mo.cli_args()` and MLflow over Weights and Biases. For the upstream W&B + `mo.cli_args()` variant, see marimo-team/skills/skills/marimo-batch.
---

# marimo-batch-mlflow

Opinionated fork of [marimo-team/skills/marimo-batch](https://github.com/marimo-team/skills/tree/main/skills/marimo-batch) that:

1. Uses **[Tyro](https://brentyi.github.io/tyro/)** for CLI parsing (works with `dataclass`, `pydantic.BaseModel`, or `attrs`) instead of `mo.cli_args()` + manual help-table rendering.
2. Uses **[MLflow](https://mlflow.org/)** + **[mlflow-widgets](https://github.com/daviddwlee84/mlflow-widgets)** for experiment tracking instead of Weights and Biases.
3. Keeps the dual-mode pattern (`mo.app_meta().mode == "script"`) so a single `notebook.py` is both the UI for iteration and the entry point for `uv run notebook.py --epochs 50` batch jobs.

## When to use this vs upstream `marimo-batch`

| Concern | upstream `marimo-batch` | this skill |
|---|---|---|
| CLI parsing | `mo.cli_args()` + hand-rolled `rich.Table` for `--help` | `tyro.cli(ModelParams)` — auto `--help`, type coercion, validation |
| Params model | Pydantic `BaseModel` | `dataclass` (primary) or `pydantic.BaseModel` (alternative) |
| Tracking backend | Weights and Biases (`wandb`) | MLflow (`mlflow` + optional `mlflow-widgets` for live charts) |
| Live training UI | none — W&B web dashboard only | `mlflow_widgets.MlflowChart` cell, gated off in script mode |
| Grid launcher | HF Jobs + `WANDB_API_KEY` secret | HF Jobs + `MLFLOW_TRACKING_URI` (+ optional `MLFLOW_TRACKING_TOKEN`) |

Pick this skill when the user has a self-hosted MLflow server (or local `./mlruns` is fine) and prefers strongly-typed CLIs. Pick upstream when the user is already on W&B.

## Dual-mode pattern

The single source-of-truth idiom: branch on `mo.app_meta().mode == "script"` once, build `params` either from a form or from CLI flags, then **let every downstream cell consume `params` regardless of source**.

```python
import marimo as mo

is_script_mode = mo.app_meta().mode == "script"

if is_script_mode:
    params = tyro.cli(ModelParams)
else:
    mo.stop(form.value is None, mo.md("*Submit the form to start training.*"))
    params = ModelParams(**form.value)

# Every cell below uses `params.epochs`, `params.batch_size`, ...
# unaware of which branch produced it.
```

This is what makes the notebook usable as both a UI for fast iteration and a CLI script for sweeps without code duplication.

## Params with dataclass + Tyro (primary)

```python
from dataclasses import dataclass
import tyro

@dataclass
class ModelParams:
    """Model training parameters."""
    epochs: int = 25
    """Number of training epochs."""
    batch_size: int = 32
    """Training batch size."""
    learning_rate: float = 1e-4
    """Learning rate for AdamW."""
    mlflow_experiment: str = "batch-sizes"
    """MLflow experiment name (empty string disables logging)."""
    mlflow_run_name: str | None = None
    """Optional explicit run name; auto-derived from params if None."""

if is_script_mode:
    params = tyro.cli(ModelParams)
```

Tyro derives `--epochs INT`, `--batch-size INT`, etc., from the field names; PEP 257 docstrings under each field become CLI help text. `--help` is generated automatically — no `rich.Table` boilerplate needed.

CLI usage:

```bash
uv run notebook.py --epochs 50 --batch-size 64 --learning-rate 5e-4
uv run notebook.py --help     # auto-generated
```

## Params with Pydantic (alternative)

Tyro v0.8+ supports `pydantic.BaseModel` directly. Trade `dataclass` for Pydantic when you need field-level validators or `@computed_field`:

```python
from pydantic import BaseModel, Field
import tyro

class ModelParams(BaseModel):
    epochs: int = Field(default=25, description="Number of training epochs.")
    batch_size: int = Field(default=32, description="Training batch size.")
    learning_rate: float = Field(default=1e-4, description="Learning rate.")
    mlflow_experiment: str = Field(default="batch-sizes")

params = tyro.cli(ModelParams)  # same call site
```

`Field(description=...)` becomes CLI help. See [`references/params-pydantic.py`](references/params-pydantic.py) for the cell-level diff against the dataclass version.

## MLflow tracking

Wrap the training loop in `mlflow.start_run()`. Default to graceful degradation when `MLFLOW_TRACKING_URI` is unset (MLflow falls back to `./mlruns/`). Disable logging entirely by setting `params.mlflow_experiment = ""`.

```python
import mlflow
import os

tracking_uri = os.environ.get("MLFLOW_TRACKING_URI")
if tracking_uri:
    mlflow.set_tracking_uri(tracking_uri)
if params.mlflow_experiment:
    mlflow.set_experiment(params.mlflow_experiment)

run_ctx = mlflow.start_run(run_name=params.mlflow_run_name) if params.mlflow_experiment else None

if run_ctx:
    mlflow.log_params({k: v for k, v in vars(params).items() if not k.startswith("mlflow_")})

for epoch in range(params.epochs):
    avg_loss = train_one_epoch(...)
    if run_ctx:
        mlflow.log_metric("loss", avg_loss, step=epoch)

if run_ctx:
    mlflow.end_run()
```

Use `with mlflow.start_run(...) as run:` if you don't need conditional disable.

## Live training widget (UI mode only)

In edit mode, embed `mlflow_widgets.MlflowChart` so the user sees the loss curve update live as the training cell runs. Gate it off in script mode (no display surface):

```python
from mlflow_widgets import MlflowChart

if not is_script_mode and params.mlflow_experiment:
    chart = MlflowChart(
        tracking_uri=os.environ.get("MLFLOW_TRACKING_URI", "file:./mlruns"),
        experiment_name=params.mlflow_experiment,
        metric_key="loss",
    )
    widget = mo.ui.anywidget(chart)
    widget
```

For comparing finished runs, swap `MlflowChart` → `MlflowRunTable` or `MlflowParallelCoordinates`. See [mlflow-widgets README](https://github.com/daviddwlee84/mlflow-widgets) for the full surface.

## Environment Variables (EnvConfig)

Keep upstream's `wigglystuff.EnvConfig` pattern but swap secrets:

```python
from wigglystuff import EnvConfig
import mlflow

env_config = mo.ui.anywidget(
    EnvConfig({
        "MLFLOW_TRACKING_URI": lambda u: mlflow.MlflowClient(tracking_uri=u).search_experiments(),
        "MLFLOW_TRACKING_TOKEN": lambda _: True,  # presence-only check
    })
)
env_config if not is_script_mode else None
```

Place the `EnvConfig` cell near the top of the notebook, after imports, before the params form.

## Columns

Preserve upstream's column convention for navigability:

```python
@app.cell(column=0, hide_code=True)
def _(mo):
    mo.md(r"""## Notebook Description""")
    return
```

Recommended layout: `column=0` description + envs, `column=1` params form, `column=2` data setup, `column=3` model, `column=4` training loop + live chart.

## Grid search

For hyperparameter sweeps point users at [`references/grid.py`](references/grid.py). Same contract as upstream:

- Dry run by default: `uv run grid.py` prints sampled combinations.
- `--launch` actually submits jobs.
- `--count N` and `--seed S` control sampling.
- Backend: Hugging Face Jobs via `huggingface_hub.run_uv_job`. Required secrets: `HF_TOKEN` and `MLFLOW_TRACKING_URI` (instead of upstream's `WANDB_API_KEY`).

Swap HF Jobs for Modal / RunPod / local `subprocess.run([...])` by replacing the `run_uv_job` call — the rest of the script (search space, dedup, dry-run formatting) is provider-agnostic.

## Workflow when the user invokes this skill

1. Confirm the user wants the MLflow + Tyro variant (not upstream W&B + `mo.cli_args()`).
2. Ask which params they want exposed as CLI flags.
3. Ask: dataclass or Pydantic? Default to dataclass unless they need validators.
4. Ask: live `MlflowChart` cell yes/no? Default yes.
5. Verify proposed cell-level edits with the user before applying. Keep `@app.cell(column=N, hide_code=True)` markers intact.
6. If they want a sweep, copy `references/grid.py` next to their notebook and update the `SEARCH_SPACE` dict.

## Cross-references

- [`marimo-notebook`](../../vendor/marimo-notebook/SKILL.md) — general marimo authoring patterns (vendored from marimo-team).
- [`anywidget-generator`](../../vendor/anywidget/SKILL.md) — for building the live-chart widget if `mlflow-widgets` doesn't cover the case (vendored).
- Upstream [`marimo-batch`](https://github.com/marimo-team/skills/tree/main/skills/marimo-batch) — the W&B variant.
- [`mlflow-widgets`](https://github.com/daviddwlee84/mlflow-widgets) — anywidget components for MLflow (`MlflowChart`, `MlflowRunTable`, `MlflowParallelCoordinates`).
- [Tyro docs](https://brentyi.github.io/tyro/) — CLI generation reference.
