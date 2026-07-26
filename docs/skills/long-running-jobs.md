# long-running-jobs

Decide **how an agent should wait** for work that outlives a single turn —
training runs, Slurm jobs, sweeps, long builds. The skill exists because the
obvious approach is the expensive one.

## The problem it solves

An agent babysitting an 8-hour training run tends to arm a scheduled check-in:
wake at 16:31, run `squeue`, see "still epoch 21", schedule the next wake-up.
It works, and it is the worst option available.

> **Polling is not the problem. Polling with the model inside the loop is.**

```
until squeue -h -j "$JID" | grep -q .; do sleep 60; done   # 8 hours, ~0 tokens
```
```
CronCreate -> wake -> squeue -> "still epoch 21" -> reschedule
                                # 1 full context read PER TICK
```

Both poll. In a session carrying 400k+ tokens, only one of them costs a context
window every 60 seconds. The skill's whole thesis is **move the timer out of
the context window** — into the scheduler, a blocked shell, or onto disk.

## The ladder

Pick the lowest-numbered tier that applies.

| Tier | Mechanism | Use when |
|---|---|---|
| **0** | Scheduler owns the chain (`sbatch --dependency=afterok`, `pueue --after`) | There is a next step. Survives session death, compaction, laptop sleep. |
| **1** | One blocking wait, backgrounded (`sbatch --wait`, `run-and-mark.sh`) | You must react at completion. Zero in-context polls. |
| **2** | Stream shell-filtered events | You must react *mid-run* — OOM, early stopping, a threshold. |
| **3** | Scheduled check-in | Last resort: a remote system you hold no handle to. |

Tier 0 is the one people skip. It requires knowing the next command *before* the
first finishes — and when you do, the agent is removed from the loop entirely.

## The invariant

Orthogonal to all four tiers: **whatever waits, something must survive not
waiting.**

```bash
python train.py; rc=$?
printf '%s\n' "$rc" > runs/v2.exit.tmp && mv runs/v2.exit.tmp runs/v2.exit
```

Temp-file-then-`mv` is a `rename(2)` within one filesystem, so a reader sees
either no marker or a complete one — never a half-written exit code read as
success.

The reading rule that falls out of it:

| Observed | Means |
|---|---|
| marker, `0` | succeeded |
| marker, non-zero | failed |
| no marker, never started | not started |
| **no marker, but started** | **unknown** — killed, node died, *or still running* |

**Absence is never success and never failure.** Treating "unknown" as "not done,
so re-run" is how you end up with two copies of an eight-hour job.

