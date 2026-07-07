# GPU VRAM isolation — shard vs MPS vs MIG

Read this when the task is capping or partitioning GPU memory so a job that
over-allocates fails on its own instead of taking down its neighbours.

## The isolation question

"If job B sets its batch size too large and blows past its VRAM budget, does it
fail alone, or does it starve/crash job A on the same card?"

| Method | VRAM isolation | B fails alone? | Enforced by |
|---|---|---|---|
| `gres/shard` | none (accounting) | ❌ | scheduler only |
| plain `gres/mps` | none | ❌ | — |
| `gres/mps` + pinned mem limit | soft-but-enforced | ✅ | MPS server/driver |
| MIG | hard hardware slice | ✅ | GPU silicon |
| framework caps (PyTorch/TF) | none (in-process) | ⚠️ only if job cooperates | framework allocator |

## gres/shard — packing, not fencing

```ini
# slurm.conf
GresTypes=gpu,shard
NodeName=... Gres=gpu:2,shard:64
# gres.conf
Name=shard Count=32          # split across the node's GPUs
```

Request `--gres=shard:N`. Slurm sets `CUDA_VISIBLE_DEVICES` to the shared card.
Docs: sharding *"does not fence the processes running on the GPU, it only
allows the GPU to be shared."* Use for trusted, correctly-sized jobs only.

## gres/mps + pinned memory limit — enforceable cap without MIG

```ini
# slurm.conf
NodeName=... Gres=gpu:2,mps:200
# gres.conf
Name=mps Count=1300 File=/dev/nvidia0
```

`--gres=mps:N` → Slurm sets `CUDA_MPS_ACTIVE_THREAD_PERCENTAGE` (= requested ×
100 / configured count). That splits **compute only** — Slurm does NOT set the
VRAM limit. The cap is a separate NVIDIA control (Volta+, CUDA 11.5+):

```sh
export CUDA_MPS_PINNED_DEVICE_MEM_LIMIT="0=8G"   # hard ceiling for this client
# or on the daemon: echo "set_default_device_pinned_mem_limit 0 8G" | nvidia-cuda-mps-control
```

Wire it via a Prolog that derives the cap from the mps % and injects the env
var (a TaskProlog). Requires the MPS control daemon running; only one user's
MPS server per node at a time. With the limit set, a client is denied past its
cap → that job OOMs alone.

## MIG — hardware slices (datacenter GPUs only)

A100/A30/H100-class only. Admin pre-partitions with `nvidia-smi mig`; Slurm
auto-detects via `AutoDetect=nvml` and treats each slice as a GPU. Request the
profile as the type: `--gres=gpu:1g.5gb:1`. Each job physically cannot exceed
its slice's memory — strongest isolation, rigid fixed profiles.

## Framework caps — defense-in-depth only

`torch.cuda.set_per_process_memory_fraction(f)` / TF `set_memory_growth` cap
only the framework's own allocator inside one process. They help only if every
job cooperates; never a substitute for MPS-limit or MIG. They also bake a
machine-specific number into the training script — prefer enforcing at the
scheduler layer (mps/MIG) so scripts stay portable.

## Sources

- Slurm GRES: https://slurm.schedmd.com/gres.html
- NVIDIA MPS: https://docs.nvidia.com/deploy/mps/index.html
- NVIDIA MIG: https://docs.nvidia.com/datacenter/tesla/mig-user-guide/index.html
