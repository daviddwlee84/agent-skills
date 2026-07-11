# REPORT.md format

Every experiment folder (`experiments/<NNN>-<slug>/` by default; any folder
name is accepted) must contain a `REPORT.md` with a machine-readable
front-matter and a fixed section skeleton. `scripts/render-index.py`
validates the front-matter and builds the index from it.

## Front-matter (validator-checked)

```yaml
---
id: 002                    # zero-padded, unique across experiments/
slug: slippage-calibration # folder-name-friendly short name
title: Slippage calibration against ATP broker fills
status: running            # see enum below
question: Is half-spread taker cost the right execution model?
axis: slippage model       # THE ablation axis — exactly one
baseline: "#001 half_spread-v2"   # named baseline: an #NNN ref or explicit config
spec: half_spread-v2       # comparability spec version (see below)
started: 2026-07-06
concluded: 2026-07-10      # required once status is a concluded-* / inconclusive / superseded
conclusion: >              # one line; required once concluded — this is what the index shows
  Real fills cost 0.7x the half-spread assumption; spec bumped to fills-v3.
findings: [F-006, F-007]   # LEDGER ids distilled from this experiment (refs must exist)
tags: [execution, costs]
refs: []                   # optional: [#NNN, ...] cross-references beyond baseline
                           # (drawn as edges in the README map; must exist)
mlflow: ""                 # optional: "sqlite:///mlruns.db exp=<name> runs=<id,...>"
---
```

Parsing note: the front-matter parser is a minimal YAML subset — flat
`key: value` scalars, inline lists `[a, b]`, and `>` folded strings on the
following indented lines. Do not use nested mappings.

### `status` enum

| status | meaning |
|---|---|
| `planned` | scaffolded, pre-registration written, not yet running |
| `running` | actively producing runs |
| `concluded-success` | hypothesis supported / improvement confirmed |
| `concluded-negative` | hypothesis rejected — **still a deliverable**; must carry a dead-end clause |
| `inconclusive` | insufficient power / mixed evidence; say what would settle it |
| `superseded` | replaced by a later experiment (name it in `conclusion`) |

## Section skeleton

### 1. `## Pre-registration` — WRITE BEFORE RUNNING

- **Hypothesis** — falsifiable, quantified where possible.
- **Success criteria** — the numeric bar, chosen now, not after seeing results.
- **Decision rule** — "if X we do A; if Y we do B". If A == B for every
  outcome, the experiment cannot change any decision: don't run it.

Pre-registration is the anti-HARKing device: editing this section after
results exist is the one thing this harness treats as cheating.

### 2. `## Setup`

Data (source, date window, filters), strategy/model config, entry-point
commands, compute used. Enough for a colleague to re-run without asking.

### 3. `## Results`

One or more Markdown tables. Rules:

- Every table caption states the `spec:` it was produced under. **Numbers
  from different specs never share a table** (see below).
- One row per run/config; columns include the varied axis value and the
  pre-registered metrics.
- Append rows as results land; don't reconstruct at the end.
- Large per-run grids can live in a `runs.csv` next to REPORT.md; the
  REPORT table then holds the aggregated/decisive view.

### 4. `## Log`

Dated bullets: decisions, surprises, dead ends, course corrections.
This is the narrative that explains *why* the results table looks the way
it does.

### 5. `## Conclusion`

- Verdict against the pre-registered criteria (quote the numbers).
- For `concluded-negative`: the **dead-end clause** — "do not retry unless
  `<assumption or F-xxx>` changes". This line is what saves future compute.
- List the findings distilled to the LEDGER.

### 6. `## Provenance`

Paste the block from `scripts/snapshot-provenance.py`. See
[`provenance.md`](provenance.md). A results table without a provenance
block is treated as unverified.

## The single-axis ablation contract

- `axis:` declares the one dimension this experiment varies; everything
  else is pinned by `baseline:` + `spec:`.
- Need to vary two things? Either factor into two experiments (or
  sub-tables varying one axis each against the same baseline), or mark the
  run rows `exploratory` — exploratory rows are excluded from cross-
  experiment comparisons and cannot back a LEDGER finding on their own.
- The baseline must be *named*: an `#NNN` reference or an explicit config
  string. "vs before" is not a baseline.

## Comparability spec (`spec:`)

A `spec` is a short version label for everything that silently changes
numbers without being the experiment's axis: cost/slippage model, fees,
eval window and sessions, metric definitions, data normalisation.

- Bump the label whenever any of those change (`half_spread-v2` →
  `fills-v3`), and record what changed in the experiment that motivated
  the bump.
- Cross-experiment comparisons (and ablation series) are only valid within
  one spec. When a spec bump invalidates old numbers, either re-run the
  old grid under the new spec or mark the affected findings `weakened`.

Rationale (real case): a threshold-search study first ran with zero
slippage and produced "+199k over 34 days" for an aggressive argmax config;
under half-spread costs the same config was deeply negative and every
conclusion flipped. The spec label exists so such numbers can never be
silently mixed.
