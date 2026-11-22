# colab-remote-runner

Use **Google Colab as a disposable remote compute box** for batch jobs, driven
entirely from the terminal with the official
[Colab CLI](https://github.com/googlecolab/google-colab-cli) (`colab`).
Create a session, ship code as wheels, pull data from Google Drive, run a
command on a GPU or high-RAM VM, download the outputs, stop the session.

Extracted from a working research setup (quant model training offloaded to
Colab T4 / high-RAM sessions) and stripped of project specifics.

| Surface | Question it answers |
|---|---|
| `SKILL.md` | "What's the default flow, and which traps will bite me?" |
| [`scripts/colab_job.py`](https://github.com/daviddwlee84/agent-skills/blob/main/skills/local/colab-remote-runner/scripts/colab_job.py) | "Run it end to end" — `exec` / `upload` / `run`, `--dry-run`, JSON stdout |
| [`assets/remote_steps.py`](https://github.com/daviddwlee84/agent-skills/blob/main/skills/local/colab-remote-runner/assets/remote_steps.py) | VM-side `install` / `data` / `run` steps |
| [`references/gotchas.md`](https://github.com/daviddwlee84/agent-skills/blob/main/skills/local/colab-remote-runner/references/gotchas.md) | Symptom-titled errors (`400 Bad Request`, `mount failed`, `Timeout waiting for reply`, `RefreshError`) |
| [`references/drive-data.md`](https://github.com/daviddwlee84/agent-skills/blob/main/skills/local/colab-remote-runner/references/drive-data.md) | Dataset on Drive, sha256 manifest, Drive API fetch |
| [`references/smoke-test.md`](https://github.com/daviddwlee84/agent-skills/blob/main/skills/local/colab-remote-runner/references/smoke-test.md) | Public Datasette table → LightGBM (CPU) and Keras (T4) on Colab, with measured time and cost |
| [`references/adapting-to-a-project.md`](https://github.com/daviddwlee84/agent-skills/blob/main/skills/local/colab-remote-runner/references/adapting-to-a-project.md) | The thin project wrapper pattern |

## Quick start

```bash
uv tool install google-colab-cli
colab new -s work --gpu T4 --high-mem
colab auth -s work                     # interactive once per session; enables Drive

colab_job.py --dry-run run -s work --wheel . --data-spec data.json \
    --cmd "my-train --out /content/job/out" --out runs/colab
colab_job.py run -s work --wheel . --data-spec data.json \
    --cmd "my-train --out /content/job/out" --out runs/colab

colab stop -s work                     # idle sessions keep billing
```

Every `run` prints one JSON object with a **cost/time block** — `timing_s` per
phase (session, upload, install, data, run, download, stop), `cost` with
`colab usage` snapshots and `units_estimated` (rate × wall time), and `vm`
(Python, CPUs, RAM, GPU) — and also writes it into the result dir's
`_colab_meta.json`, even when a step fails. The smoke test took ~65 s end to
end: ≈0.001 compute units on a CPU VM, ≈0.02 on a T4.

## The lessons that shaped it

- **Data is the bottleneck, not the GPU.** Local → VM upload runs at ~2 MB/s and
  each request is capped (~60–94 MB). A 5–6 GB dataset spent most of a 22-minute
  run uploading. Put datasets on Drive once; the VM pulls them over Google's network.
- **`colab exec` doesn't tell you the truth.** It can exit 0 after a remote
  exception, and its 30 s *silence* timeout fires during quiet steps. Every remote
  step prints a success marker; the client uses a long timeout and trusts the marker.
- **`colab drivemount` fails headless.** `colab auth` + the Drive API works, but
  auth needs a human once per session — so keep one session per working block.
- **CLI 0.8 moved the token into the OS keyring.** Over SSH a locked keyring
  stalls every call ~60 s; `colab_job.py --no-keyring` or `colab --auth=adc` avoids it.
- **Log results locally.** Download the output dir and run your tracker (e.g.
  MLflow) on your machine with a `compute=colab` tag; no tracker credentials on the VM.

## When not to use it

Interactive notebook work (use the Colab UI), queued/scheduled multi-job
pipelines ([`slurm-hpc`](slurm-hpc.md), [`pueue-job-queue`](pueue-job-queue.md)),
or data that must not be stored in Google Drive.
