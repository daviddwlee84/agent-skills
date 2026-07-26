# Plan: `long-running-jobs` skill — stop putting the model in the polling loop

## Context

**The problem.** In an ML session on this machine, the agent babysits a Slurm
training run by *self-rescheduling one-shot `CronCreate` tasks* — "check at
16:31", then "check at 03:29" — each wake-up running `squeue`/`nvidia-smi`,
finding nothing changed, and scheduling the next one. That session sits at
**432k/1M context**, so every health-check tick re-reads a huge context to
learn "epoch 21, still fine". Worse, the Phase A → Phase B chain lives only in
the agent's head: if the session dies, compacts, or the laptop sleeps, Phase B
never starts.

**The real diagnosis.** Polling is not the sin. *Polling with the model inside
the loop* is. A shell `until squeue -h -j $JID | grep -q .; do sleep 60; done`
burns zero tokens over eight hours; a scheduled check-in burns a full context
read per tick. The fix is to move the timer out of the context window — into
the scheduler, a blocked shell, or a durable on-disk marker.

**Why a new skill.** Verified gaps:

- `skills/local/slurm-hpc/` has **zero** content on `--dependency`/`afterok`,
  `sbatch --wait`, `--parsable`, `--mail-type`, or any notion of waiting for a
  job. Only one-shot `squeue`/`sacct` inspection. `scripts/` and `assets/` are
  empty `.gitkeep` placeholders.
- `skills/local/experiment-knowledge-harness/` covers *before* a run
  (pre-registration, triage) and *after* (conclusion, provenance), but the
  window **during** a long run is one line: "append dated bullets to the Log".
  Its `status: running` is a static string nothing watches; `depends-on: #NNN`
  is a documentation edge with no execution semantics.
- `skills/local/pueue-job-queue/` is the closest prior art — it already ships a
  blocking `scripts/wait.py` — but it is pueue-specific.

The question "how should an agent wait?" is harness-level and tool-agnostic
(Slurm, pueue, DVC, a bare `python train.py`, a Docker build). That is what
makes it a skill rather than a paragraph inside `slurm-hpc`.

**Outcome.** An agent that reaches for a scheduler-owned chain first, a single
blocked background shell second, and a scheduled check-in only as a last
resort — and that always leaves a durable completion record so finished work
survives losing the session.

## Verified facts this plan rests on

Two of these contradict commonly-repeated advice, so the provenance matters.

### Claude Code harness — from the 2.1.220 binary on this machine + direct experiment

| Fact | Evidence |
|---|---|
| `Bash(run_in_background: true)` **notifies the agent when the process exits**. The tool result says "You will be notified when it completes." | Ran `sleep 45` backgrounded; received a completion `task-notification`. **Public-doc summaries claiming the agent must poll `/tasks` are stale.** This is the single most important fact — Tier 1 depends on it. |
| *"Use the Monitor tool to stream events from a background process (each stdout line is a notification). For one-shot \"wait until done,\" use Bash with run_in_background instead."* | verbatim string in the binary |
| *"To wait for a condition, use Monitor with an until-loop (e.g. `until <check>; do sleep 2; done`). To wait for a command you started, use run_in_background: true. Do not chain shorter sleeps to work around this block."* — foreground `sleep` is blocked | verbatim string in the binary |
| A `Monitor` tool exists (`MonitorTool`) but is **not exposed in every session's toolset** even on 2.1.220 — the skill must degrade gracefully when absent | binary contains it; this session's tool list does not |
| Plugins may ship `monitors/monitors.json` — host-armed persistent monitors, *"unsandboxed, same trust tier as hooks"*, fields `name` (dedupes re-arming), `description`, `trigger` (`always` \| `on-skill-invoke:<skill>`) | binary manifest-schema strings |
| `CronCreate` recurring tasks auto-expire after 7 days and only fire while the session runs and is idle | tool documentation |

### Slurm — from official docs

