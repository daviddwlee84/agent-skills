# Completion contracts

Designing a record of "this finished, and here is how it went" that outlives
the agent, the session, and the queue.

## Why this exists

The agent's context is the least durable place in the system. It is lost to
session exit, compaction, a dropped SSH connection, a closed laptop, or an OOM
in the harness itself. If the only evidence that Phase A succeeded lives there,
the recovery path is re-running the GPU time.

The filesystem and the scheduler's accounting database both outlive the agent.
Put the record there.

## The atomic marker

```bash
python train.py > runs/v2.log 2>&1
rc=$?
printf '%s\n' "$rc" > runs/v2.exit.tmp && mv runs/v2.exit.tmp runs/v2.exit
```

**Write to a temp name, then `mv`.** Within a single filesystem `mv` is a
`rename(2)`, which is atomic: a concurrent reader sees either no marker or a
complete one, never a half-written one. A plain `> runs/v2.exit` can be
observed empty between `open` and `write`, and an empty marker read as an exit
code is a silent success.

Two ways this breaks:

- **Across filesystems** `mv` degrades to copy-then-unlink and loses atomicity.
  Keep the `.tmp` in the same directory as the final marker — not in `/tmp`.
- **The writer dies before the `mv`.** By design: no marker means *unknown*,
  which is the correct reading.

`scripts/run-and-mark.sh` implements this, plus a `.meta` sidecar with the
command, host, timestamps, and pid.

## Absence is not success

The single most important rule when reading markers back:

| Observed | Means | Do |
|---|---|---|
| marker present, `0` | succeeded | proceed |
| marker present, non-zero | failed | report the code and the log |
| **no marker, never started** | not started | start it |
| **no marker, but started** | **unknown** — killed, node died, still running | **ask; do not re-run silently** |

`check-runs.sh` distinguishes the last two and exits `4` on unknown. Treating
unknown as "not done, so re-run" is how people accidentally launch a second
copy of an eight-hour job that is still running.

## Slurm: exit codes that outlive the queue

`scontrol show job <id>` is **live only** — the record disappears once the job
ages out of the controller's memory. For anything you will read later, use
`sacct`, which reads the accounting store.

```bash
sacct -j "$JID" --format=JobID,State,ExitCode,DerivedExitCode,Elapsed,MaxRSS --parsable2
```

### State vocabulary

| State | Meaning |
|---|---|
| `COMPLETED` | *"Job has terminated all processes on all nodes with an exit code of zero."* |
| `FAILED` | *"Job terminated with non-zero exit code or other failure condition."* |
| `CANCELLED` | *"Job was explicitly cancelled by the user or system administrator. The job may or may not have been initiated."* |
| `TIMEOUT` | *"Job terminated upon reaching its time limit."* |
| `OUT_OF_MEMORY` | *"Job experienced out of memory error."* |
| `NODE_FAIL` | *"Job terminated due to failure of one or more allocated nodes."* |
| `PREEMPTED` | *"Job terminated due to preemption."* |
| `BOOT_FAIL` | *"Job terminated due to launch failure, typically due to a hardware failure"* |
| `DEADLINE` | *"Job terminated on deadline."* |
| `REQUEUED` | *"Job was requeued."* |

`TIMEOUT`, `OUT_OF_MEMORY`, `NODE_FAIL`, and `PREEMPTED` are the four that mean
**"retry might work"** — as opposed to `FAILED`, which usually means your code
is wrong. Distinguishing them is the difference between a useful automated
retry and an infinite loop.

### ExitCode field

- `ExitCode` — *"The exit code returned by the job script or salloc, typically
  as set by the exit() function."*
- `DerivedExitCode` — *"The highest exit code returned by the job's job steps
  (srun invocations)."*
- Format is `exitcode:signal` — *"Following the colon is the signal that caused
  the process to terminate if it was terminated by a signal."*

This is why `sbatch --wait`'s exit code is not enough on its own: it collapses
*every* signal death to `1`. A `137` (SIGKILL, usually OOM) and a deliberate
`exit 1` are the same number to the caller. `sacct`'s `State` plus the `:signal`
suffix recovers the distinction.

### If accounting is not configured

`sacct` needs an accounting store — *"the job accounting log file or Slurm
database, as configured with the AccountingStorageType parameter"*. On a
cluster without `slurmdbd`, `sacct` may return nothing.

That is precisely the case where your **own** marker file is the system of
record, not a nicety. If `sacct -j "$JID"` comes back empty on a job you know
ran, stop relying on it and write markers.

## Shared filesystems

On NFS/Lustre/GPFS — i.e. every cluster — a marker written by a compute node is
not instantly visible on the login node. NFS caches file attributes
(`acregmin`/`acregmax`, typically a few seconds up to a minute) and provides
only close-to-open consistency.

Practical consequences:

- A watcher can observe "no marker" for some seconds *after* the job wrote one.
  Keep timeouts generous; never treat a single missing-marker observation as
  proof of failure.
- Have the writer `close()` the file before the reader looks — the
  temp-file-then-`mv` pattern gives you this, since `mv` happens after close.
- Do not build tight loops around marker appearance; you are polling a cache.

If you need a *fast* completion signal on a cluster, the scheduler is the
better source (`sacct`, or a Tier 0 dependency that never needs a signal at
all). Markers are for durability, not latency.

## Waiting primitives and their portability

Which of these you can actually use depends on the OS, and the answers are not
symmetric.

| Primitive | Works on | Notes |
|---|---|---|
| `wait "$PID"` | everywhere | **Children of the current shell only.** Cannot wait on a foreign pid. |
| `tail --pid=PID -f /dev/null` | GNU coreutils only | BSD/macOS `tail` rejects `--pid` outright. On macOS with Homebrew coreutils it is `gtail`. |
| `pidwait` | Linux, procps-ng | Not on macOS. |
| `inotifywait` | Linux, inotify-tools | **Races**: if the marker already exists when it starts, it blocks forever. Test first, then watch. |
| `fswatch` | macOS/Linux, but not preinstalled | |
| `flock` | Linux (util-linux) | Not on stock macOS. |
| `until <check>; do sleep N; done` | everywhere | Polling — and that is fine, because it is outside the model's context. |

**The design rule that falls out of this table:** own the process, or own a
marker. Attaching to a stranger's PID has no portable answer, so do not build
on it. `run-and-mark.sh` runs the command as its own child specifically so that
plain `wait` — the one primitive available everywhere — is sufficient.

If you must watch a marker rather than a process, the race-free shape is:

```bash
until [ -f "$MARKER" ]; do sleep 10; done     # test-then-sleep, not watch-then-hope
```

Boring, portable, correct, and free — as long as the model is not the thing
doing the looping.
