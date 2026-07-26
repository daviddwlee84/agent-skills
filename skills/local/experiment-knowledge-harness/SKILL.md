---
name: experiment-knowledge-harness
description: Set up and operate a research-experiment memory for ML/DL/Quant projects — LEDGER.md of numbered findings (what we believe, evidence links, overturn protocol), ROADMAP.md experiment queue triaged by expected payoff × cost × category × assumption dependencies, INBOX.md human scratchpad swept into the roadmap via targeted questions, an auto-rendered Mermaid map of how experiments/findings/queued work reference each other, and per-experiment REPORT.md with pre-registration, single-axis ablation contract, results tables and provenance blocks (git SHA, config hash, data window, seeds, MLflow refs). Use when the user wants to track which directions were explored vs not, record which succeeded or failed, avoid re-running dead-end experiments or wasting compute, make results discoverable and comparable, keep experiments reproducible, re-prioritize planned work when a conclusion changes, get a big-picture map of all experiments, jot a raw research idea somewhere, or asks to sweep the experiments inbox.
---

# experiment-knowledge-harness

A file-based **research memory** for ML/DL/Quant projects. Sibling of
`project-knowledge-harness` (which manages software-work memory:
`TODO.md` / `backlog/` / `pitfalls/`). This skill manages **experiments**:
hypotheses, runs, conclusions, and the beliefs built on top of them.

The atomic difference from software work: in research, a *failed* experiment
is a first-class deliverable (it saves future compute), results are only
meaningful when *comparable* (ablation discipline), and numbers without
*provenance* rot within weeks.

Five surfaces, separated by the question they answer:

| Surface | Question it answers | Access pattern |
|---|---|---|
| `experiments/LEDGER.md` | "What do we currently **believe**? What succeeded / failed?" | Numbered findings `F-001…`; **grep before designing anything new** |
| `experiments/ROADMAP.md` | "What is **worth running** next?" | Priority lanes; payoff × cost × category × `depends-on:` tags |
| `experiments/INBOX.md` | "Where do I **jot a raw idea** before it's priceable?" | Human free-text bullets; agent sweeps them into ROADMAP on request |
| `experiments/<NNN>-<slug>/REPORT.md` | "What exactly was run, and what did we conclude?" | Front-matter (machine-readable) + results tables + provenance |
| `experiments/README.md` | "Where do I **find** result X? How does it all **fit together**?" | Auto-rendered Mermaid map + index table — never edit the sentinel blocks by hand |

Engineering chores stay in `TODO.md`; debugging traps stay in `pitfalls/`
(both from `project-knowledge-harness`). The two harnesses compose — see
[`references/when-to-log-what.md`](references/when-to-log-what.md) for the
routing rules.

## When to use this skill

Use when the user surfaces any of:

- "Have we tried X before?" / "avoid repeating failed experiments" /
  "別重複造輪子" / "浪費算力"
- "Which directions worked, which didn't?" — needs a findings ledger
- "Where is the result of experiment Y?" — needs the index + REPORT layout
- "This idea depends on assumption Z — reorder plans if Z falls" —
  needs `depends-on:` triage
- "Make this experiment reproducible / record versions & data configs"
- A pile of ad-hoc experiment folders/notebooks with no comparable
  conclusions table

Do NOT use for: single ad-hoc calculations (just answer them), engineering
tasks with no hypothesis (route to `TODO.md`), or run-level metric streaming
(that's MLflow/W&B territory — this harness stores *conclusions and
references*, not raw run telemetry).

## How to apply this skill (default workflow)

```
scripts/
  init.sh                  # one-shot scaffold: LEDGER + ROADMAP + INBOX + index + agent guidance
  new-experiment.py        # allocate #NNN, scaffold REPORT.md, link from ROADMAP
  log-finding.py           # append F-xxx to LEDGER (handles --overturns)
  render-index.py          # rebuild experiments/README.md (map + index) from REPORT front-matter + validate all surfaces
  sweep-inbox.py           # formalize INBOX.md ideas into ROADMAP items (lists missing judgments to ask the user)
  retriage.py              # list planned items whose depends-on findings were overturned
  snapshot-provenance.py   # emit a ready-to-paste provenance block
```

### 0. Set up once per project

```sh
scripts/init.sh --target /path/to/project --project-name "My Project"
```

