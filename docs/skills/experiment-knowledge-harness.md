# experiment-knowledge-harness

A file-based **research memory** for ML / DL / Quant projects. Sibling of
`project-knowledge-harness`: that one remembers *engineering work*, this one
remembers *what we believe and why*.

The problem it exists for: six months into a research project, nobody can
answer "did we already try this?" — so the dead end gets re-run, and the GPU
hours get spent twice.

| Surface | Question it answers |
|---|---|
| `experiments/LEDGER.md` | "What do we currently believe, and on what evidence?" |
| `experiments/ROADMAP.md` | "What's worth running next, and why that order?" |
| `experiments/INBOX.md` | "Where do I dump a raw idea at 2am?" |
| `<NNN>-<slug>/REPORT.md` | "What exactly was run, under what spec, with what result?" |
| `experiments/README.md` | Auto-rendered Mermaid map + index of everything |

## The two ideas that make it work

**Findings are numbered and overturnable.** A finding is `F-007`, dated, tied
to the experiment that produced it and a link to the evidence. When a later
experiment contradicts it, `log-finding.py --overturns F-007` moves the old one
to a graveyard lane with strikethrough — the history stays readable instead of
being quietly edited away.

**Overturning a finding re-triages the queue.** ROADMAP items carry
`depends-on: F-007`. When `F-007` falls, `retriage.py` lists every planned
experiment resting on it and exits non-zero. Planned work that was justified by
a belief you no longer hold gets flagged rather than silently executed.

## Pre-registration and the single-axis contract

Each REPORT is filled in **before running**:

- **Pre-registration** — hypothesis, success criteria, and a decision rule.
  If the decision rule's branches are identical, don't run the experiment.
  (That check alone kills a surprising number of experiments.)
- **One ablation axis**, declared in front-matter, compared against a *named*
  baseline.
- **Comparability spec** — every results table states the `spec:` (cost model,
  fee, eval-window version) it was produced under. Numbers from different specs
  never share a table.

`references/anti-patterns.md` names the failure modes this is defending
against: HARKing, decision-less experiments, winner's curse, spec drift, and
unwritten dead ends.

## During a long run

The harness covers *before* a run (pre-registration, triage) and *after* it
(conclusion, findings, provenance). The window **during** a multi-day run is
now covered too, because `status: running` is a note-to-self that nothing
watches:

1. **The run writes a durable completion marker** — an atomic exit-code file,
   so a *later* session can tell "finished, exit 0" from "killed at 3am"
   without re-running GPU time. After a restart, reconcile every
   `status: running` REPORT against the actual markers rather than assuming.
2. **If the next experiment is already decided, chain it in the scheduler.** A
   `depends-on: #NNN` tag is documentation — it schedules nothing. When #008
   genuinely runs after #007, submit it with a real dependency at the same time.

Explicitly *not* recommended: babysitting a long run with a self-rescheduling
check-in that wakes, greps a log, finds nothing changed, and reschedules. See
[`long-running-jobs`](long-running-jobs.md).

## When the skill triggers

- "Have we tried X before?" / "別重複造輪子、別浪費算力"
- Recording which directions succeeded vs failed, so dead ends stay dead.
- Making results discoverable and comparable across months.
- Re-prioritizing planned work when a conclusion changes.
- "Give me the big picture of all experiments."
- Jotting a raw research idea, or sweeping the experiments inbox.

## When it doesn't

- A single ad-hoc calculation — no hypothesis, no experiment.
- Hypothesis-free engineering work → `TODO.md` / `project-knowledge-harness`.
- **Run-level metric streaming** → that's MLflow / W&B territory. This harness
  stores conclusions and references, not raw run telemetry.

## Structure

```
skills/local/experiment-knowledge-harness/
├── SKILL.md
├── scripts/
│   ├── init.sh                     # idempotent scaffold into a target repo
│   ├── new-experiment.py           # allocate #NNN, scaffold REPORT.md
│   ├── log-finding.py              # append F-NNN; --overturns moves the old one
│   ├── render-index.py             # validate all surfaces + rewrite Mermaid map
│   ├── sweep-inbox.py              # triage INBOX bullets into ROADMAP items
│   ├── retriage.py                 # flag items resting on overturned findings
│   ├── snapshot-provenance.py      # collect git SHA, versions, host, timestamp
│   └── _lib.py                     # shared stdlib-only parsers/validators
├── references/                     # report-format, ledger-format, tag-schema,
│                                   # provenance, when-to-log-what, anti-patterns
└── assets/                         # 6 templates incl. agent-guidance snippet
```

Everything is stdlib Python + bash 3.2 — deliberately harness-agnostic, so it
works the same under Claude Code, Cursor, Codex, or a human.

## Reproducibility ladder

`references/provenance.md` grades provenance rather than demanding perfection:

| Rung | Meaning |
|---|---|
| Anecdote | a number in a message |
| Recorded | number + REPORT with a spec |
| Replayable | + git SHA, config hash, data window, seeds |
| Pinned | + environment and artifact paths |

Default assumption is **no tracking server**. When run telemetry is worth
keeping, it suggests a local SQLite MLflow backend so the store stays a single
portable file.

## Validation

`render-index.py` is the gate: it validates REPORT front-matter against the
status enum, checks ledger syntax and cross-references, verifies ROADMAP item
grammar (mandatory `payoff:` and `cat:`), and flags experiment folders missing
a REPORT.md — then rewrites the map. `retriage.py` exits `1` when re-triage is
needed, so it can run in CI.
