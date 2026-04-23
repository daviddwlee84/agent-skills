# Plots and metrics

> Authoritative source: https://dvc.org/doc/user-guide/experiment-management/visualizing-plots and https://dvc.org/doc/command-reference/plots and https://dvc.org/doc/command-reference/metrics

## Metrics: scalar values bound to commits

A metrics file is any JSON or YAML file marked with `-M` / `--metrics-no-cache` in `dvc stage add`, or listed under `metrics:` in `dvc.yaml`.

### Recommended format

```json
{
  "accuracy": 0.912,
  "loss": 0.231,
  "f1": 0.886
}
```

Or one level of nesting (rendered as `train.loss`, `val.loss`):

```json
{
  "train": {"loss": 0.18, "acc": 0.94},
  "val":   {"loss": 0.23, "acc": 0.91}
}
```

Avoid arrays at the top level — they don't render in `dvc exp show`.

### Reading metrics

```bash
dvc metrics show                       # current workspace
dvc metrics show --all-commits         # every commit on current branch
dvc metrics diff HEAD~1                # workspace vs HEAD~1
dvc metrics diff main feature-branch   # any two refs
dvc metrics diff --md                  # markdown table (good for PR comments)
dvc metrics diff --json                # parseable
```

Programmatic:

```python
import dvc.api
metrics = dvc.api.metrics_show()       # dict from current commit
metrics_old = dvc.api.metrics_show(rev="HEAD~1")
```

## Plots: time-series, confusion matrices, custom visualizations

A plot file is CSV/JSON/YAML with per-step or per-class data, marked with `--plots` / `--plots-no-cache` or listed under `plots:` in `dvc.yaml`.

### Default rendering

CSV with a header row, x-axis specified:

```csv
epoch,train_loss,val_loss
1,0.85,0.91
2,0.62,0.74
3,0.41,0.53
```

```yaml
# dvc.yaml
plots:
  - plots.csv:
      x: epoch
      y: [train_loss, val_loss]      # multiple series
      title: "Training curves"
```

```bash
dvc plots show                         # opens HTML report in browser
dvc plots show plots.csv               # specific file
dvc plots diff HEAD~1                  # overlay current vs HEAD~1
dvc plots diff exp-a exp-b             # compare two experiments
```

### Confusion matrices

```yaml
plots:
  - confusion.json:
      template: confusion
      x: actual
      y: predicted
```

`confusion.json` should be:

```json
[
  {"actual": "cat", "predicted": "cat"},
  {"actual": "dog", "predicted": "cat"},
  ...
]
```

DVC ships several built-in templates: `default`, `linear`, `scatter`, `confusion`, `confusion_normalized`, `bar_horizontal_sorted`, `bar_horizontal`. List them with `dvc plots templates`.

### Custom Vega-Lite templates

For anything else, drop a Vega-Lite spec JSON into `.dvc/plots/` and reference it:

```yaml
plots:
  - my-data.csv:
      template: my-template          # looks for .dvc/plots/my-template.json
```

The placeholders `<DVC_METRIC_X>`, `<DVC_METRIC_Y>`, `<DVC_METRIC_DATA>` get substituted at render time.

## Comparing across many experiments

After a sweep:

```bash
dvc exp show                           # table form
dvc plots diff $(dvc exp list --names-only --rev HEAD)
# overlays plots from every experiment derived from HEAD
```

For a parallel-coordinates view of params vs metrics across all experiments, use the **VS Code DVC extension** (see below) — the CLI doesn't render parallel coordinates natively.

## VS Code extension

Install: `marketplace.visualstudio.com/items?itemName=Iterative.dvc`

What it adds:

- Live experiments table (auto-refreshes)
- Plot dashboard with side-by-side comparison and parallel coordinates
- One-click `dvc exp run` / `apply` / `branch`
- `dvc.yaml` schema validation in the editor
- Tree view of pipelines and stages

The extension uses the local `dvc` CLI under the hood, so any version-specific behavior matches your CLI.

## HTML report

`dvc plots show` and `dvc plots diff` produce a static HTML file by default (path printed to stdout). For CI pipelines, capture and upload it as a build artifact:

```bash
dvc plots diff main HEAD --out plots.html
# then upload plots.html in CI
```

## Common pitfalls

- **Plot data file is checked into git AND tracked as `plots:` cache** — DVC complains about double-tracking. Either set `cache: false` (file lives in git) or omit it from `git add` (file lives in cache).
- **`dvc metrics show` returns nothing** — The metrics file isn't listed in any stage's `metrics:` and isn't tracked with `dvc.api.metrics_show()`-compatible markers. Add it to `dvc.yaml`.
- **CSV plot has no x-axis** — Default rendering picks the first numeric column. Specify `x:` explicitly.
- **`dvc plots diff` between two experiments shows only one series** — One of the experiments doesn't have the plot file. Check with `dvc plots show --rev <exp-name>`.
- **HTML report doesn't open** — Use `--open` flag or open the printed path manually. On headless servers, just capture the HTML file as an artifact.