| Surface | Question it answers |
|---|---|
| `run-and-mark.sh` | "Run this, block, and leave a record that outlives my session." |
| `check-runs.sh` | "What finished while I was away?" |
| [`references/claude-code-mechanisms.md`](https://github.com/daviddwlee84/agent-skills/blob/main/skills/local/long-running-jobs/references/claude-code-mechanisms.md) | "Which harness tool implements each tier?" |
| [`references/scheduler-chaining.md`](https://github.com/daviddwlee84/agent-skills/blob/main/skills/local/long-running-jobs/references/scheduler-chaining.md) | "How do I wire Phase A → Phase B so nothing has to stay awake?" |
| [`references/completion-contracts.md`](https://github.com/daviddwlee84/agent-skills/blob/main/skills/local/long-running-jobs/references/completion-contracts.md) | "How do I record completion so it survives the queue and the session?" |
| [`assets/chained.sbatch.template`](https://github.com/daviddwlee84/agent-skills/blob/main/skills/local/long-running-jobs/assets/chained.sbatch.template) | "Give me the dependency plumbing already correct." |

## Two facts worth the skill's existence

**Backgrounded shell commands wake the agent on exit.** Verified by experiment
against Claude Code 2.1.220, and stated in the harness's own guidance:

> "Use the Monitor tool to stream events from a background process (each stdout
> line is a notification). For one-shot \"wait until done,\" use Bash with
> `run_in_background` instead."

This makes Tier 1 a single call, not a loop. Public documentation summaries
claiming the agent must poll for completion are stale — the skill says so
explicitly, because acting on the stale version reintroduces the polling the
skill is trying to remove.

**A failed Slurm parent leaves its child pending forever.** From `sbatch(1)`:

> "By default the job stays pending with reason DependencyNeverSatisfied"

> "Once a job dependency fails due to the termination state of a preceding job,
> the dependent job will never be run, even if the preceding job is requeued"

So Phase B does not fail when Phase A does — it parks indefinitely, looking in
`squeue` exactly like a job waiting its turn, and requeueing Phase A does not
release it. Every chain in the skill therefore carries
`--kill-on-invalid-dep=yes` and `--mail-type=INVALID_DEPEND`. This one has its
own [pitfall page](https://github.com/daviddwlee84/agent-skills/blob/main/pitfalls/slurm-dependent-job-pends-forever-after-failed-parent.md).

## When the skill triggers

- A job "takes hours" / "runs overnight" / "will finish tomorrow morning".
- "Check back when it's done", "wait for training to finish", "run B after A".
- **You are about to arm a recurring check-in, or repeat a `squeue` /
  `nvidia-smi` / `ls checkpoints/` poll to see whether something finished.**
  That impulse is the trigger.

## When it doesn't

- The command finishes in seconds — just run it.
- Metrics, curves, parameter tracking → `mlflow-tracking`.
- Recording what the run *meant* → `experiment-knowledge-harness`.
- Resource requests and GPU isolation → `slurm-hpc`.

## Structure

```
skills/local/long-running-jobs/
├── SKILL.md                                # the ladder, the invariant, 8 gotchas
├── scripts/
│   ├── run-and-mark.sh                     # bash 3.2; own the child, block, atomic marker
│   └── check-runs.sh                       # bash 3.2; marker reader, exit 0/3/4
├── references/
│   ├── claude-code-mechanisms.md           # which tool per tier; blocked foreground sleep; cron limits
│   ├── scheduler-chaining.md               # Slurm dependency matrix + traps; pueue; DVC
│   └── completion-contracts.md             # atomic markers; sacct states; wait-primitive portability
└── assets/
    └── chained.sbatch.template             # Phase A/B chain, correct by construction
```

## Own the process, or own a marker

The portability table in `completion-contracts.md` drives one design decision
worth calling out:

| Primitive | Works on |
|---|---|
| `wait "$PID"` | everywhere — **children of the current shell only** |
| `tail --pid=PID` | GNU coreutils only; BSD/macOS `tail` rejects it |
| `pidwait` | Linux (procps-ng) |
| `inotifywait` | Linux; **races** if the marker predates the watch |
| `flock` / `fswatch` | not on stock macOS |

There is no portable way to wait on a *foreign* PID. So `run-and-mark.sh` runs
its command as its own child, which makes plain `wait` — the one primitive
available everywhere — sufficient.

## Verification

Every claim in the skill was tested rather than assumed:

```bash
bash skills/local/skill-author/scripts/lint-skill.sh --strict skills/local/long-running-jobs

# exit-code contract, under stock macOS bash 3.2
/bin/bash scripts/run-and-mark.sh --marker-dir .r --name ok  -- /bin/sh -c 'exit 0'   # 0
/bin/bash scripts/run-and-mark.sh --marker-dir .r --name oom -- /bin/sh -c 'kill -9 $$'  # 137
/bin/bash scripts/check-runs.sh --marker-dir .r --json | python3 -m json.tool
```

- Backgrounding `run-and-mark.sh` fires a real completion notification carrying
  the command's exit code — the Tier 1 mechanism, proven end to end.
- `SIGKILL` is preserved as **137**, so an OOM stays distinguishable from
  `exit 1` — which `sbatch --wait` alone cannot do (it collapses every signal
  death to `1`).
- A stubbed `sbatch` emitting `999;clus` yields `--dependency=afterok:999`,
  confirming the `${JID%%;*}` cluster-suffix strip.
- `check-runs.sh` returns `4` for unknown ahead of `3` for failed — unknown is
  the state that needs a human, so it outranks.
