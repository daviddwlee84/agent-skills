# When to log what — routing between the two harnesses

`experiment-knowledge-harness` (research memory) composes with
`project-knowledge-harness` (software memory). Neither replaces the other.
Route each piece of knowledge by what it *is*, not where you happened to
be working when you learned it.

## Routing table

| You have... | It goes to | Why |
|---|---|---|
| A hypothesis worth testing, with a payoff guess | `experiments/ROADMAP.md` | It's an experiment: needs payoff/cat/depends-on triage |
| An engineering chore (refactor, speedup, pipeline glue) | `TODO.md` | No hypothesis; priority×effort is enough |
| A vague *research* spark (can't price payoff yet) | `experiments/INBOX.md` | Cheapest capture; `sweep-inbox.py` formalizes it into the ROADMAP later, asking the open questions |
| A vague *software* spark, not research | `backlog/inbox.md` | Same mechanism, project-knowledge-harness side |
| Design/trade-off analysis for a planned experiment (`[XL]`) | `backlog/<slug>.md`, linked from the ROADMAP item | Same resume-friendly notes mechanism as TODO items |
| Results + conclusion of an executed experiment | `experiments/<NNN>-<slug>/REPORT.md` | The atomic research record |
| A distilled belief the project should act on | `experiments/LEDGER.md` (`F-xxx`) | Reverse-lookup surface; feeds `depends-on:` |
| A debugging trap (error message, non-obvious fix) | `pitfalls/<slug>.md` | Grep-by-symptom works regardless of research/engineering origin |
| A rule agents must never break | `AGENTS.md` invariants | Graduation target for severe pitfalls *and* load-bearing findings |

## Boundary cases

- **"The experiment failed because of a bug"** — the bug goes to
  `pitfalls/` (symptom-titled); the experiment stays `running`/`inconclusive`
  until re-run on fixed code. A crashed run is not a negative finding.
- **"The tooling was too slow to run the sweep"** — the speedup work is a
  `TODO.md` item (`cat` would be engineering anyway); if the slowness
  *changed the research design* (smaller grid, fewer seeds), note that in
  the REPORT's Log so the power of the conclusion is judged honestly.
- **"A finding implies a code change"** (e.g. "zero-slippage marking is
  wrong everywhere") — finding in LEDGER, implementation item in `TODO.md`
  referencing the finding: `... — motivated by F-001`.
- **"Is this run-level detail or a finding?"** — if it changes what someone
  runs *next*, it's a finding; if it explains a row in a table, it's REPORT
  content; if it's per-epoch telemetry, it's MLflow's job.
- **An external paper/result** — log as `(ext)` finding only if the project
  will act on it; cite the source in the statement.

## Graduation paths

- Pitfall → `AGENTS.md` Hard invariant: unchanged from the base harness
  (recurring / silently corrupting / non-obvious workaround).
- **Finding → `AGENTS.md` invariant**: when a finding must constrain all
  future work regardless of context budget (e.g. "all backtests must use
  the half-spread cost model — zero-slippage numbers are fiction"),
  add it as an invariant and link back to the F-xxx. The LEDGER entry
  remains the evidence record.
- ROADMAP `## Done` entries stay forever (with `→ #NNN` links) — they are
  the queue's audit trail, mirroring the TODO harness convention.
