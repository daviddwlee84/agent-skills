# Scheduler chaining (Tier 0)

Making the *scheduler* own the "run B after A" transition, so no agent, session,
or laptop needs to stay alive for the pipeline to complete.

## Slurm

### The canonical chain

```bash
#!/usr/bin/env bash
set -euo pipefail

JID=$(sbatch --parsable phase_a.sbatch)
JID=${JID%%;*}                      # strip ";cluster" — see Gotchas

sbatch --parsable \
       --dependency=afterok:"$JID" \
       --kill-on-invalid-dep=yes \
       --mail-type=INVALID_DEPEND,END,FAIL \
       phase_b.sbatch
```

Four things are doing work here, and dropping any one of them is a known way to
get burned:

| Piece | Why |
|---|---|
| `--parsable` | Machine-readable job id. Without it you are parsing "Submitted batch job 12345" with `awk`. |
| `${JID%%;*}` | `--parsable` *"Outputs only the job ID number and the cluster name if present. The values are separated by a semicolon."* |
| `afterok:` (explicit) | The default type is `afterany` — Phase B would run on a crashed Phase A. |
| `--kill-on-invalid-dep=yes` | Otherwise a failed Phase A leaves Phase B pending **forever**. |

### Dependency types

| Type | Semantics (from `sbatch(1)`) |
|---|---|
| `after:job_id[+time]` | *"After the specified jobs start or are cancelled and 'time' … happens, this job can begin execution."* |
| `afterany:job_id` | *"This job can begin execution after the specified jobs have terminated. **This is the default dependency type.**"* |
| `afterok:job_id` | *"…after the specified jobs have successfully executed (ran to completion with an exit code of zero)."* |
| `afternotok:job_id` | *"…after the specified jobs have terminated in some failed state (non-zero exit code, node failure, timed out, etc)."* |
| `aftercorr:job_id` | *"A task of this job array can begin execution after the corresponding task ID in the specified job has completed successfully."* Element-wise array chaining. |
| `afterburstbuffer:job_id` | …after termination *and* burst-buffer stage-out completes. |
| `singleton` | *"…after any previously launched jobs sharing the same job name and user have terminated."* |

Separators: *"All dependencies must be satisfied if the `,` separator is used.
Any dependency may be satisfied if the `?` separator is used."* — `,` is AND,
`?` is OR.

`afternotok` is the useful one people forget: it gives you a cleanup or
alerting job that runs **only** on failure.

```bash
sbatch --dependency=afternotok:"$JID" --kill-on-invalid-dep=yes notify_failure.sbatch
```

### The dependency trap

This is the single most expensive Slurm gotcha for a chained pipeline.

> *"By default the job stays pending with reason DependencyNeverSatisfied or if
> the `kill_invalid_depend` is specified in slurm.conf the job is terminated."*

> *"Once a job dependency fails due to the termination state of a preceding job,
> the dependent job will never be run, even if the preceding job is requeued and
> has a different termination state in a subsequent execution."*

Consequences:

1. If Phase A fails, Phase B **does not fail** — it *pends indefinitely*. In
   `squeue` it looks identical to a job waiting for resources. You can lose days
   to this before noticing.
2. Fixing Phase A and requeueing it does **not** release Phase B. You must
   resubmit Phase B.
3. Whether it hangs or gets cancelled depends on a **site-wide** `slurm.conf`
   setting you probably do not control — so set it per-job:
   `--kill-on-invalid-dep=yes` (*"A terminated job state will be
   JOB_CANCELLED."*).

Diagnose with:

```bash
squeue -j "$JID" -o '%.10i %.9T %.40R'      # Reason column shows DependencyNeverSatisfied
scontrol show job "$JID" | grep -i reason
```

And make it announce itself: `--mail-type=INVALID_DEPEND`.

### Array jobs

- Plain `afterok:<array_job_id>` waits for the **whole array**.
- `aftercorr:<array_job_id>` chains **task N to task N**, so element 7 of Phase B
  starts as soon as element 7 of Phase A succeeds. *"If the specified job is not
  an array, this is treated the same as afterok."*
- Mail: *"Unless the ARRAY_TASKS option is specified, mail notifications on job
  BEGIN, END, FAIL and REQUEUE apply to a job array as a whole rather than
  generating individual email messages for each task."*

`aftercorr` is the right tool for a per-seed train → per-seed eval sweep.

### Checkpoint before the wall-clock kill

`--time` is a hard kill. To checkpoint first, ask Slurm to signal you early:

```bash
#SBATCH --time=08:00:00
#SBATCH --signal=B:USR1@300     # SIGUSR1 to the batch shell, 300s before the end
```

*"Use the `B:` option to signal only the batch shell, none of the other
processes will be signaled."* Without `B:`, the signal goes to the job steps
instead — which is what you want only if the training process itself traps it.

The batch script must actually trap it:

```bash
checkpoint_and_requeue() {
  kill -USR1 "$TRAIN_PID" 2>/dev/null || true   # ask trainer to save
  wait "$TRAIN_PID"
  scontrol requeue "$SLURM_JOB_ID"
}
trap checkpoint_and_requeue USR1

python train.py & TRAIN_PID=$!
wait "$TRAIN_PID"
```

The 300s budget must exceed your actual checkpoint-write time, or you have
built an elaborate way to still lose the checkpoint.

### `--mail-type` values

`NONE`, `BEGIN`, `END`, `FAIL`, `REQUEUE`, `ALL`, `INVALID_DEPEND`,
`STAGE_OUT`, `TIME_LIMIT`, `TIME_LIMIT_90`, `TIME_LIMIT_80`, `TIME_LIMIT_50`,
`ARRAY_TASKS`.

For a chained pipeline: `--mail-type=INVALID_DEPEND,END,FAIL,TIME_LIMIT`.

## pueue

For local shell jobs. Dependencies are **AND-only and success-only** — which
maps onto `afterok:a,b` and nothing else. No OR, no run-on-failure, no retry.

This repo's `pueue-job-queue` skill already wraps id extraction defensively;
prefer its script over raw `pueue add`, and use its `wait.py` for Tier 1:

```bash
P=skills/local/pueue-job-queue/scripts
A=$("$P"/submit.sh --label phase-a -- ./phase_a.sh | jq -r .task_id)
"$P"/submit.sh --label phase-b --after "$A" -- ./phase_b.sh

"$P"/wait.py --label-prefix phase- --fail-fast     # blocking; JSON summary
```

For anything with conditional branching, OR-dependencies, or
retry-with-backoff, pueue is the wrong layer — escalate to a real orchestrator
(see that skill's "When NOT to use").

## DVC

If the work is already a `dvc.yaml` pipeline, the DAG *is* the chain: `dvc repro`
runs stages in dependency order and skips unchanged ones. Chaining Phase A and
Phase B means declaring B's `deps` to include A's `outs` — not scheduling
anything. See the `dvc-ml-workflow` skill.

## Choosing a Tier 0 mechanism

| Situation | Use |
|---|---|
| Cluster job, next step known at submit time | Slurm `--dependency` |
| Per-element sweep chaining | Slurm `aftercorr` with arrays |
| Local shell jobs, capped parallelism | pueue `--after` |
| Reproducible artifact pipeline | DVC stage deps |
| Next step depends on *inspecting* results | No Tier 0 — use Tier 1 and decide when you wake |

That last row matters. Tier 0 requires knowing the next command **before** the
first one finishes. When the next step genuinely depends on a judgement call
about the results, a blocking Tier 1 wait is the honest choice — you are not
avoiding the agent, you are just not paying it to idle.
