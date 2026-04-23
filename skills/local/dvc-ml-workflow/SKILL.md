---
name: dvc-ml-workflow
description: Set up and operate a DVC (Data Version Control) workflow for ML projects — `dvc init`, `dvc.yaml` pipelines, `params.yaml`, `dvc exp run --queue` for parallel sweeps with metrics auto-bound to ephemeral git commits, and remote storage (S3/SSH/GDrive). Use whenever the user wants reproducible ML pipelines, data/model versioning that lives alongside git, parameter sweeps without standing up a tracking server, queued/parallel experiment execution, or asks about `dvc.yaml` / `dvc exp run` / `dvc queue` / `params.yaml` / `dvc add` / `dvc push` / `.dvc/cache`. Always references the official docs at https://dvc.org/doc and the upstream repo https://github.com/treeverse/dvc (Iterative was acquired by Treeverse in 2024 — `pip install dvc` resolves to this repo).
---

# DVC ML Workflow

DVC turns a git repo into a full ML lab: data and model files are versioned out-of-band (in a cache + remote), pipelines are declared in `dvc.yaml`, and experiments are run as ephemeral git commits with metrics and plots attached. No tracking server, no separate database — everything lives in your existing git history.

This skill is opinionated about **the parts of DVC that matter for production ML work**: pipelines, queued experiments, metrics/commit binding, and remotes. It defers to the official docs at https://dvc.org/doc for everything else and links them inline so the agent always pulls the latest guidance.

## When to use

- User wants reproducible ML pipelines without a tracking server (`mlflow`, `wandb`, etc.)
- User mentions `dvc.yaml`, `params.yaml`, `dvc exp run`, `dvc queue`, `dvc push`, `.dvc/cache`
- User wants to do a hyperparameter sweep / grid search and have each run land as a separate commit with metrics
- User wants to version a dataset or model file too large for git
- User asks "how do I make my training reproducible" and is already on git
- User wants `mlflow ui`-style experiment comparison but **doesn't want to run a server** (DVC's `dvc exp show` + VS Code extension fills that role)

## When NOT to use

- User wants a hosted experiment dashboard with multi-user collaboration → use `mlflow-tracking` skill
- User wants LLM trace observability (spans, prompts, token costs) → DVC has no story here; use `mlflow-tracking`
- User just needs `git lfs` for a few large files → DVC is overkill; recommend `git lfs`
- User has an existing `mlflow` workflow and is happy with it → don't push DVC unless they ask

## Authoritative sources (always link these, don't paraphrase from memory)

- Docs root: https://dvc.org/doc
- Command reference: https://dvc.org/doc/command-reference
- User guide: https://dvc.org/doc/user-guide
- Upstream repo: https://github.com/treeverse/dvc (formerly `iterative/dvc`; redirects)
- PyPI: https://pypi.org/project/dvc/

When you're unsure of a flag, syntax, or behavior, **fetch the relevant doc page** rather than guessing — DVC's CLI surface changes between minor versions.

## Core mental model

Three orthogonal things, often confused:

| DVC concept | Analogy | What it does |
|---|---|---|
| `dvc add <file>` | `git lfs track` | Snapshots a single file/dir into the cache, writes a `.dvc` pointer file (which **is** committed to git) |
| `dvc.yaml` (stages) | `Makefile` | Declares pipeline stages with dependencies and outputs; `dvc repro` re-runs only stages whose inputs changed |
| `dvc exp run` | `git commit` for experiments | Runs the pipeline once with optional param overrides, captures metrics + outputs as an **ephemeral commit** |

The non-obvious bit: `dvc exp run` builds on top of `dvc.yaml`. You don't choose between "use pipelines" and "run experiments" — you write the pipeline once, then launch many experiments against it.

## Workflow

### 1. Initialize the project

Use the bundled helper (handles `.gitignore`, sample files, optional remote):

```bash
bash skills/local/dvc-ml-workflow/scripts/init-dvc-project.sh
# or with a remote:
bash skills/local/dvc-ml-workflow/scripts/init-dvc-project.sh --remote s3://my-bucket/dvc-store
```

