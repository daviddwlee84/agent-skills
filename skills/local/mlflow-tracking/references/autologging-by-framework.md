# Autologging by framework

> Authoritative source: https://mlflow.org/docs/latest/tracking/autolog.html
>
> **Always check the docs page** for the current support matrix — frameworks
> are added/removed across releases.

`mlflow.autolog()` instruments supported libraries with zero code changes.
Calling it once enables logging for every subsequent `.fit()` / `.train()`
call. Each framework also has a per-library autolog (`mlflow.sklearn.autolog()`,
etc.) for explicit control.

## Universal call (covers everything supported)

```python
import mlflow
mlflow.autolog()                      # detects framework at first .fit()
```

Equivalent to calling all per-framework autologs. Handy for "I don't care,
just log it" scripts.

## Per-framework supported (as of MLflow 3.x)

The following ship with first-party autolog; check the docs page for the current list:

- `mlflow.sklearn.autolog()` — scikit-learn (estimators, pipelines, grid search)
- `mlflow.pytorch.autolog()` — vanilla PyTorch (limited; use Lightning for best coverage)
- `mlflow.pytorch.autolog()` + Lightning — full coverage via `pytorch-lightning`
- `mlflow.tensorflow.autolog()` — TensorFlow / Keras (Keras model.fit, tf.estimator)
- `mlflow.keras.autolog()` — Keras (standalone, including Keras 3 multi-backend)
- `mlflow.xgboost.autolog()` — XGBoost
- `mlflow.lightgbm.autolog()` — LightGBM
- `mlflow.catboost.autolog()` — CatBoost
- `mlflow.statsmodels.autolog()` — statsmodels
- `mlflow.spark.autolog()` — Spark MLlib + Spark DataFrames (datasource autolog)
- `mlflow.fastai.autolog()` — fastai
- `mlflow.gluon.autolog()` — Apache MXNet Gluon (legacy; check current support)
- `mlflow.paddle.autolog()` — PaddlePaddle
- `mlflow.transformers.autolog()` — Hugging Face Transformers (Trainer + Pipelines)
- `mlflow.sentence_transformers` — model logging (no autolog; use `log_model`)
- `mlflow.langchain.autolog()` — LangChain (mostly trace-focused; see llm-tracing.md)
- `mlflow.llama_index.autolog()` — LlamaIndex (trace-focused)
- `mlflow.dspy.autolog()` — DSPy
- `mlflow.openai.autolog()` — OpenAI SDK (trace-focused)
- `mlflow.anthropic.autolog()` — Anthropic SDK (trace-focused)

The **trace-focused** entries are covered in `llm-tracing.md` rather than
this file — they emit traces, not metric/param logs.

## What gets logged (typical)

For traditional ML frameworks:

- **Params**: every constructor arg / hyperparameter
- **Metrics**: training/validation loss per epoch, final metrics
- **Model**: serialized in the framework's native flavor + `pyfunc` wrapper
- **Artifacts**: feature importances, training history, sometimes plots
- **Tags**: framework version, mlflow version, source script

## Per-framework gotchas

### scikit-learn

- Autologs `GridSearchCV` / `RandomizedSearchCV` as nested runs (one per CV split).
  Set `log_models=False` to skip per-split model serialization for huge grids.
- Pipelines are logged as a single composite model.

### PyTorch (vanilla)

- Vanilla PyTorch has no `.fit()` — autolog can't hook training loops.
  You'll get model logging on `mlflow.pytorch.log_model()` but no auto metrics.
  **Use `mlflow.pytorch.autolog()` together with PyTorch Lightning** for full coverage.

### PyTorch Lightning

- Hooks into the trainer; per-epoch metrics, gradients (optional), models, checkpoints.
- `mlflow.pytorch.autolog(log_every_n_epoch=1, log_models=True)` for fine control.

### TensorFlow / Keras

- Keras 3 (multi-backend): use `mlflow.keras.autolog()`.
- TF 2 with `tf.keras`: `mlflow.tensorflow.autolog()` works.
- Don't enable both at once.

### XGBoost / LightGBM / CatBoost

- Logs `eval_set` metrics per boosting round.
- For `xgb.cv` cross-validation, set `log_models=False` to avoid huge cache.

### Hugging Face Transformers

- Hooks into `Trainer`. Pipelines and direct model use are logged via `log_model`.
- Set `MLFLOW_FLATTEN_PARAMS=true` env var to flatten nested config dicts so
  they're searchable in the UI.
- Use `report_to=["mlflow"]` in `TrainingArguments` to make it explicit.

### Spark

- Two distinct things: model autolog (`mlflow.spark.autolog`) for MLlib pipelines,
  and **datasource autolog** which captures input DataFrame paths/queries as
  tags. The second is opt-in: `mlflow.spark.autolog()` enables both.

### fastai

- Hooks into the `Learner.fit` callbacks. v1 and v2 both supported (separate import paths).

### PaddlePaddle / Gluon / MXNet

- Less common; check the latest docs for current support — these have been
  in-and-out across versions.

## Autolog parameters (every framework supports these)

```python
mlflow.sklearn.autolog(
    log_input_examples=True,        # log a small sample of training data as a tag
    log_model_signatures=True,      # log inferred input/output schema
    log_models=True,                # log the model itself
    log_datasets=True,              # log dataset metadata (since MLflow 2.4+)
    disable=False,                  # hard-off switch
    exclusive=False,                # if True, only autolog runs (suppress manual log_X)
    disable_for_unsupported_versions=False,
    silent=False,                   # quieter logs
    extra_tags={"team": "ml-plat"}, # add tags to every autologged run
)
```

## Common pitfalls

- **Calling autolog AFTER `start_run()` / `.fit()`** — Silently no-op. Always
  call autolog at module top, before any training.
- **Mixing manual and auto** — Calling `mlflow.log_metric("loss", x)` while
  autolog is active creates duplicate or conflicting logs. Use `exclusive=True`
  to suppress manual log calls under autolog.
- **Massive log_input_examples on big tabular data** — Toggle off
  (`log_input_examples=False`) for production training jobs to avoid bloating
  the registry.
- **Autolog version mismatch warnings** — MLflow whitelists tested framework
  versions. New framework releases sometimes work but emit warnings; set
  `disable_for_unsupported_versions=True` if you want to be safe.
- **Forgetting `mlflow.set_experiment()`** — Autologged runs land in the
  "Default" experiment, which is messy. Always set a named experiment first.
- **`mlflow.autolog()` (universal) silently misses some frameworks** when the
  framework imports lazily. If you see no logs, call the per-framework autolog
  explicitly.

## Verifying autolog works

Quick smoke test:

```python
import mlflow
from sklearn.ensemble import RandomForestRegressor
from sklearn.datasets import make_regression

mlflow.set_tracking_uri("sqlite:///mlflow.db")
mlflow.set_experiment("autolog-test")
mlflow.sklearn.autolog()

X, y = make_regression()
RandomForestRegressor().fit(X, y)
# Check the UI — should see params, metrics, model, signature.
```

If the run is empty, autolog isn't hooked. Common cause: framework imported
before autolog called, or wrong framework autolog (e.g., `mlflow.tensorflow`
for an `xgboost` model).
