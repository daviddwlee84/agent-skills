# Anti-patterns

Failure modes this harness exists to prevent. Each has been observed in
real research codebases; several were observed in the reference project.

## Process

- **HARKing (Hypothesizing After Results are Known)** — writing the
  "hypothesis" after seeing which config won. Prevention: pre-registration
  section is written before running; treat post-hoc edits to it as
  falsification. Post-hoc *observations* are welcome — in `## Log` or as
  new `P?` roadmap items, labeled as exploratory.
- **Running an experiment that cannot change a decision** — if the
  decision rule's branches are identical ("interesting either way"), the
  compute is entertainment. Park it in `P?` until a decision hangs on it.
- **Winner's-curse reporting** — quoting the best cell of a searched grid
  as "the result". The REPORT must show the search space and selection
  rule, not just the argmax; robust aggregates (median-of-top-k,
  significance gates) beat single peaks.
- **Silent spec drift** — changing fees/cost model/eval window and
  comparing against old numbers. Prevention: `spec:` labels on every
  table; a spec bump forces re-runs or `weakened` markers.
- **Retrying a dead end because nobody wrote it down** — negative results
  without a dead-end clause ("do not retry unless X changes") get
  re-attempted by the next person/agent with fresh enthusiasm and the
  same outcome.

## Structure

- **Spawning parallel surfaces** — `RESULTS.md`, `FINDINGS_v2.md`,
  `experiments_new/`... One LEDGER, one ROADMAP, one index. Same rule as
  the TODO harness: consolidate, don't fork.
- **Editing `experiments/README.md` by hand** — it's rendered from
  front-matter; hand edits are overwritten. Fix the front-matter instead.
- **Run-level noise in the LEDGER** — 15 findings from one experiment
  means the REPORT's job leaked upward. Distill to the 1–5 statements
  someone would act on.
- **Findings without evidence links** — "we tried X, didn't work" with no
  `(#NNN)` pointer is folklore, not a finding; it can't be audited or
  overturned properly.
- **Orphan experiments** — folders with results but no REPORT front-matter
  never appear in the index, so they'll be re-run. `render-index.py`
  reports folders that are missing REPORT.md files.

## Provenance

- **Numbers from dirty working trees** — `dirty: yes` on the final run of
  record means the SHA doesn't reproduce the table. Commit first, then run.
- **"See MLflow" as the whole conclusion** — MLflow rots (deleted stores,
  moved hosts). The decisive table and verdict live in the REPORT;
  MLflow holds telemetry.
- **Unpinned data windows** — "recent data" instead of explicit date
  ranges. Every data reference carries its window and staging/filter
  description.
- **Seed amnesia in stochastic pipelines** — if two runs of the repro
  command differ materially and no seed is recorded, the result is rung-1
  anecdote regardless of how nice the table looks.

## Triage

- **Priorities frozen while assumptions moved** — a P1 whose `depends-on:`
  finding was overturned three weeks ago. Run `retriage.py` after every
  overturn and periodically otherwise.
- **Everything is P1** / **payoff: "might help"** — un-priced queues decay
  into vibes-driven execution. The payoff field is mandatory precisely so
  the queue stays an expected-value ranking.
- **Research/engineering blur** — engineering tasks camouflaged as
  experiments ("try making the cache faster") skip the payoff question and
  crowd out actual research. The `cat:` tag keeps the mix visible.
