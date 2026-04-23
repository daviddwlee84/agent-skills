# marimo-batch-mlflow

Opinionated fork of [marimo-team/skills/marimo-batch](https://github.com/marimo-team/skills/tree/main/skills/marimo-batch)
that swaps three things:

| Concern | upstream `marimo-batch` | this skill |
|---|---|---|
| CLI parsing | `mo.cli_args()` + hand-rolled `rich.Table` for `--help` | `tyro.cli(ModelParams)` — auto `--help`, type coercion, validation |
| Params model | Pydantic `BaseModel` | `dataclass` (primary) or `pydantic.BaseModel` (alternative) |
| Tracking | Weights and Biases | MLflow (`mlflow` + optional [`mlflow-widgets`](https://github.com/daviddwlee84/mlflow-widgets) for live charts) |

Pick this skill when the user has (or is happy with) MLflow and prefers
strongly-typed CLIs. Pick upstream when the user is already on W&B.

## What ships

- The full SKILL.md
  ([skills/local/marimo-batch-mlflow/SKILL.md](https://github.com/daviddwlee84/agent-skills/blob/main/skills/local/marimo-batch-mlflow/SKILL.md))
  with a decision matrix vs upstream, a dual-mode pattern recipe, and
  cell-level templates for params / EnvConfig / training loop / live chart.
- A reference notebook
  ([starting-point.py](https://github.com/daviddwlee84/agent-skills/blob/main/skills/local/marimo-batch-mlflow/references/starting-point.py))
  — full PyTorch training notebook with dataclass params, Tyro CLI, MLflow
  logging, and a live `MlflowChart` cell that's gated off in script mode.
- A Pydantic-variant snippet
  ([params-pydantic.py](https://github.com/daviddwlee84/agent-skills/blob/main/skills/local/marimo-batch-mlflow/references/params-pydantic.py))
  — only the params cell differs; rest of the notebook is identical.
- A grid-search launcher
  ([grid.py](https://github.com/daviddwlee84/agent-skills/blob/main/skills/local/marimo-batch-mlflow/references/grid.py))
  — randomized sweeps via Hugging Face Jobs with MLflow secrets injected.
  Dry-run by default; `--launch` actually submits.

## Dual-mode pattern (the core idiom)

```python
import marimo as mo
import tyro

is_script_mode = mo.app_meta().mode == "script"

if is_script_mode:
    params = tyro.cli(ModelParams)        # CLI flags
else:
    mo.stop(form.value is None, mo.md("*Submit form to start.*"))
    params = ModelParams(**form.value)    # UI form

# Every cell below uses `params.epochs`, `params.batch_size`, ...
# unaware of which branch produced it.
```

Same notebook serves as the UI for fast iteration **and** the entry point
for `uv run notebook.py --epochs 50` batch jobs. No code duplication.

## Why a fork instead of vendoring

The upstream `marimo-batch` skill is opinionated towards W&B and
`mo.cli_args()`. Vendoring + patching would be clobbered every sync; a
local fork in `skills/local/` keeps the divergence safe and explicit. The
SKILL.md cross-references upstream so users can pick the right variant.

## Cross-references

- Upstream [`marimo-batch`](https://github.com/marimo-team/skills/tree/main/skills/marimo-batch)
  — the W&B variant; pick this if the user is already on W&B.
- [`marimo-notebook`](https://github.com/daviddwlee84/agent-skills/blob/main/skills/vendor/marimo-notebook/SKILL.md)
  — general marimo authoring patterns (vendored from marimo-team).
- [`anywidget-generator`](https://github.com/daviddwlee84/agent-skills/blob/main/skills/vendor/anywidget/SKILL.md)
  — for building custom live-chart widgets if `mlflow-widgets` doesn't
  cover the case (vendored from marimo-team).
- [`mlflow-widgets`](https://github.com/daviddwlee84/mlflow-widgets) —
  the anywidget-based MLflow chart/table/parallel-coordinates components
  used in `starting-point.py`'s live-chart cell.
- [Tyro docs](https://brentyi.github.io/tyro/) — CLI generation reference;
  supports dataclass, Pydantic, attrs.
