# dvc-ml-workflow

DVC ([Data Version Control](https://dvc.org/doc), upstream
[treeverse/dvc](https://github.com/treeverse/dvc)) turns a git repo into a
full ML lab: data and model files are versioned out-of-band, pipelines are
declared in `dvc.yaml`, and experiments are run as **ephemeral git commits**
with metrics and plots attached. No tracking server, no separate database —
everything lives in your existing git history.

This skill is opinionated about the parts of DVC that matter for production
ML work: pipelines, queued experiments with metrics auto-bound to commits,
and remote storage. It defers to the official docs at
[dvc.org/doc](https://dvc.org/doc) for everything else and links them inline.

> Iterative was acquired by Treeverse in 2024. `pip install dvc` resolves to
> [github.com/treeverse/dvc](https://github.com/treeverse/dvc) — the link
> redirects from the old `iterative/dvc`.

## What ships

- The full SKILL.md
  ([skills/local/dvc-ml-workflow/SKILL.md](https://github.com/daviddwlee84/agent-skills/blob/main/skills/local/dvc-ml-workflow/SKILL.md))
  with a three-mode mental model (`add` / pipeline / `exp run`), a decision
  workflow, and a gotchas section calibrated to actual production failures.
- Four references — read on demand, not preloaded into context:
    - [`pipelines-and-stages.md`](https://github.com/daviddwlee84/agent-skills/blob/main/skills/local/dvc-ml-workflow/references/pipelines-and-stages.md)
      — `dvc.yaml` schema, `foreach` matrix stages, `frozen`, `always_changed`.
    - [`experiments-and-queue.md`](https://github.com/daviddwlee84/agent-skills/blob/main/skills/local/dvc-ml-workflow/references/experiments-and-queue.md)
      — `dvc exp run --queue`, `dvc queue start --jobs N`, ephemeral-commit
      semantics, `dvc exp apply` / `branch` / `gc`.
    - [`data-and-remotes.md`](https://github.com/daviddwlee84/agent-skills/blob/main/skills/local/dvc-ml-workflow/references/data-and-remotes.md)
      — S3 / GCS / Azure / SSH / GDrive / MinIO setup, credential handling.
    - [`plots-and-metrics.md`](https://github.com/daviddwlee84/agent-skills/blob/main/skills/local/dvc-ml-workflow/references/plots-and-metrics.md)
      — `dvc metrics diff`, plot templates, confusion matrices, VS Code extension.
- Three scripts:
    - [`init-dvc-project.sh`](https://github.com/daviddwlee84/agent-skills/blob/main/skills/local/dvc-ml-workflow/scripts/init-dvc-project.sh)
      — idempotent `dvc init` + `.gitignore` + optional `dvc remote add` +
      drops the templates if missing.
    - [`queue-helper.sh`](https://github.com/daviddwlee84/agent-skills/blob/main/skills/local/dvc-ml-workflow/scripts/queue-helper.sh)
      — agent-friendly wrapper around `dvc queue` with a `grid` subcommand
      that does cartesian-product enqueueing in one call. JSON stdout.
    - [`lint-dvcyaml.sh`](https://github.com/daviddwlee84/agent-skills/blob/main/skills/local/dvc-ml-workflow/scripts/lint-dvcyaml.sh)
      — parse-only validator (`dvc dag --dot`), exits non-zero on schema
      errors without running any stage.
- Three templates in `assets/`:
  [`dvc.yaml.template`](https://github.com/daviddwlee84/agent-skills/blob/main/skills/local/dvc-ml-workflow/assets/dvc.yaml.template),
  [`params.yaml.template`](https://github.com/daviddwlee84/agent-skills/blob/main/skills/local/dvc-ml-workflow/assets/params.yaml.template),
  [`.dvcignore.template`](https://github.com/daviddwlee84/agent-skills/blob/main/skills/local/dvc-ml-workflow/assets/.dvcignore.template).

## Why DVC (in one paragraph)

If you're already on git and want reproducibility without standing up a
tracking server, DVC is hard to beat. The killer feature is that
`dvc exp run --queue` + `dvc queue start --jobs N` runs a parameter sweep
in parallel and **each completed run is a real commit** in `refs/exps/`
with metrics, params, and outputs bundled — no separate database to
correlate against. Promote one to a branch with `dvc exp apply`, garbage-
collect the rest with `dvc exp gc`. The `dvc.yaml` pipeline format also
gives you change-detection (`dvc repro` only re-runs stages whose deps
changed), which `make` can't do for binary inputs.

## Quick start

```bash
# Initialize in current dir (in an existing git repo):
bash skills/local/dvc-ml-workflow/scripts/init-dvc-project.sh \
  --remote s3://my-bucket/dvc-store

# Edit the dvc.yaml + params.yaml templates, then:
dvc repro                                  # run the pipeline once
dvc exp run -S model.lr=1e-3              # try a different LR
dvc exp run --queue -S model.lr=5e-4      # queue a sweep entry
dvc queue start --jobs 4                  # parallel workers
dvc exp show                              # tabular comparison
```

## Cross-references

- Official docs: [dvc.org/doc](https://dvc.org/doc) — always link these,
  don't paraphrase from memory; DVC's CLI surface changes between minor
  versions.
- Upstream repo: [github.com/treeverse/dvc](https://github.com/treeverse/dvc).
- VS Code extension:
  [marketplace.visualstudio.com/items?itemName=Iterative.dvc](https://marketplace.visualstudio.com/items?itemName=Iterative.dvc)
  — adds a live experiments table, plot dashboard with parallel coordinates,
  and `dvc.yaml` schema validation in the editor.
