# LEDGER.md format

`experiments/LEDGER.md` is the findings ledger: one numbered, greppable
statement per thing the project currently believes, each backed by
evidence. It is the **first file to grep before designing any experiment**.

## Why a ledger and not just reports

Reports answer "what did experiment #NNN find?". The ledger answers the
reverse lookup: "what do we believe about topic X, and which experiment
proved it?" — without knowing which experiment to open. It is also the
substrate for `depends-on:` triage in ROADMAP.md.

## Finding syntax (validator-checked)

Two lanes, in order: `## Active`, then `## Overturned`.

### Active findings

```markdown
- **F-001** [2026-07-04] (#001) Zero-slippage mid-price marking was the
  dominant overfit driver — argmax picked (0.5,0.5) "+199k / 34d", deeply
  negative under half-spread costs. → [evidence](threshold_search/README.md)
```

- `- **F-NNN**` — zero-padded id, unique, monotonically increasing.
- `[YYYY-MM-DD]` — date recorded.
- `(#NNN)` — source experiment id; use `(ext)` for findings imported from
  outside the harness (papers, other repos, production incidents) and name
  the source in the text.
- Statement — one to three lines; wrapping/indentation is free, the
  validator only checks the first line's prefix.
- Optional ` → [evidence](<relative link>)` deep-link.
- Optional weakened marker appended: `(weakened by F-012)` — belief still
  held but with reduced confidence; `retriage.py` flags dependents.

### Overturned findings

Never delete a finding — move it and strike it through, so the reasoning
trail survives:

```markdown
- ~~**F-004**~~ [2026-07-03] (#001) IS argmax transfers to OOS. —
  overturned 2026-07-05 by F-005
```

The line must contain `overturned <date> by F-NNN`.

## What makes a good finding

- **Decision-relevant**: someone reading it changes what they run next.
- **Falsifiable and quantified**: "robust_sharpe beats baseline in 6/6 dev
  configs (PBO 0.10 vs 0.574)" — not "robust methods seem better".
- **Self-contained**: readable without opening the report (the report holds
  the detail, the finding holds the takeaway).
- **Scoped**: state the regime/spec it was established under when that
  matters ("under half_spread-v2 costs, ...").
- Negative findings are first-class: "X does not work because Y — do not
  retry unless Z changes" is often the most compute-saving line in the file.

Granularity: an experiment typically distills 1–5 findings. If you're
writing 10, they're run-level observations — keep those in the REPORT.

## The overturn protocol

When new evidence contradicts an active finding:

1. `scripts/log-finding.py --statement "..." --evidence "#012" --overturns F-004`
   — records the new finding and moves F-004 to `## Overturned` with the
   annotation.
2. Run `scripts/retriage.py` — every ROADMAP item with `depends-on: F-004`
   is now flagged; re-sort those priorities with the user.
3. If the overturn came from a spec bump (cost model change etc.), sweep
   the ledger for other findings established under the old spec and mark
   them `(weakened by F-new)` where appropriate.