| Fact | Source |
|---|---|
| `-W, --wait`: *"Do not exit until the submitted job terminates."* / *"The exit code of the sbatch command will be the same as the exit code of the submitted job."* / *"If the job terminated due to a signal rather than a normal exit, the exit code will be set to 1."* / job arrays record *"the highest value for any task"* | [sbatch(1)](https://manpages.debian.org/buster/slurm-client/sbatch.1.en.html) |
| **The trap:** *"By default the job stays pending with reason DependencyNeverSatisfied"* unless `kill_invalid_depend` is set site-wide. And *"Once a job dependency fails due to the termination state of a preceding job, the dependent job will never be run, even if the preceding job is requeued."* | [sbatch(1)](https://slurm.schedmd.com/sbatch.html) |
| `afterany` is **the default dependency type** — a bare `-d 12345` is *not* `afterok` | [sbatch(1)](https://slurm.schedmd.com/sbatch.html) |
| *"All dependencies must be satisfied if the `,` separator is used. Any dependency may be satisfied if the `?` separator is used."* | [sbatch(1)](https://slurm.schedmd.com/sbatch.html) |
| `--parsable`: *"Outputs only the job ID number and the cluster name if present. The values are separated by a semicolon."* | [sbatch(1)](https://slurm.schedmd.com/sbatch.html) |
| `aftercorr` chains array tasks element-wise; `--signal=B:USR1@300` signals *only the batch shell* before the wall-clock kill; `--mail-type` includes `INVALID_DEPEND` | [sbatch(1)](https://slurm.schedmd.com/sbatch.html) |

### Portability — tested on this macOS box

`tail --pid` is GNU-only (BSD `tail` errors with ``unrecognized option `--pid=1'``); no
`flock`, no `fswatch`; GNU coreutils only as `gtail`. **Conclusion: never build a
portable wait on a foreign PID. Own the process, or own a marker file.**

## Approach

Per your decisions: **new skill + surgical edits**, **agnostic core with one
Claude Code reference**, **wrapper script + resume/status reader**.

### New skill: `skills/local/long-running-jobs/`

Frontmatter description (~600 chars, "pushy" per `skill-author` guidance):

> Decide how an agent should wait for work that outlives a turn — model
> training, Slurm/sbatch jobs, sweeps, long builds, backfills. Use when a job
> "takes hours" or "runs overnight", when the user says "check back when it's
> done", "wait for training to finish", or "run B after A finishes" — and
> especially when you are about to schedule a recurring check-in, cron
> heartbeat, or repeated squeue/nvidia-smi poll to babysit a run. Ranks the
> options: let the scheduler own the chain, block once in a backgrounded
> shell, stream filtered events, and only then fall back to scheduled
> wake-ups — plus durable exit-code markers so finished runs survive losing
> the session.

`SKILL.md` sections:

1. **The principle** — polling isn't the problem; polling with the model in the
   loop is. A shell `until` loop is free; a scheduled wake-up costs a context
   read per tick. Move the timer out of the context window.
2. **The ladder** — pick the highest tier that applies:

   | Tier | Mechanism | Use when |
   |---|---|---|
   | 0 | **Scheduler owns the chain.** Submit B with A. `JID=$(sbatch --parsable a.sbatch); JID=${JID%%;*}; sbatch --dependency=afterok:$JID --kill-on-invalid-dep=yes b.sbatch`; pueue `--after` | A→B pipeline. Survives session death entirely. **Default for the user's Phase A/B case.** |
   | 1 | **One blocking wait, backgrounded.** `Bash(run_in_background: true)` on a command that blocks (`sbatch --wait`, `wait $!`, `scripts/run-and-mark.sh`). Harness re-invokes on exit. | You need the agent to react at completion. Zero in-context polls. |
   | 2 | **Stream filtered events.** Monitor tool, or a backgrounded command emitting only milestone lines via `grep --line-buffered`. | You must react *mid-run* (OOM, early stopping), not just at the end. |
   | 3 | **Scheduled check-in.** `CronCreate` / `ScheduleWakeup`. | Last resort — remote system you cannot hold a handle to. Note the 7-day expiry, session-scoped firing, and per-tick context cost. |

3. **The invariant: completion must be durable** — orthogonal to tier. Every
   long run writes an atomic exit-code marker so a *new* session can recover
   without re-running. This is what makes losing the session survivable.
4. **Choosing** — a short decision flowchart.
5. **Gotchas** (all verified above): `afterany` is the default type; a failed
   parent leaves the child pending forever as `DependencyNeverSatisfied`, and
   requeuing the parent does not help; `--parsable` emits `jobid;cluster` so
   strip with `${JID%%;*}`; `,` is AND and `?` is OR; `sbatch --wait` returns 1
   for *any* signal death so an OOM and an `exit 1` look identical — read
   `sacct` for the true state; `tail --pid` is GNU-only; foreground `sleep` is
   blocked by the harness; recurring cron tasks expire after 7 days.
6. **Reference files** — with "read X when Y" load conditions.

References:

- `references/claude-code-mechanisms.md` — `run_in_background` notifies on exit;
  Monitor + until-loop and its absence-handling; `CronCreate` expiry/limits;
  blocked foreground `sleep`; plugin `monitors/monitors.json`; Channels as the
  push-direction alternative; version notes.
- `references/scheduler-chaining.md` — full Slurm `--dependency` matrix and
  traps, `--mail-type=INVALID_DEPEND`, `--signal=B:USR1@300` checkpointing,
  array/`aftercorr` semantics; pueue `--after`; DVC stage deps.
- `references/completion-contracts.md` — atomic marker writes (`write .tmp` +
  `mv`), exit-code capture, `sacct` state vocabulary
  (`TIMEOUT`/`OUT_OF_MEMORY`/`NODE_FAIL`/`CANCELLED`) and its `slurmdbd`
  dependency, shared-filesystem caveats, portability of wait primitives.

Scripts (repo conventions: `--help`, `--dry-run`, JSON on stdout, prose on
stderr, explicit exit codes, bash 3.2-compatible):

- `scripts/run-and-mark.sh` — runs `<command>` **as its own child** so plain
  `wait` works (no foreign-PID tricks), blocks, then atomically records
  completion. Launched once with `run_in_background: true`.
  ```
  run-and-mark.sh --marker-dir DIR --name NAME [--dry-run] -- <command> [args...]
    writes  DIR/NAME.exit   single integer, written to .tmp then mv'd
            DIR/NAME.meta   JSON: name, command, start, end, exit_code, host, pid
    stdout  one JSON object at completion
    stderr  two lines (start, end) — nothing per-tick
    exit    the command's exit code; 1 bad args; 2 marker dir unwritable
  ```
- `scripts/check-runs.sh` — reads a marker dir and reports what finished while
  the agent was away; the resume path after a session dies.
  ```
  check-runs.sh [--marker-dir DIR] [--name NAME] [--json]
    stdout  JSON array (--json) or aligned table
    exit    0 all recorded runs succeeded
            3 at least one run failed
            4 at least one run started but has no marker (killed / session died)
  ```

Asset: `assets/chained.sbatch.template` — Phase A/B with `--parsable`,
`afterok`, `--kill-on-invalid-dep=yes`, a `--signal=B:USR1@300` trap, and the
marker write.

### Edits to existing skills

- **`skills/local/slurm-hpc/SKILL.md`** — new `## Chaining and waiting` section
  after `## Resource requests`: `--parsable` + `${JID%%;*}`, the `--dependency`
  type table with `,` vs `?`, `sbatch --wait` and its exit-code semantics,
  `--mail-type=INVALID_DEPEND,END,FAIL`, `--kill-on-invalid-dep=yes`,
  `--signal=B:USR1@300`. Add the four new Gotchas bullets. Add a pointer: for
  the agent-side question ("how should *I* wait?"), see `long-running-jobs`.
  SKILL.md is only 90 lines, so this stays inline — no new reference file.
- **`skills/local/experiment-knowledge-harness/SKILL.md`** — expand
  `### 4. While the experiment runs`: before starting a long run, establish the
  marker contract; on session restart, reconcile `status: running` REPORT
  front-matter against actual markers instead of assuming; back a
  `depends-on: #NNN` edge with a real scheduler dependency when the runs are
  genuinely chained. **Mirror the same guidance into
  `assets/agent-guidance.md.template`** — that is what gets copied into target
  repos, so an edit to SKILL.md alone would not reach users.
- **`skills/local/pueue-job-queue/SKILL.md`** — one See-also line: pueue is the
  Tier 0/1 mechanism for local shell jobs; `long-running-jobs` owns the
  which-tier decision.

### Registration

- `skills/.claude-plugin/marketplace.json` — append `./local/long-running-jobs`
  to the `03-infra-and-docs` plugin's `skills[]` (where `slurm-hpc` and
  `pueue-job-queue` already live), then `make marketplace`.
- `pitfalls/slurm-dependent-job-pends-forever-after-failed-parent.md` — the
  `DependencyNeverSatisfied` trap, symptom-first per `CLAUDE.md`: verbatim
  symptom (`squeue` shows `PENDING`, `Reason=DependencyNeverSatisfied`), root
  cause, workaround, and the invariant (`--kill-on-invalid-dep=yes` +
  `--mail-type=INVALID_DEPEND`).
- Docs page — **optional, flagged**: `docs/skills/long-running-jobs.md` +
  `.zh-TW.md` + an `mkdocs.yml` nav entry. Note `slurm-hpc` and
  `experiment-knowledge-harness` currently have *no* docs pages, so skipping
  this is consistent with the status quo; adding it is a small improvement.
  Will confirm before doing it.

## Verification

1. **Lint** — `bash skills/local/skill-author/scripts/lint-skill.sh --strict
   skills/local/long-running-jobs`, and re-lint the two edited skills. Checks
   frontmatter, description trigger phrasing, `SKILL.md` < 500 lines, script
   shebang/`+x`/`--help`, and that every `references/*.md` is mentioned.
2. **Manifest** — `make marketplace` (catches broken paths, duplicates).
3. **Script surfaces** — `run-and-mark.sh --help`, `check-runs.sh --help`,
   and `run-and-mark.sh --dry-run` produce usage and a no-op plan.
4. **End-to-end, no cluster needed** — launch
   `run-and-mark.sh --marker-dir /tmp/lrj --name probe -- bash -c 'sleep 20; exit 7'`
   with `run_in_background: true`. Confirm: (a) a completion notification
   fires, (b) `/tmp/lrj/probe.exit` contains `7`, (c) `check-runs.sh --json`
   reports the failure and exits `3`. **This exercises the exact mechanism the
   skill recommends over cron polling.**
5. **Resume path** — `kill` the wrapper mid-run, then confirm `check-runs.sh`
   exits `4` (started, no marker) rather than reporting success.
6. **Slurm path** — if a cluster is reachable, `sbatch --test-only` against
   `assets/chained.sbatch.template`; otherwise `bash -n` the template and
   verify the `${JID%%;*}` extraction with a stubbed `sbatch` that echoes
   `12345;mycluster`.
7. **Real-world check** — apply Tier 0 to the actual Phase A → Phase B chain in
   the ConvertibleBond session and cancel the outstanding `CronCreate` tasks.

## Notes

- I ran a verification workflow whose Slurm/portability claims I ended up
  confirming directly (official `sbatch(1)` docs, plus live tests on this
  machine); I stopped it rather than let its design phase re-litigate choices
  you had already made.
- Remaining unknown, to resolve during implementation: shared-filesystem
  (NFS/Lustre) marker visibility latency — attribute caching means a marker
  written on a compute node may not be immediately visible to a watcher on the
  login node. `completion-contracts.md` will state this honestly rather than
  guess a number, and `check-runs.sh` will treat "no marker" as *unknown*
  (exit 4), never as success.
