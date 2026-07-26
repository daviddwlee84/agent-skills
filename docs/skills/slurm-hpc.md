# slurm-hpc

Portable Slurm know-how for **any** cluster — authoring `sbatch` scripts,
choosing resource requests, chaining jobs, and reasoning about what actually
isolates a misbehaving job. Deliberately site-agnostic: for one cluster's
specific partitions and recipes, that repo's own skill wins.

| Surface | Question it answers |
|---|---|
| Batch script skeleton | "What does a correct `#SBATCH` header look like?" |
| Resource requests | "What do `--mem` / `--cpus-per-task` / `--gres` / `--time` actually enforce?" |
| Chaining and waiting | "How do I run B after A without babysitting the queue?" |
| Isolation section | "If my neighbour's job goes wrong, do I go down with it?" |
| `references/gpu-isolation.md` | "How do I cap GPU VRAM — shard vs MPS vs MIG?" |

## The question the skill is really built around

**Does a misbehaving job fail alone?** For CPU and RAM, yes: with
`task/cgroup` the job is pinned to its cores and hard-capped at `--mem`, and
exceeding it triggers the kernel OOM killer *inside that job's cgroup only*.
Neighbours are untouched.

For GPU memory, **allocating a GPU does not cap its memory** — and the options
differ in whether they actually fence anything:

| Method | VRAM isolation | Fails alone? |
|---|---|---|
| `--gres=gpu:N` (whole card) | n/a (owns it) | — |
| `--gres=shard:N` | **none** — accounting only | ❌ can OOM the whole card |
| `--gres=mps:N` (plain) | none | ❌ |
| `--gres=mps:N` + `CUDA_MPS_PINNED_DEVICE_MEM_LIMIT` | enforced cap | ✅ |
| **MIG** (`--gres=gpu:1g.5gb:1`) | **hardware slice** | ✅ strongest |

Sharing a GPU is not the same as isolating one. Slurm's own docs say sharding
"does not fence the processes" — so a wrong batch size takes down the card and
its neighbours. `references/gpu-isolation.md` has the `slurm.conf` / `gres.conf`
snippets, the TaskProlog wiring for the MPS memory limit, and the MIG
prerequisites.

## Chaining and waiting

Added because the skill previously had **no** answer to "how do I run B after
A?" — only one-shot `squeue` / `sacct` inspection.

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
| `afternotok:<id>` | failed — the hook for alerting / cleanup |
| `afterany:<id>` | terminated, either way (**the default**) |
| `after:<id>[+min]` | started |
| `aftercorr:<id>` | array task N follows parent array task N |
| `singleton` | previous job of the same name+user ended |

`,` means **all** must be satisfied; `?` means **any**.

To block instead of chain: `sbatch --wait` — *"Do not exit until the submitted
job terminates"*, with the job's exit code.

For the agent-side question — *how should **I** wait?* — the skill defers to
[`long-running-jobs`](long-running-jobs.md), which ranks scheduler chaining,
one blocking backgrounded wait, filtered event streams, and scheduled
check-ins.

## The four gotchas that cost the most

- **`afterany` is the default dependency type.** A bare `-d 12345` runs the
  child after the parent terminates *either way* — including after it crashed.
  Always spell out `afterok:`.
- **A failed parent leaves the child `PENDING` forever.** Slurm's default is
  *"the job stays pending with reason DependencyNeverSatisfied"*, which looks
  identical to waiting for resources; and *"the dependent job will never be
  run, even if the preceding job is requeued"*. Pass
  `--kill-on-invalid-dep=yes`. This has its own
  [pitfall page](https://github.com/daviddwlee84/agent-skills/blob/main/pitfalls/slurm-dependent-job-pends-forever-after-failed-parent.md).
- **`--parsable` prints `jobid;cluster`**, not a bare id, when a cluster name
  is configured. Strip with `${JID%%;*}` — otherwise the dependency string is
  malformed *and* the `;` truncates your shell command.
- **`sbatch --wait` collapses every signal death to exit 1.** An OOM kill, a
  `TIMEOUT`, a `scancel`, and a plain `exit 1` are indistinguishable. Read
  `sacct -j <id> --format=State,ExitCode` — states like `OUT_OF_MEMORY` /
  `TIMEOUT` / `NODE_FAIL` are what tell you whether a retry could work.

Plus: `--mem` is a hard cgroup cap, not a hint; `sacct` needs `slurmdbd`
configured (fall back to `scontrol show job`, live only); a failing site
`Prolog`/`Epilog` drains the node; `srun --oversubscribe` is ignored under
consumable resources.

## When the skill triggers

- Writing or fixing an `sbatch` script or `srun` command line.
- Choosing resource requests (CPUs, memory, GPUs, time, partition).
- Reading job/queue/node state (`squeue`, `sacct`, `sinfo`, `scontrol`).
- Chaining jobs, or asking why a dependent job never started.
- Reasoning about cgroups and what fences GPU VRAM.

## When it doesn't

- Operating a specific project's cluster with its own recipes → that repo's skill.
- Designing cluster provisioning / `slurm.conf` from scratch → admin work.
- "How should the *agent* wait for this job?" → [`long-running-jobs`](long-running-jobs.md).

## Structure

```
skills/local/slurm-hpc/
├── SKILL.md                        # skeleton, resources, chaining, isolation, gotchas
└── references/
    └── gpu-isolation.md            # shard vs mps vs MIG, config snippets, enforcement details
```
