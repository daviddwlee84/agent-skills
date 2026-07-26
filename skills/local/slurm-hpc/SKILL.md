---
name: slurm-hpc
description: Generic Slurm/HPC know-how for any cluster. Use when the user writes or debugs sbatch/srun batch scripts, requests resources (--mem/--cpus-per-task/--gres/--time/partitions), reads job state with squeue/sacct/sinfo/scontrol, cancels jobs, or reasons about resource isolation — cgroup CPU/RAM limits and GPU GRES (gpu vs shard vs mps vs MIG) and which of them actually fence VRAM so a misbehaving job fails alone.
---

# slurm-hpc — generic Slurm workload-manager know-how

Portable Slurm reference for authoring batch jobs and reasoning about resource
isolation on any cluster. Not tied to a specific site — for a specific repo's
recipes and layout, prefer that project's own skill.

## When to use

- Writing or fixing an `sbatch` script, or an `srun` command line.
- Choosing resource requests (CPUs, memory, GPUs, time, partition).
- Reading job/queue/node state (`squeue`, `sacct`, `sinfo`, `scontrol`).
- Reasoning about what isolates jobs (cgroups) and what fences GPU VRAM.

## When NOT to use

- Operating a specific project's cluster with its own recipes → use that repo's skill.
- Designing cluster provisioning/config from scratch → that's admin work, not this.

## Batch script skeleton

```bash
#!/bin/bash
#SBATCH --job-name=train
#SBATCH --partition=<partition>       # see `sinfo`
#SBATCH --gres=gpu:1                  # GPUs (see GPU section)
#SBATCH --cpus-per-task=8
#SBATCH --mem=32G                     # per-node; enforced as a hard cgroup cap
#SBATCH --time=02:00:00               # job killed at this wall-clock limit
#SBATCH --output=logs/%x_%j.out       # %x=name %j=jobid
srun python train.py
```

Submit `sbatch script.sh`; inspect `squeue -j <id>`; after it ends,
`sacct -j <id> --format=JobID,State,ExitCode,Elapsed,MaxRSS,ReqTRES,AllocTRES`.
Cancel `scancel <id>`. `--start` on squeue estimates a pending job's start.

## Resource requests

- `--mem=<N>G` / `--mem-per-cpu=<N>G` — real memory; with cgroups this is a
  **hard cap** (see below). `--cpus-per-task` + `--ntasks` set core count.
- `--gres=gpu:N` or `--gres=gpu:<type>:N` (e.g. `gpu:a100:2`).
- `--time` is mandatory discipline on most clusters; jobs are killed at it.
- `--exclusive` gives the whole node. Partitions (`sinfo`) gate limits/priority.

## Chaining and waiting

Do not babysit a job by re-running `squeue` on a timer. Either hand the
sequencing to the scheduler, or block on it once.

**Chain B behind A** — Phase B is queued at submit time and runs without
anything staying connected:

```bash
JID=$(sbatch --parsable phase_a.sbatch); JID=${JID%%;*}   # strip ";cluster"
sbatch --dependency=afterok:"$JID" \
       --kill-on-invalid-dep=yes \
       --mail-type=INVALID_DEPEND,END,FAIL \
       phase_b.sbatch
```

| Dependency | Fires when the parent… |
|---|---|
| `afterok:<id>` | succeeded (exit 0) |
| `afternotok:<id>` | failed — the hook for alerting/cleanup |
| `afterany:<id>` | terminated, either way (**this is the default**) |
| `after:<id>[+min]` | started (optionally +minutes) |
| `aftercorr:<id>` | array task N follows parent array task N |
| `singleton` | previous job of the same name+user ended |

Separators: `,` means **all** must be satisfied, `?` means **any**.

