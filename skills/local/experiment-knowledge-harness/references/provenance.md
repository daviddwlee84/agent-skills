# Provenance conventions

A number you cannot reproduce is an anecdote. Every concluded REPORT.md
carries a `## Provenance` block; `scripts/snapshot-provenance.py` generates
it so nothing is transcribed by hand.

## The block

```markdown
## Provenance

- **code**: `7dfd2fc` (dirty: no) @ branch `main`
- **repro**: `uv run python experiments/001-threshold-search/scripts/run_meta_sweep.py --workers 8`
- **data**: orders+snapshots 2026-05-13..2026-06-30 (34 d); staged via `prepare_date.py`
- **config-hash**: grid cache schema v2; StrategyParams md5 `a1b2c3...` where applicable
- **spec**: half_spread-v2 (fee 0.6bp, sessions 09:35–11:30/13:00–14:50, size 10)
- **seeds**: n/a (deterministic) | `PYTHONHASHSEED=0, numpy seed 42`
- **env**: python 3.13.x, vectorbt 0.28.x, numpy 2.x (`uv.lock` @ same SHA)
- **artifacts**: `experiments/001-threshold-search/results/` (gitignored, host: <hostname>)
- **mlflow**: sqlite:///mlruns.db exp=threshold_search runs=3f2a...,9c1b...  <!-- optional -->
```

Field notes:

- **code** — commit SHA + dirty flag. If dirty, the script appends
  `git diff --stat`; prefer committing before the final run of record.
- **repro** — the exact command(s). If a chain, list in order. A block
  without a runnable command is decoration.
- **data** — source + date window + filters/staging. In this repo's terms:
  which dates were staged, which loader normalisation applied.
- **config-hash** — the project's canonical param hash where one exists
  (e.g. `StrategyParams.md5()` / cache schema version). This is the join
  key between the REPORT and on-disk artifacts.
- **spec** — the comparability spec label (see `report-format.md`) with its
  decisive constants inlined.
- **seeds** — every stochastic component, or an explicit `deterministic`.
- **env** — interpreter + the few libraries whose version changes numbers;
  the lockfile at the recorded SHA is the full answer.
- **artifacts** — where heavy outputs live (usually gitignored); name the
  host if storage is machine-local.
- **mlflow** — optional pointer, never a replacement for this block.

## MLflow integration (optional, local-first)

Default assumption: **no tracking server**. When run telemetry is worth
keeping (long training runs, many-seed sweeps), prefer a local SQLite
backend so the store is a single portable file:

```python
import mlflow
mlflow.set_tracking_uri("sqlite:///mlruns.db")   # repo-local, gitignored
mlflow.set_experiment("threshold_search")
```

- Record the pointer in front-matter `mlflow:` and in the provenance block:
  `sqlite:///mlruns.db exp=<name> runs=<id,...>`.
- Browse later with `mlflow ui --backend-store-uri sqlite:///mlruns.db`.
- Switching backends later (team server etc.) is a URI swap; the harness
  only ever stores the URI + run ids, so nothing else changes. If a store
  migrates, update the pointer lines — ids survive `mlflow` export/import.
- Division of labour: MLflow holds *run-level telemetry* (params, per-epoch
  metrics, model artifacts); the REPORT holds *the decisive table and the
  conclusion*. If a reader must open MLflow to learn what was concluded,
  the REPORT is incomplete.

## Reproducibility ladder

Not every experiment deserves the same rigor; declare the rung you're on
rather than silently mixing them:

1. **Anecdote** — number in chat/notebook, no provenance. Fine for
   exploration; never cite in LEDGER.
2. **Recorded** — provenance block complete; artifacts on one host.
   Minimum bar for `concluded-*` status.
3. **Replayable** — clean checkout at the SHA + `repro` command
   regenerates the table (data staged separately).
4. **Pinned** — rung 3 plus immutable data snapshot (hash-addressed) and
   fixed seeds; bit-for-bit or tolerance-bounded identical output.

Findings that gate real-money decisions should sit on rung 3+.