Manual equivalent (only do this if the helper doesn't fit):

```bash
dvc init                              # creates .dvc/, .dvcignore
git add .dvc .dvcignore
git commit -m "Initialize DVC"
```

For a sub-project inside a monorepo that already has its own `.git`, use `dvc init --subdir`. See [Gotchas](#gotchas).

### 2. Track data and models

```bash
dvc add data/raw/             # snapshot a directory
dvc add models/best.pt        # snapshot a single model file
git add data/raw.dvc models/best.pt.dvc .gitignore
git commit -m "Track raw data and best model"
```

The `.dvc` files are tiny pointers (md5 + path). The actual bytes go to `.dvc/cache/`. **Never** `git add` anything inside `.dvc/cache/` — it's gitignored automatically and would defeat the purpose.

### 3. Define a pipeline (`dvc.yaml`)

Use `params.yaml` for hyperparameters. Use `dvc stage add` to declare stages — never hand-edit `dvc.yaml` from scratch unless you've already used `dvc stage add` enough times to know the schema.

```bash
dvc stage add -n featurize \
  -d src/featurize.py -d data/raw \
  -o data/features \
  python src/featurize.py

dvc stage add -n train \
  -d src/train.py -d data/features -p model.lr,model.epochs \
  -o models/best.pt \
  -M metrics.json --plots-no-cache plots.csv \
  python src/train.py
```

The `-M` flag marks a file as a **metrics file** (auto-bound to the experiment commit). `--plots-no-cache` marks a file as a plot source (rendered by `dvc plots show`).

For schema details and `foreach` matrix stages, **read** `references/pipelines-and-stages.md`.

### 4. Run experiments (the queue is the killer feature)

For a single run:

```bash
dvc exp run                           # uses current params.yaml
dvc exp run -S model.lr=1e-3          # override one param
dvc exp run -S 'model.lr=range(1e-4,1e-2,3)'  # NOT valid — see queue below
```

For a **sweep**, queue + start workers:

```bash
# Enqueue a grid (each -S adds one experiment to the queue):
dvc exp run --queue -S model.lr=1e-4
dvc exp run --queue -S model.lr=5e-4
dvc exp run --queue -S model.lr=1e-3

# Start 3 parallel workers — they each pick one queued experiment:
dvc queue start --jobs 3

# Watch progress:
dvc queue status
dvc queue logs <task-id>             # if one fails

# When done:
dvc exp show                          # tabular view of all experiments
```

Each completed experiment is an **ephemeral commit** in `refs/exps/...`. Metrics, params, and outputs are bundled with it. Promote one to a real commit with `dvc exp apply <exp-name>` then `git commit`.

For grids, queue helpers, and ephemeral-vs-real commit semantics, **read** `references/experiments-and-queue.md`.

### 5. Push artifacts to a remote

```bash
dvc remote add -d origin s3://my-bucket/dvc-store    # -d = default
dvc push                                             # upload cache to remote
git push                                             # share the .dvc pointers
```

Anyone who clones can `dvc pull` to get the actual bytes. For S3 / GCS / Azure / SSH / GDrive specifics and credential handling, **read** `references/data-and-remotes.md`.

### 6. Compare and visualize

```bash
dvc exp show                          # table of all experiments
dvc exp show --csv | column -t -s,    # human-readable
dvc metrics show                      # current workspace metrics
dvc metrics diff HEAD~1               # compare against last commit
dvc plots show                        # render plots from --plots files
dvc plots diff HEAD~1                 # overlay current vs prior plots
```

For plot templates (Vega-Lite), confusion matrices, and the VS Code extension, **read** `references/plots-and-metrics.md`.

## Available scripts

- **`scripts/init-dvc-project.sh`** — Idempotent project init. `dvc init` + `.gitignore` for `.dvc/cache/` + optional `dvc remote add` + drops the `dvc.yaml` / `params.yaml` / `.dvcignore` templates from `assets/` if missing.
  - Flags: `--remote URL`, `--subdir`, `--force`, `--dry-run`, `--help`
- **`scripts/queue-helper.sh`** — Wraps `dvc queue` subcommands with structured JSON stdout (one object per task) so an agent can grep/filter task status without parsing tabular output.
  - Subcommands: `enqueue PARAM=VAL,...`, `start --jobs N`, `status`, `logs TASK_ID`
  - Flags: `--help`, `--json` (default for `status`)
- **`scripts/lint-dvcyaml.sh`** — Validates `dvc.yaml` by running `dvc dag --dot` (parse-only, no execution). Exits non-zero with the parse error if the schema is broken.
  - Flags: `--help`

## Bundled assets

- `assets/dvc.yaml.template` — Minimal 2-stage pipeline (`featurize` → `train`) with metrics and plots wired up correctly.
- `assets/params.yaml.template` — Nested params for `data` / `model` / `train` sections (the `-S model.lr=...` override syntax keys off this nesting).
- `assets/.dvcignore.template` — Sensible defaults: ignore notebooks, scratch dirs, `__pycache__`, etc.

## Reference files

- `references/pipelines-and-stages.md` — Read **when** writing or debugging `dvc.yaml`: stage schema, `foreach`, `vars`, `wdir`, `frozen`, `always_changed`, and the difference between `-d` / `-o` / `-M` / `--plots`.
- `references/experiments-and-queue.md` — Read **when** the user wants sweeps, parallel runs, or asks how metrics get bound to commits. Covers `dvc exp run --queue`, `dvc queue start --jobs`, `dvc exp apply` / `branch` / `remove` / `gc`, and ephemeral-commit semantics.
- `references/data-and-remotes.md` — Read **when** setting up `dvc remote` or troubleshooting `dvc push` / `dvc pull`. Covers S3, SSH, GDrive, Azure, GCS, MinIO (S3-compatible), credentials via env / `dvc remote modify --local`.
- `references/plots-and-metrics.md` — Read **when** the user asks about visualization, dashboards, or VS Code integration. Covers `dvc plots show / diff`, custom Vega-Lite templates, confusion matrices, and `dvc.api.metrics_show()` for programmatic access.

## Gotchas

- **`dvc init` fails inside an existing repo's subdirectory** unless you pass `--subdir`. Symptom: `ERROR: '.git' or '.hg' directory not found`. The helper script handles this — manually, do `dvc init --subdir`.
- **`dvc exp run --queue` only enqueues; it does not run.** Until you call `dvc queue start`, queued experiments sit idle. The agent will sometimes report "experiment finished" because the enqueue succeeded — verify with `dvc queue status`.
- **`dvc.lock` MUST be committed.** It records the exact md5s of inputs/outputs for each stage. If you `.gitignore` it, `dvc repro` becomes non-deterministic between machines. Conversely, **`.dvc/cache/` MUST NOT be committed** (it's the actual data — that goes to the remote).
- **Metrics file format matters.** `-M metrics.json` expects a flat JSON object (`{"acc": 0.91, "loss": 0.3}`) or a one-level-nested one. YAML works too. Free-form text won't render in `dvc exp show`.
- **`dvc push` silently succeeds if the remote is misconfigured but credentials are missing** for some backends — it just reports "0 files pushed" without an error code in older versions. Always verify with `dvc status -c` (cloud status) after the first push from a new machine.
- **Param overrides use dot-notation against `params.yaml` keys.** `-S lr=1e-3` only works if `lr` is at the top level. If you nested it under `model:`, you must use `-S model.lr=1e-3`.
- **macOS port 8080 / Iterative Studio**: if the user mentions Iterative Studio, note that it's now a separate Treeverse-managed product, not bundled with `dvc` itself. Don't conflate the two.
- **`dvc queue start` runs jobs in the background.** Closing your terminal does NOT kill them (they're detached). Use `dvc queue kill <task-id>` to stop one.