**Block until done** (one command, exit code mirrors the job's):

```bash
sbatch --wait phase_a.sbatch
```

**Checkpoint before the wall-clock kill** — `--signal=B:USR1@300` sends
`SIGUSR1` to the batch shell 300 s before `--time` expires; trap it and save.
The `B:` prefix is what targets the batch shell rather than the job steps.

For the agent-side question — *how should I, the agent, wait for this?* — see
the `long-running-jobs` skill, which ranks scheduler chaining, one blocking
backgrounded wait, filtered event streaming, and scheduled check-ins.

## Isolation: what actually fences a misbehaving job

**CPU/RAM (cgroups, if the site enables `task/cgroup` + `ConstrainCores/RAMSpace`):**
a job is pinned to its cores (cpuset) and hard-capped at `--mem`. Exceeding
`--mem` triggers the **kernel cgroup OOM killer inside that job's cgroup only**
— the job dies alone; neighbours and the host are untouched. A thread-bomb
only saturates its own cores. This is real isolation and is the norm.

**GPU VRAM — the gap.** Allocating a GPU does NOT cap its memory:

| Method | VRAM isolation | Misbehaving job fails alone? |
|---|---|---|
| `--gres=gpu:N` (whole card) | n/a (owns it) | — |
| `--gres=shard:N` | **none** — accounting only | ❌ can OOM the whole card |
| `--gres=mps:N` (plain) | none | ❌ |
| `--gres=mps:N` + `CUDA_MPS_PINNED_DEVICE_MEM_LIMIT` | enforced cap | ✅ OOMs at its cap |
| **MIG** (`--gres=gpu:1g.5gb:1`) | **hardware slice** | ✅ strongest |

Read `references/gpu-isolation.md` when the task is specifically about capping
or partitioning GPU VRAM, or choosing between shard/mps/MIG.

## Reference files

- `references/gpu-isolation.md` — read when capping/partitioning GPU VRAM or
  choosing shard vs mps vs MIG; has the config snippets and enforcement details.

## Gotchas

- **`--gres=shard:N` and plain `--gres=mps:N` do NOT fence VRAM.** Sharing a
  GPU ≠ isolating it. Only MPS *with a pinned memory limit set*, or MIG,
  enforces a per-job VRAM ceiling. A job with a wrong batch size otherwise OOMs
  the whole card and takes down its neighbours.
- **MIG needs a datacenter GPU** (A100/A30/H100…); GeForce/RTX cards can't do it.
- **`--mem` is a hard cap under cgroups, not a hint.** A job that needs more
  gets OOM-killed; bump `--mem`, don't expect bursting into idle RAM.
- **`sacct` needs accounting (`slurmdbd`) configured.** Without it use
  `scontrol show job <id>` (live only — gone after the job ages out).
- **`afterany` is the default dependency type.** A bare `-d 12345` runs the
  child after the parent terminates *either way* — including after it crashed.
  Always spell out `afterok:`.
- **A failed parent leaves the child PENDING forever.** Slurm's default is
  *"the job stays pending with reason DependencyNeverSatisfied"*, which in
  `squeue` looks identical to waiting for resources. Worse, *"the dependent job
  will never be run, even if the preceding job is requeued"* — fixing and
  requeueing the parent does **not** release it; you must resubmit the child.
  Pass `--kill-on-invalid-dep=yes` and `--mail-type=INVALID_DEPEND`.
- **`--parsable` prints `jobid;cluster`**, not a bare id, when a cluster name is
  configured — *"The values are separated by a semicolon."* Strip it with
  `${JID%%;*}`, or the dependency string is malformed and the `;` truncates
  your shell command.
- **`sbatch --wait` collapses every signal death to exit 1.** *"If the job
  terminated due to a signal rather than a normal exit, the exit code will be
  set to 1."* An OOM kill, a `TIMEOUT`, a `scancel`, and a plain `exit 1` are
  indistinguishable from the exit code. Read
  `sacct -j <id> --format=State,ExitCode` for the real state — the `:signal`
  suffix and states like `OUT_OF_MEMORY` / `TIMEOUT` / `NODE_FAIL` are what
  tell you whether a retry could work. For arrays the code is *"the highest
  value for any task"*.
- **A failing site `Prolog`/`Epilog` drains the node**, showing jobs as
  `PENDING` with a node `Reason=`. Check `scontrol show node`.
- **`srun --oversubscribe` is ignored under consumable resources** — you can't
  opportunistically grab more than you requested.