Creates `experiments/{LEDGER.md,ROADMAP.md,README.md}` from templates
(skipping existing files), appends a sentinel-guarded guidance snippet to
`AGENTS.md`/`CLAUDE.md`, and runs `render-index.py --validate-only`.
Idempotent; safe to re-run.

### 1. BEFORE designing or running any experiment

1. `grep` the LEDGER and the index for the topic — has this direction been
   tried? Is there a `dead-end` finding whose assumptions still hold?
2. If a relevant finding exists, cite it (`F-xxx`) in the new plan instead
   of re-deriving it.
3. Check `ROADMAP.md`: is this already queued with a priority? If yes,
   start from that item (and its linked notes) rather than from scratch.

### 2. When the user surfaces an experiment idea (not running it yet)

Add a ROADMAP entry with the four mandatory judgments (see
[`references/tag-schema.md`](references/tag-schema.md)):

```markdown
- [ ] **[M] Calibrate slippage against broker fills** — replay real fills vs
  simulated same-day PnL (payoff: decides which threshold regions are truly
  tradable; cat: research; depends-on: F-001)
```

- `payoff:` — expected gain **with units** (metric uplift, bp/day, x-fold
  speedup, "unblocks Y"). Forces the expected-value conversation early.
- `cat:` — `research` (answers a question) vs `engineering` / `data` /
  `tooling` / `infra` (improves the machinery).
- `depends-on:` — findings this plan's priority *assumes*. This is what
  makes re-prioritization mechanical when a conclusion flips.
- Not sure about priority yet? Put it in the `## P?` lane — same as the
  TODO harness. Ideas that can't even be judged yet belong in
  `experiments/INBOX.md` (see below); non-research software sparks go to
  `backlog/inbox.md` as usual.

### 2b. Sweeping the inbox (human ideas → ROADMAP)

`experiments/INBOX.md` is the zero-friction human capture surface: the user
drops free-text `- ` bullets whenever an idea strikes, without stopping to
price it. When the user asks to *sweep the inbox* (掃一下 inbox / 整理 idea):

1. Run `scripts/sweep-inbox.py` (no args). It lists every entry, the
   judgments derivable from inline hints, and — per entry — the questions
   still open (lane / effort / cat / payoff).
2. For entries the LEDGER already answers, say so: cite the `F-xxx` and ask
   whether to drop the entry instead of queueing a duplicate.
3. **Ask the user the listed questions** for incomplete entries — payoff
   with units is the one judgment you must never invent. Batch questions
   for all entries into a single round where possible. If an idea is too
   vague to formalize even after one round, leave it in the inbox with a
   short note rather than forcing it.
4. Formalize each resolved entry:
   `scripts/sweep-inbox.py --formalize N --lane P2 --effort M --cat research
   --payoff "..." [--depends-on F-003] [--title "..."]` — the item lands in
   the right ROADMAP lane, validator-checked, and the bullet is deleted.
   Entries whose inline hints are already complete: `--batch` does them all.
5. Finish with `scripts/render-index.py` so the map picks up new
   `depends-on:` edges.

### 3. When starting an experiment

```sh
scripts/new-experiment.py --title "Slippage calibration vs ATP fills" \
  --question "Is half-spread taker cost the right execution model?" \
  --axis "slippage model" --baseline "#001 half_spread" \
  --from-roadmap "Calibrate slippage"
```

Then **fill in the pre-registration section of REPORT.md before running
anything**: hypothesis, success criteria, and the decision rule
("if X we do A, if Y we do B"). If A == B for every outcome, the experiment
cannot change a decision — *don't burn the compute*.

Non-negotiable design contract (details in
[`references/report-format.md`](references/report-format.md)):

- **One ablation axis per experiment**, declared in front-matter, compared
  against a *named* baseline (`#NNN` or an explicit config).
- **Comparability spec**: every results table states the `spec:` (cost
  model / fee / eval-window versions) it was produced under. Numbers from
  different specs never share a table.

### 4. While the experiment runs

Append dated bullets to the REPORT's `## Log` (decisions, surprises,
course corrections). Add one row per run/config to the results table as
results land — don't batch-reconstruct at the end.

For runs measured in hours or days, two things must be true before you walk
away:

