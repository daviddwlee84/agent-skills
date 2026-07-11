# ROADMAP tag schema (priority × cost × payoff × category × dependencies)

`experiments/ROADMAP.md` is the experiment queue. Same lane mechanics as
the TODO harness (`## P1` / `## P2` / `## P3` / `## P?` / `## Done`), but
each item carries research-specific judgments that make triage — and
re-triage — mechanical.

## Item syntax (validator-checked)

Active items in `P1`/`P2`/`P3`:

```markdown
- [ ] **[M] Calibrate slippage against ATP broker fills** — replay real
  fills vs simulated same-day PnL (payoff: decides which threshold regions
  are truly tradable; cat: research; depends-on: F-001)
```

Active items in `P?` use `**[?/M] ...**` — explicitly "unknown of size M".

Shipped/concluded items in `## Done`:

```markdown
- ✅ [2026-07-05] [P1/L] Threshold anti-overfit study → #001 (F-001..F-005)
```

Grammar:

- `- [ ] **[Effort] Title** — description (payoff: ...; cat: ...[; depends-on: F-xxx[, F-yyy]])`
- The parenthesized tail must contain `payoff:` and `cat:`;
  `depends-on:` is optional. Free prose may precede the parenthesis.
- Sub-bullets, prose paragraphs, and HTML comments between items are
  ignored by the validator — use them for context.
- You rarely need to hand-write this: `scripts/sweep-inbox.py --formalize`
  emits the grammar mechanically from an `INBOX.md` idea plus the four
  judgments, and validates before committing the edit.

## Axes

### Priority — `P1` / `P2` / `P3` / `P?`

Same semantics as the TODO harness: P1 = next batch, P2 = worth doing,
P3 = someday, P? = needs a spike before it can be priced. **Priority is a
function of payoff ÷ cost given current findings** — which is why
`depends-on:` exists: when a finding flips, the priority computed from it
is stale.

### Effort — `[S]` / `[M]` / `[L]` / `[XL]`

Total cost: human + compute + calendar.

- `S` — under an hour of work; compute finishes while you watch
  (e.g. pure re-analysis over an existing cache)
- `M` — half-day of work or an overnight compute job
- `L` — multi-day; serious GPU/cluster time; needs checkpointing
- `XL` — multi-week campaign; write a design note in `backlog/` first

When compute dominates and is worth calling out, append it in prose:
`**[M] ...** — ... (~40 GPU-h)`.

### `payoff:` — expected value, with units (mandatory)

The single highest-leverage field. Forces "what do we get if this works?"
before compute is spent. Good payoffs are falsifiable:

- metric uplift: `payoff: +0.3 Sharpe on dev split` / `+2bp/day net`
- performance: `payoff: 30x cache build speedup, unblocks daily re-tune`
- risk/knowledge: `payoff: decides go/no-go on per-symbol tuning`
- unblocking: `payoff: unblocks #007 and #009`

`payoff: might be interesting` is not a payoff — park the item in `P?` or
`backlog/inbox.md` until it can be priced.

### `cat:` — category (mandatory)

- `research` — answers a question; output is a finding
- `engineering` — improves machinery (speed, refactor, pipeline); output is capability
- `data` — new data source, labeling, coverage extension
- `tooling` — analysis/visualisation/harness improvements
- `infra` — compute, storage, scheduling, tracking backends

Research and engineering compete for the same hours but produce different
value; tagging keeps the queue honest about the mix.

### `depends-on:` — assumption links (optional but load-bearing)

List the LEDGER findings whose truth this item's priority assumes.
`scripts/retriage.py` cross-references these against finding statuses and
flags every item resting on an overturned/weakened finding. This turns
"new conclusion → re-sort the plan" from a memory feat into a command.

Also allowed: `depends-on: #NNN` when the dependency is "experiment NNN
must conclude first" rather than a specific finding.

## Useful combinations

- `P? [?/S] payoff: unknown` — cheap spike to price a bigger idea: run it
  in idle time, then re-file properly.
- `P1 [XL]` — validator accepts it but treat as a smell: scope-cut or
  split before starting.
- `P3 + depends-on:` — parked *conditionally*: revisit automatically when
  the dependency changes rather than on a calendar.
