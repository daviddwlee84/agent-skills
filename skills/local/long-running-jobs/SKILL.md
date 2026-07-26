---
name: long-running-jobs
description: Decide how an agent should wait for work that outlives a turn — training runs, Slurm/sbatch jobs, sweeps, long builds. Use when a job "takes hours" or "runs overnight", the user says "check back when it's done", "wait for training to finish", or "run B after A finishes" — and especially when you are about to schedule a recurring check-in or repeated squeue poll to babysit a run. Ranks scheduler chaining, one blocking backgrounded wait, event streams, then scheduled wake-ups last.
---

# long-running-jobs

How an agent should wait for work that outlives a single turn.

## The principle

**Polling is not the problem. Polling with the model inside the loop is.**

```
until squeue -h -j "$JID" | grep -q .; do sleep 60; done   # 8 hours, ~0 tokens
```
```
CronCreate("check training") -> wake -> squeue -> "still epoch 21" -> reschedule
                                                  # 1 full context read PER TICK
```

Both poll. Only one charges you a context window every 60 seconds. When a
session is carrying 400k+ tokens, a scheduled heartbeat is the single most
expensive way to learn that nothing has changed.

So the goal is never "avoid polling". It is **move the timer out of the
context window** — into the scheduler, into a blocked shell, or onto disk.

## When to use

- A job "takes hours", "runs overnight", or "will finish tomorrow morning".
- The user says "check back when it's done" / "wait for training to finish" /
  "let me know when the job lands".
- Phase A → Phase B chaining: "run the eval after the training finishes".
- **You are about to arm a recurring check-in or repeat a `squeue` /
  `nvidia-smi` / `ls checkpoints/` poll to see whether something finished.**
  That impulse is the trigger.

## When NOT to use

- The command finishes in seconds or a couple of minutes — just run it.
- You want run-level metrics, curves, or parameter tracking → `mlflow-tracking`.
- You want to record what the run *meant* → `experiment-knowledge-harness`.
- You need the Slurm resource-request or GPU-isolation details themselves →
  `slurm-hpc`.

## The ladder

Pick the **lowest-numbered tier that applies**. Do not skip down because a
higher tier needs a little setup — the setup is the point.

| Tier | Mechanism | Use when |
|---|---|---|
| **0** | **The scheduler owns the chain.** Submit B at the same time as A, with a dependency. | There is a next step. Survives session death, compaction, laptop sleep, and agent restarts entirely. |
| **1** | **One blocking wait, backgrounded.** A command that blocks until done, launched once in the background. The harness wakes you when it exits. | You need to *react* at completion. Zero in-context polls while waiting. |
| **2** | **Stream filtered events.** A background command that prints only milestone lines. | You must react *mid-run* — OOM, early stopping, a metric crossing a threshold — not just at the end. |
| **3** | **Scheduled check-in.** A cron / wake-up prompt. | Last resort. Nothing above can reach the job (e.g. a remote system you hold no handle to). |

### Tier 0 — let the scheduler own the chain

The agent is not involved in the transition at all. This is almost always
right for "run B after A finishes".

```bash
# Slurm. Note the ${JID%%;*} — --parsable emits "jobid;cluster" when a
# cluster name is configured, and "afterok:123;mycluster" is not a job id.
JID=$(sbatch --parsable phase_a.sbatch); JID=${JID%%;*}

sbatch --dependency=afterok:"$JID" \
       --kill-on-invalid-dep=yes \
       --mail-type=INVALID_DEPEND,END,FAIL \
       phase_b.sbatch
```

```bash
# pueue (local shell jobs). Use the pueue-job-queue skill's wrapper — it
# already handles defensive id parsing and emits JSON.
P=skills/local/pueue-job-queue/scripts
A=$("$P"/submit.sh --label phase-a -- ./phase_a.sh | jq -r .task_id)
"$P"/submit.sh --label phase-b --after "$A" -- ./phase_b.sh
```

`--kill-on-invalid-dep=yes` is **not optional**. See Gotchas.

### Tier 1 — one blocking wait, backgrounded

Launch a command that blocks until the work is done, in the background. The
harness re-invokes you when it exits, so you spend nothing while waiting.

```bash
sbatch --wait phase_a.sbatch          # blocks; exit code mirrors the job's
```
```bash
scripts/run-and-mark.sh --marker-dir .runs --name v2_full -- python train.py
```

Launch it **once**, backgrounded — not in a loop, and not in the foreground.
If your harness exposes a background flag on its shell tool, that is the one to
use; see `references/claude-code-mechanisms.md` for the Claude Code specifics,
including which mechanism actually wakes you on completion and which does not.

For a job you did **not** start and hold no handle to, block on a condition in
a subshell rather than in your context:

```bash
until ! squeue -h -j "$JID" | grep -q .; do sleep 60; done
sacct -j "$JID" --format=State,ExitCode --noheader
```

### Tier 2 — stream filtered events

Only when you need to act before the end. Filter **in the shell**, never by
feeding raw logs into context:

```bash
tail -F runs/v2_full.log \
  | stdbuf -oL grep --line-buffered -E \
      'Training complete|Early stopping|CUDA out of memory|Traceback'
```

A bare `tail -F` on a training log is an anti-pattern: every epoch line becomes
an event and you have reinvented the expensive poll with extra steps.

### Tier 3 — scheduled check-in

Legitimate only when no handle exists — a job on a machine you cannot hold a
blocking connection to. If you land here, make each tick cheap: check one thing
and report one line. Know your scheduler's limits (in Claude Code: session-
scoped, and recurring tasks expire after 7 days — see
`references/claude-code-mechanisms.md`).

## The invariant: completion must be durable

Orthogonal to all four tiers. **Whatever waits, something must survive not
waiting.**

