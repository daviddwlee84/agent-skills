# Skills overview

This page indexes the skills bundled in this repo. Local skills are
maintained here; vendored skills are synced from upstream via the
[`vendor.yaml`](https://github.com/daviddwlee84/agent-skills/blob/main/vendor.yaml)
manifest — see [Adding vendor skills](../workflows/adding-vendor-skills.md).

## Local skills

| Skill | One-line | Detailed page |
|---|---|---|
| [`project-knowledge-harness`](project-knowledge-harness.md) | TODO + backlog + pitfalls structure with a bundled validator/init/promote toolkit | [docs](project-knowledge-harness.md) |
| [`quantatitive-factor-researcher`](quantatitive-factor-researcher.md) | Quantitative factor research persona for Python-based strategy work | [docs](quantatitive-factor-researcher.md) |
| [`skill-author`](skill-author.md) | Author new skills following agentskills.io best practices; ships `new-skill.sh` and `lint-skill.sh` | [docs](skill-author.md) |
| [`mkdocs-site-bootstrap`](mkdocs-site-bootstrap.md) | Bootstrap a MkDocs Material site + GitHub Pages deploy; consent-gated with `.skills/preferences.yaml` | [docs](mkdocs-site-bootstrap.md) |
| [`marimo-batch-mlflow`](marimo-batch-mlflow.md) | marimo dual-mode (UI + batch CLI) notebooks with Tyro + MLflow | [docs](marimo-batch-mlflow.md) |
| [`dvc-ml-workflow`](dvc-ml-workflow.md) | DVC pipelines + queued experiments with metrics auto-bound to ephemeral commits; ships init/queue/lint helpers | [docs](dvc-ml-workflow.md) |
| [`mlflow-tracking`](mlflow-tracking.md) | Generic MLflow skill — sqlite + `mlflow ui`, vendored PostgreSQL + MinIO docker stack, LLM tracing, registry, autolog | [docs](mlflow-tracking.md) |

## Vendored skills

| Skill | Upstream |
|---|---|
| [`marimo-notebook`](https://github.com/daviddwlee84/agent-skills/tree/main/skills/vendor/marimo-notebook) | [marimo-team/skills](https://github.com/marimo-team/skills) |

For the rules every local skill follows (layout, naming, scripts,
references), see [Conventions](../conventions.md).