1. **The run writes a durable completion marker.** `status: running` in the
   front-matter is a note-to-self, not evidence — nothing watches it. Have the
   job record its own exit code atomically (temp file + `mv`), so a *later*
   session can tell "finished, exit 0" from "killed at 3am" without re-running
   GPU time. On a session restart, reconcile every `status: running` REPORT
   against the actual markers rather than assuming it is still going.
2. **If the next experiment is already decided, chain it in the scheduler**
   rather than in your head. A `depends-on: #NNN` tag is documentation — it
   schedules nothing. When #008 genuinely runs after #007, submit it with a
   real dependency (`sbatch --dependency=afterok:`, `pueue --after`) at the
   same time, so the queue survives losing the session.

Do **not** babysit a long run with a repeating check-in that wakes up, greps a
log, finds nothing changed, and reschedules itself — that costs a full context
read per tick and still loses the chain if the session dies. See the
`long-running-jobs` skill for the full ladder.

### 5. When an experiment concludes (including failures)

1. Write `## Conclusion` in REPORT.md: status
   (`concluded-success` / `concluded-negative` / `inconclusive`), and for
   negative results the **dead-end clause**: "do not retry unless
   `<assumption / F-xxx>` changes".
2. Paste the provenance block (`scripts/snapshot-provenance.py --cmd "..."`)
   — git SHA, config hash, data window, seeds, artifact paths, optional
   MLflow ref. See [`references/provenance.md`](references/provenance.md).
3. Distill 1–5 findings: `scripts/log-finding.py --statement "..."
   --evidence "#002" [--overturns F-004]`.
4. `scripts/render-index.py` to refresh the index; move the ROADMAP item to
   `## Done`.
5. If a finding got **overturned**, immediately run `scripts/retriage.py`
   and re-sort the flagged ROADMAP items with the user.

### 6. Periodically (or when priorities feel stale)

Run `scripts/retriage.py`. It cross-references LEDGER statuses against
`depends-on:` tags and lists every planned item resting on overturned or
weakened findings.

## The map (big picture at a glance)

`render-index.py` also rewrites a Mermaid graph between the
`experiment-map` sentinels in `experiments/README.md` (inserted
automatically above the index on first render). It is derived entirely
from data that already exists — never drawn by hand:

- **Experiment nodes**, colour-coded by `status:`, linking to their REPORTs
  and listing their findings.
- **`baseline:` edges** — #NNN references in front-matter `baseline:` become
  "built on" arrows; the optional front-matter key `refs: [#NNN, ...]`
  adds further cross-reference edges (validated to exist).
- **Overturn edges** — when a finding overturns another, an arrow connects
  the two source experiments, labelled `F-new overturns F-old`.
- **Queued ROADMAP items** hang off the experiments whose findings their
  `depends-on:` cites — so the map shows both where knowledge came from
  and what is planned on top of it.

When two experiments relate in a way no `baseline:`/`depends-on:` captures,
add `refs: [#NNN]` to the later REPORT's front-matter and re-render.

## Formats

- REPORT.md front-matter and section schema: [`references/report-format.md`](references/report-format.md)
- LEDGER finding syntax and the overturn protocol: [`references/ledger-format.md`](references/ledger-format.md)
- ROADMAP tag grammar (validator-checked): [`references/tag-schema.md`](references/tag-schema.md)
- Provenance & MLflow conventions: [`references/provenance.md`](references/provenance.md)
- What goes where (vs TODO/backlog/pitfalls): [`references/when-to-log-what.md`](references/when-to-log-what.md)
- Common failure modes: [`references/anti-patterns.md`](references/anti-patterns.md)

## Templates and bundled assets

- `assets/LEDGER.md.template` — findings ledger skeleton
- `assets/ROADMAP.md.template` — experiment queue skeleton with lane docs
- `assets/INBOX.md.template` — human idea scratchpad (sweep target)
- `assets/experiments-README.md.template` — map + index shell (auto-rendered body)
- `assets/report.md.template` — single experiment REPORT
- `assets/agent-guidance.md.template` — snippet appended to `AGENTS.md`

## Reference implementation

`OfflineAnalysis` repo: `experiments/` root with
`001-threshold-search` backfilled from a real anti-overfitting study —
LEDGER findings F-001…F-005 (including an overturned-assumption example),
ROADMAP with payoff/cat/depends-on triage, and a REPORT.md whose Round 0
(execution-cost model) shows exactly why the comparability `spec:` field
exists.