Sessions die, contexts compact, laptops sleep, SSH drops. If the only record
that Phase A succeeded is in the agent's context, that record is one disconnect
from gone — and the usual recovery is re-running eight hours of GPU time.

So every long run writes an atomic completion marker:

```bash
python train.py; rc=$?
printf '%s\n' "$rc" > runs/v2.exit.tmp && mv runs/v2.exit.tmp runs/v2.exit
```

`mv` within one filesystem is atomic, so a reader never sees a half-written
marker — it sees either no marker or a complete one. `scripts/run-and-mark.sh`
does this for you; `scripts/check-runs.sh` reads the markers back and tells a
fresh session what finished while it was away.

**Absence of a marker means "unknown" — never "failed", never "fine".** A run
that started and has no marker was probably killed. That is exit code 4 from
`check-runs.sh`, and it is a question for the user, not something to silently
re-run.

## Choosing

```
Is there a next step to run after this one?
├─ yes → Tier 0: submit it now with a dependency. Done — you are not in the loop.
└─ no  → Do you need to react before the end (OOM, early stop, threshold)?
         ├─ yes → Tier 2: stream, filtered at the shell.
         └─ no  → Can you hold a blocking handle on the work?
                  ├─ yes → Tier 1: one blocking command, backgrounded.
                  └─ no  → Tier 3: scheduled check-in, cheapest possible tick.

In every branch: the job writes a durable exit-code marker.
```

## Available scripts

- **`scripts/run-and-mark.sh`** — run something long as a child process, block
  until it exits, record completion atomically. Launch **once**, backgrounded.
  - Flags: `--help`, `--dry-run`, `--marker-dir DIR`, `--name NAME`, `-- <cmd>`
- **`scripts/check-runs.sh`** — report what finished while you were away; the
  resume path after a session dies.
  - Flags: `--help`, `--marker-dir DIR`, `--name NAME`, `--json`

```bash
scripts/run-and-mark.sh --marker-dir .runs --name v2_full -- python train.py
scripts/check-runs.sh --marker-dir .runs --json
```

## Bundled assets

- `assets/chained.sbatch.template` — a Phase A / Phase B pair wired with
  `--parsable`, `afterok`, `--kill-on-invalid-dep=yes`, a `SIGUSR1` checkpoint
  trap, and the durable marker write. Copy and edit rather than hand-rolling
  the dependency plumbing.

## Reference files

- `references/claude-code-mechanisms.md` — read when working inside Claude Code
  and you need to know *which* mechanism implements each tier: which one wakes
  you on completion, why foreground `sleep` is blocked, and the scheduler's
  limits.
- `references/scheduler-chaining.md` — read when building a Tier 0 chain: the
  full Slurm `--dependency` matrix, array / `aftercorr` semantics,
  checkpointing before the wall-clock kill, plus pueue and DVC equivalents.
- `references/completion-contracts.md` — read when designing the durable
  record: atomic marker writes, capturing an exit code that outlives the queue,
  `sacct` state vocabulary, and shared-filesystem caveats.

## Gotchas

- **`afterany` is Slurm's default dependency type.** A bare `-d 12345` means
  "after it terminates, success *or* failure" — which will happily run Phase B
  on top of a crashed Phase A. Always write the type: `-d afterok:12345`.
- **A failed parent leaves the child pending forever.** Slurm's default is
  *"the job stays pending with reason DependencyNeverSatisfied"* — not
  cancellation. It sits in the queue indefinitely, looking like it is merely
  waiting its turn. Worse: *"Once a job dependency fails due to the termination
  state of a preceding job, the dependent job will never be run, even if the
  preceding job is requeued"* — so fixing and requeueing Phase A does **not**
  release Phase B. Always pass `--kill-on-invalid-dep=yes`, and add
  `--mail-type=INVALID_DEPEND` so a hang announces itself.
- **`--parsable` prints `jobid;cluster`**, not a bare id, when a cluster name is
  configured. Strip it with `JID=${JID%%;*}`. Skipping this builds
  `--dependency=afterok:123;mycluster` — and the `;` also terminates the shell
  command.
- **`,` is AND, `?` is OR** in a dependency list: *"All dependencies must be
  satisfied if the `,` separator is used. Any dependency may be satisfied if the
  `?` separator is used."*
- **`sbatch --wait` returns 1 for any signal death.** *"If the job terminated
  due to a signal rather than a normal exit, the exit code will be set to 1."*
  An OOM kill, a wall-clock `TIMEOUT`, a `scancel`, and a plain `exit 1` are
  indistinguishable from the exit code alone. Read `sacct -j "$JID"
  --format=State,ExitCode` for the real story. For a job array the recorded code
  is *"the highest value for any task"*.
- **`tail --pid=PID` is GNU-only.** BSD/macOS `tail` rejects it outright
  (`unrecognized option`), and macOS ships no `flock` and no `fswatch` by
  default. Do not build a portable wait on someone else's PID — **own the
  process** (so plain `wait` works) **or own a marker file**. Shell `wait` only
  ever works on children of the current shell.
- **`inotifywait` on a marker file races.** If the marker is created before
  `inotifywait` starts, it blocks forever. Test for the marker first, *then*
  watch. (Linux-only regardless — there is no portable equivalent.)
- **On a shared filesystem a marker is not instantly visible.** NFS attribute
  caching means a marker written on a compute node can lag on the login node.
  Treat "no marker yet" as unknown and keep timeouts generous.

## See also

- `slurm-hpc` — writing the batch scripts these tiers submit.
- `pueue-job-queue` — a local Tier 0/1 implementation with its own blocking
  `wait.py`, group parallelism, and JSON status.
- `experiment-knowledge-harness` — recording what the run *meant* once it lands.
