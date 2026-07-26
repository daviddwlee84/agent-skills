# Chained Slurm job sits `PENDING` forever with `DependencyNeverSatisfied`

## Symptom

You submitted a Phase A → Phase B chain, Phase A failed, and Phase B is still
sitting in the queue hours later. `squeue` looks like it is merely waiting its
turn:

```
$ squeue -j 4471903 -o '%.10i %.9T %.40R'
     JOBID     STATE                                   REASON
   4471903   PENDING                 (DependencyNeverSatisfied)
```

```
$ scontrol show job 4471903 | grep -i reason
   JobState=PENDING Reason=DependencyNeverSatisfied Dependency=afterok:4471902(failed)
```

It will never run. It will also never fail, never time out, and never send a
`FAIL` mail — so nothing tells you unless you look. The usual way to discover
this is noticing the next morning that the eval never produced results.

Second, sharper symptom: you fix the bug in Phase A, requeue it, watch it
succeed — **and Phase B still does not start.**

## Root cause

Two separate Slurm behaviours compound.

**1. The default is to hang, not to cancel.** From `sbatch(1)`:

> By default the job stays pending with reason DependencyNeverSatisfied or if
> the `kill_invalid_depend` is specified in slurm.conf the job is terminated.

Whether an unsatisfiable dependency hangs or gets cancelled is a **site-wide
`slurm.conf` setting** you probably do not control. On a cluster that has not
set `kill_invalid_depend`, the dependent job is parked indefinitely.

**2. The dependency verdict is permanent.** Also from `sbatch(1)`:

> Once a job dependency fails due to the termination state of a preceding job,
> the dependent job will never be run, even if the preceding job is requeued
> and has a different termination state in a subsequent execution.

The failure is recorded against the dependency itself, not re-evaluated. So
requeueing the parent cannot rescue the child.

A third, quieter variant of the same trap: writing `-d 12345` without a type.
`afterany` is the **default** dependency type, so the child runs after the
parent terminates *either way* — happily evaluating a checkpoint that a crashed
training run never finished writing.

## Workaround

Cancel and resubmit the child. There is no way to release it in place:

```bash
scancel 4471903
JID=$(sbatch --parsable phase_a.sbatch); JID=${JID%%;*}
sbatch --dependency=afterok:"$JID" --kill-on-invalid-dep=yes phase_b.sbatch
```

## Prevention

Submit every dependent job with all three of these:

```bash
sbatch --dependency=afterok:"$JID" \
       --kill-on-invalid-dep=yes \
       --mail-type=INVALID_DEPEND,END,FAIL \
       phase_b.sbatch
```

| Flag | Buys you |
|---|---|
| `afterok:` spelled out | the child does not run on a crashed parent (`afterany` is the default) |
| `--kill-on-invalid-dep=yes` | the child is **cancelled** instead of parked — *"A terminated job state will be JOB_CANCELLED"* — regardless of site config |
| `--mail-type=INVALID_DEPEND` | you are told, instead of finding out tomorrow |

**Invariant:** a job chained with `afterok` must always carry
`--kill-on-invalid-dep=yes`. A silent indefinite pend is strictly worse than a
loud failure — it consumes a queue slot, produces no output, and looks normal.

`skills/local/long-running-jobs/assets/chained.sbatch.template` wires all of
this up; the trap is also in that skill's Gotchas and in `slurm-hpc`.

## See also

- `skills/local/long-running-jobs/references/scheduler-chaining.md` — full
  dependency-type matrix, `,` (AND) vs `?` (OR), and `aftercorr` for arrays.
- `skills/local/slurm-hpc/SKILL.md` — `## Chaining and waiting`.
