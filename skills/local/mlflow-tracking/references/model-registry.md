# Model Registry

> Authoritative source: https://mlflow.org/docs/latest/model-registry.html

The registry is MLflow's "model versioning + promotion" layer. It lives on
top of any non-file backend (SQLite, PostgreSQL, MySQL, server).

## Aliases vs Stages — use aliases

**Stages (`None` / `Staging` / `Production` / `Archived`) are deprecated**
since MLflow 2.9. New code MUST use aliases.

| Concern | Stages (deprecated) | Aliases (current) |
|---|---|---|
| Number per model | 4 fixed | Unlimited, user-defined |
| Naming | Fixed | Free-form (`Champion`, `Challenger`, `prod-eu`, ...) |
| Multiple versions per label | No | No (alias points to exactly one version) |
| Recommended for new code | NO | YES |

```python
client = mlflow.MlflowClient()
client.set_registered_model_alias(
    name="my-model",
    alias="Champion",
    version=3,
)

# Load by alias:
model = mlflow.pyfunc.load_model("models:/my-model@Champion")
# Note: @ syntax for aliases, / for explicit version (models:/my-model/3)
```

If you maintain a codebase that still uses `transition_model_version_stage`,
it works (with deprecation warning) but should be migrated:

```python
# OLD:
client.transition_model_version_stage("my-model", version=3, stage="Production")
# NEW:
client.set_registered_model_alias("my-model", "Champion", version=3)
```

## Registering a model

### From a logged run

```python
with mlflow.start_run() as run:
    mlflow.sklearn.log_model(model, "model")
    result = mlflow.register_model(
        model_uri=f"runs:/{run.info.run_id}/model",
        name="my-model",
    )
print(result.version)        # → 1, 2, 3, ...
```

### Inline at log time (shortcut)

```python
mlflow.sklearn.log_model(
    model, "model",
    registered_model_name="my-model",       # creates registered model + new version
)
```

This is concise but couples training to registration. For a clean separation
("only register the best run after a sweep"), use the two-step pattern.

## Loading models

```python
# By alias (preferred):
model = mlflow.pyfunc.load_model("models:/my-model@Champion")

# By explicit version:
model = mlflow.pyfunc.load_model("models:/my-model/3")

# Latest version (avoid in production — no traceability):
model = mlflow.pyfunc.load_model("models:/my-model/latest")

# Flavor-specific (gives you the original object, not a pyfunc wrapper):
model = mlflow.sklearn.load_model("models:/my-model@Champion")
```

`pyfunc` is the universal wrapper — works for any flavor. Flavor-specific
loaders return the original framework object (sklearn estimator, torch
module, etc.).

## Champion / Challenger pattern

```python
# Promote a new candidate:
client.set_registered_model_alias("my-model", "Challenger", version=4)

# A/B test in production code:
champ = mlflow.pyfunc.load_model("models:/my-model@Champion")
chall = mlflow.pyfunc.load_model("models:/my-model@Challenger")

if random.random() < 0.05:                  # 5% to challenger
    pred = chall.predict(X)
else:
    pred = champ.predict(X)

# After validation, promote:
client.set_registered_model_alias("my-model", "Champion", version=4)
client.delete_registered_model_alias("my-model", "Challenger")
```

## Tags and descriptions

Tags are searchable; descriptions are markdown-rendered in the UI.

```python
client.set_registered_model_tag("my-model", "team", "ml-platform")
client.set_model_version_tag("my-model", "3", "validated_on", "2025-01-15")

client.update_registered_model("my-model", description="Customer churn predictor.")
client.update_model_version("my-model", "3", description="Trained on Q4 data.")
```

## Searching the registry

```python
for mv in client.search_model_versions("name='my-model' AND tag.team='ml-platform'"):
    print(mv.version, mv.aliases, mv.tags)
```

## Webhooks (server backend only)

Trigger external systems on registry events (new version registered, alias set):

```python
from mlflow.entities.webhook import WebhookEvent

client.create_webhook(
    name="notify-deploy",
    url="https://hooks.slack.com/services/...",
    events=[WebhookEvent.MODEL_VERSION_TAG_SET, WebhookEvent.MODEL_VERSION_ALIAS_CREATED],
)
```

Webhooks are server-side; SQLite mode does NOT support them. Useful for
hooking into CI/CD ("on alias=Champion → trigger deploy").

## Common pitfalls

- **Trying to register from `file:./mlruns`** — Raises. Switch to SQLite or a server.
- **`models:/my-model/latest` in production** — "Latest" silently shifts under
  you. Use an alias for any pinned reference.
- **Two aliases pointing at the same version** — Allowed, but confusing during
  rollback. Conventionally each alias points at a distinct version.
- **Deleting a registered model deletes all versions** — `client.delete_registered_model("name")`
  is irreversible and removes all underlying version metadata. The model
  artifacts in S3/MinIO remain (orphaned) and need manual cleanup.
- **Loading a model with missing dependencies** — MLflow logs a `requirements.txt`
  with each model. Use `mlflow.models.predict --env-manager virtualenv` for
  hermetic loading, or `pip install -r <model_path>/requirements.txt` first.
- **Loading on a different platform** — Pickled sklearn / torch models are
  architecture-sensitive. For cross-platform use, prefer ONNX export or
  retrain on the target platform.

## When to skip the registry

If your project has only one model and you never re-deploy, skip it. Just
load by `runs:/<run_id>/model` directly. The registry's value is in
**versioning + promotion**, which only matters when you have more than one
candidate version.
