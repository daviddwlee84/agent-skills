# Pipelines and stages (`dvc.yaml`)

> Authoritative source: https://dvc.org/doc/user-guide/pipelines and https://dvc.org/doc/user-guide/project-structure/dvcyaml-files
>
> When in doubt, fetch the latest doc — the schema gains fields between minor versions.

## Anatomy of a stage

```yaml
# dvc.yaml
stages:
  train:
    cmd: python src/train.py            # the command DVC runs
    deps:                               # inputs (-d on CLI)
      - src/train.py
      - data/features
    params:                             # subset of params.yaml this stage cares about
      - model.lr
      - model.epochs
      - train.batch_size
    outs:                               # outputs (-o on CLI) — cached
      - models/best.pt
    metrics:                            # outputs (-M on CLI) — cached + tracked as metrics
      - metrics.json:
          cache: false                  # if you also want it in git
    plots:                              # outputs (--plots on CLI) — cached + tracked as plot data
      - plots.csv:
          cache: false
          x: epoch
          y: loss
```

The four output kinds:

| Kind | Use for | CLI flag |
|---|---|---|
| `outs` | Models, intermediate artifacts | `-o` |
| `metrics` | Scalar metrics (JSON/YAML) | `-M` (cached) / `--metrics-no-cache` |
| `plots` | Time-series / per-epoch data (CSV/JSON) | `--plots` (cached) / `--plots-no-cache` |
| `outs_persist` | Outputs that should NOT be removed before re-run (logs, checkpoints) | `--outs-persist` |

## Generating stages: prefer `dvc stage add` over hand-editing

`dvc.yaml` is technically hand-editable, but the schema is fiddly. Use `dvc stage add` for the first version, then iterate by editing:

```bash
dvc stage add -n featurize \
  -d src/featurize.py -d data/raw \
  -o data/features \
  python src/featurize.py
```

Re-running `dvc stage add -n <name> ...` with `--force` overwrites the existing stage.

## Matrix stages with `foreach`

For grids that should be **declared in the pipeline** (not enqueued ad-hoc):

```yaml
stages:
  train:
    foreach:
      small:  { lr: 1e-4, batch: 16 }
      medium: { lr: 5e-4, batch: 32 }
      large:  { lr: 1e-3, batch: 64 }
    do:
      cmd: python src/train.py --lr ${item.lr} --batch ${item.batch}
      deps:
        - src/train.py
        - data/features
      outs:
        - models/${key}.pt
      metrics:
        - metrics-${key}.json:
            cache: false
```

`${key}` interpolates the dict key (`small`/`medium`/`large`); `${item.field}` interpolates the value. Use `foreach` when the grid is part of the canonical pipeline; use `dvc exp run --queue` (see `experiments-and-queue.md`) when it's an ad-hoc sweep.

## `vars`, `wdir`, `frozen`, `always_changed`

- **`vars`**: import variables from external files into stage interpolation. `vars: [params.yaml, configs/extra.yaml]`.
- **`wdir`**: run the stage's `cmd` from a different directory. Useful for monorepos.
- **`frozen: true`**: skip this stage in `dvc repro` even if deps changed (e.g., expensive pretraining you've already done). Unfreeze with `dvc unfreeze`.
- **`always_changed: true`**: always re-run this stage regardless of dep hashes (e.g., a stage that pulls fresh data from an API).

## `dvc repro` semantics

`dvc repro` is the "make" of DVC. It walks the DAG and re-runs only stages whose:

- `deps` files changed (md5 differs from `dvc.lock`), or
- `params` (the subset listed in this stage) changed in `params.yaml`, or
- `cmd` changed in `dvc.yaml`, or
- `always_changed: true`.

If nothing changed, `dvc repro` is a no-op and exits 0. Force with `dvc repro -f` (re-run everything) or `dvc repro -s <stage>` (single stage, downstream-only).

After every `dvc repro`, **`dvc.lock` is regenerated**. Commit it.

## Inspecting the DAG

```bash
dvc dag                              # ASCII art of the pipeline
dvc dag --dot | dot -Tpng -o dag.png # graphviz render
dvc dag <stage>                      # only ancestors of <stage>
```

`dvc dag --dot` is also the cheapest way to **validate `dvc.yaml` syntax without running anything** — it parses but does not execute. The bundled `scripts/lint-dvcyaml.sh` wraps this.

## The 5 most common errors

1. **`Stage 'X' is missing the field 'cmd'`** — every stage needs `cmd`. There is no implicit "do nothing" stage.
2. **`Output 'X' is specified more than once`** — two stages can't both write the same file. Split or merge them.
3. **`Cyclic dependency detected`** — stage A's `outs` are in stage B's `deps`, and vice versa. Re-think the DAG.
4. **`Parameter 'X' not found in 'params.yaml'`** — the param key under `params:` must exist in `params.yaml`. Typos here fail fast.
5. **`The following untracked files would be overwritten by checkout`** — happens when `outs` overlap with files that were already `git add`ed. Either `git rm --cached <file>` or remove from `outs`.
