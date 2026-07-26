# pueue-job-queue

Drive [Nukesor/pueue](https://github.com/Nukesor/pueue) — a daemon-backed
shell job queue — for queued, parallel, scheduled, and lightly-DAG'd shell
work. The skill is a **CLI bridge**, not a custom scheduler: it wraps
`pueue add --after`, `pueue status --json`, and `pueue log --json` so an
agent can submit, batch, chain, wait, and retry without losing track of
what's running.

| Surface | Question it answers |
|---|---|
| `check-daemon.sh` | "Is `pueued` running, and where do logs live on this OS?" |
| `submit.sh` | "Submit one task and give me a parseable `{task_id, label, group, after}`." |
| `submit-dag.py` | "Submit this whole fan-out / fan-in pipeline with deps wired — in a fresh isolated group sized to the DAG width." |
| `wait.py` | "Block until these tasks finish, then summarize success/failure." |
| `cleanup.sh` | "Reclaim disk + status latency: prune old tasks, empty groups, log files." |
| [`references/cli-cheatsheet.md`](https://github.com/daviddwlee84/agent-skills/blob/main/skills/local/pueue-job-queue/references/cli-cheatsheet.md) | "What un-wrapped `pueue` subcommand do I reach for?" |
| [`references/json-schema.md`](https://github.com/daviddwlee84/agent-skills/blob/main/skills/local/pueue-job-queue/references/json-schema.md) | "What does `pueue status --json` actually look like? What's the QUERY DSL syntax?" |
| [`references/dag-patterns.md`](https://github.com/daviddwlee84/agent-skills/blob/main/skills/local/pueue-job-queue/references/dag-patterns.md) | "How do I express fan-out / fan-in / diamond shapes?" |
| [`references/daemon-and-config.md`](https://github.com/daviddwlee84/agent-skills/blob/main/skills/local/pueue-job-queue/references/daemon-and-config.md) | "How do I auto-start `pueued` on macOS / Linux?" |
| [`references/remote-daemon.md`](https://github.com/daviddwlee84/agent-skills/blob/main/skills/local/pueue-job-queue/references/remote-daemon.md) | "The daemon is on another machine — can I drive it, and should I?" |

The skill exists to keep three things out of an agent's way:

1. **Bookkeeping** — task ids, dependency wiring, group autocreate, defensive
   id parsing of `pueue add --print-task-id`.
2. **Schema drift** — `pueue status --json` uses serde tagged enums
   (`{"Done": {"result": "Success" | "DependencyFailed" | "Killed" | {"Failed": <int>}}}`).
   `wait.py` classifies all variants and returns predictable exit codes
   (`0` ok, `5` any failure, `6` timeout).
3. **Footguns** — `pueue add -- bash -c 'sleep 60'` does NOT preserve the
   inner quote (pueue re-shells); `pueue kill --all` also pauses every
   group; `pueue restart` (default) creates a NEW id; `pueue clean`
   (default) wipes failures too. The SKILL.md has a 10-item gotcha list
   covering each of these.

## When the skill triggers

- "Run these 30 commands, max 4 at a time" → set group parallelism, loop
  `submit.sh --group sweep`.
- "Kick off a long training job and let me close my laptop" → `submit.sh
  -- ./train.sh` (pueue persists across reboots).
- "Run task B only after task A succeeds" → `submit.sh --after $A_ID -- ./b.sh`.
- "Fan out 4 trainings, then evaluate" → `submit-dag.py dag.yaml`.
- "Schedule this for tonight" → `submit.sh --delay 6h -- ./nightly.sh`.
- The user says **pueue / pueued / pueue add / pueue queue / pueue group**
  or asks about a "task queue for shell jobs".

## When it doesn't

- One short shell command — just run it. Pueue adds daemon overhead.
- Cross-host scheduling, OR-deps, conditional branching, retry-with-backoff,
  typed task IO — escalate to **Airflow / Prefect / Dagster / DVC / Slurm**.
  [`references/dag-patterns.md`](https://github.com/daviddwlee84/agent-skills/blob/main/skills/local/pueue-job-queue/references/dag-patterns.md) has a decision table.
- Long-running services — that's `systemd` / `launchd`.

## Structure

```
skills/local/pueue-job-queue/
├── SKILL.md                                  # ~275 lines
├── scripts/
│   ├── check-daemon.sh                       # bash; daemon health + auto-start
│   ├── submit.sh                             # bash; submit-one wrapper, JSON out, group autocreate
│   ├── wait.py                               # PEP 723; block until terminal, state-change events, JSON summary
│   ├── submit-dag.py                         # PEP 723 (pyyaml); DAG submitter with --isolated-group / --auto-parallel
│   └── cleanup.sh                            # bash; prune tasks + empty groups + old log files
├── references/
│   ├── cli-cheatsheet.md                     # un-wrapped commands
│   ├── json-schema.md                        # observed status --json shape (4.0.2) + QUERY DSL + jq recipes
│   ├── dag-patterns.md                       # fan-out / fan-in / diamond + escalation table
│   ├── daemon-and-config.md                  # pueued setup per OS, config knobs, log paths
│   └── remote-daemon.md                      # SSH socket forwarding, TCP+TLS, the client-resolved-cwd trap
├── assets/
│   ├── dag.example.yaml                      # 5-task fan-out / fan-in fixture
│   └── pueue.yml.example                     # config with `pause_group_on_failure: true`
└── tests/
    ├── conftest.py                           # isolated pueued fixture, skip if pueue absent
    ├── test_submit.py                        # submit.sh paths + dependency failure
    ├── test_dag.py                           # topo invariant, cycle/unknown/missing-cmd, isolated-group
    ├── test_wait.py                          # success/failure/timeout exit codes
    ├── test_contracts.sh                     # bash --help/error-code contract
    └── fixtures/simple-dag.yaml              # 4-task diamond
```

## Always pass a label

`pueue status` shows the **label** column before the command. In a busy
queue, scanning labels is the only way to tell `train.py` runs apart at a
glance. The skill's gotchas section opens with:

> Always pass `--label` when submitting, and bias toward names that
> distinguish *this* task from its siblings.

Convention: `<verb>-<subject>-<key>` (≤30 chars). Encode the discriminator
(seed, dataset slice, model variant) — not the command:

| Good | Bad |
|---|---|
| `train-baseline-seed1` | `task1` |
| `eval-prod-2026q1` | `python eval.py --quarter 2026q1` |
| `nightly-featurize` (DAG) | `step-2-of-5` |

`submit-dag.py --label-prefix <run>-` produces `<run>-<task_name>` so
`wait.py --label-prefix <run>-` selects the whole graph and `pueue clean`
can be filtered later.

## Empirical schema

Pueue's JSON output isn't formally documented in the wiki. The skill ships
the observed shape on **pueue 4.0.2** in [`references/json-schema.md`](https://github.com/daviddwlee84/agent-skills/blob/main/skills/local/pueue-job-queue/references/json-schema.md),
including the diagnostic snippet to re-verify on a different major. Key
shape:

```json
{
  "tasks": {
    "<id>": {
      "id": 17,
      "label": "train-baseline-seed1",
      "group": "ml",
      "dependencies": [12, 14],
      "status": {
        "Done": {
          "enqueued_at": "...", "start": "...", "end": "...",
          "result": "Success"            // or "DependencyFailed" | "Killed" | {"Failed": 1}
        }
      }
    }
  },
  "groups": {
    "default": {"status": "Running", "parallel_tasks": 1}
  }
}
```

`wait.py` classifies every variant; if a future pueue release adds one
(say `Suspended`), the test suite catches it before the skill goes silent.

## Verification

The skill ships **22 pytest cases** that spin up an isolated `pueued`
under a tempdir-scoped config — your real queue is never touched — plus a
bash exit-code contract test. Both auto-skip if `pueue` / `pueued` aren't
on `PATH`. `lint-skill --strict` is clean (0 errors, 0 warnings).

```bash
uv run --extra dev pytest skills/local/pueue-job-queue/tests/ -q
bash skills/local/pueue-job-queue/tests/test_contracts.sh
bash skills/local/skill-author/scripts/lint-skill.sh skills/local/pueue-job-queue --strict
```

The pytest fixture uses `pueue reset --force` between tests because plain
`pueue kill --all` also pauses every group — a non-obvious failure mode
worth documenting (see SKILL.md gotchas).

## Remote daemons: yes, but submit over SSH

Pueue can't schedule *across* hosts, but a local client **can** drive a single
remote `pueued` — with full control (`add`, `kill`, `log`, `follow`), not just
status. [`references/remote-daemon.md`](https://github.com/daviddwlee84/agent-skills/blob/main/skills/local/pueue-job-queue/references/remote-daemon.md) covers the setup; the short version is
that the recommended path changes nothing on the server:

```bash
# forward the daemon's own unix socket — no server reconfiguration, no TLS
ssh -f -N -L ~/.config/pueue/remote/remote.sock:/run/user/1000/pueue_you.socket myhost
pueue -c ~/.config/pueue/remote/client.yml status
```

Verified end to end with a macOS client (4.0.4) against a Linux daemon (4.0.2).
Findings worth knowing before you try it:

- **`read_local_logs: false` is mandatory** on the client, or `log` / `follow`
  look for the daemon's logs on your own disk and find nothing.
- **A version mismatch warns but works** — `Different protocol version detected
  '0.30.1'` on every command, then normal behaviour. Filter it from stderr;
  stdout JSON stays clean.
- **Submitting is the part that doesn't travel.** `pueue add` records the
  working directory and canonicalizes it *on the client*, so a remote submit
  fails three ways: the local cwd gets sent and the task ends `FailedToSpawn`;
  a remote-only path is rejected outright (`Failed to canonicalize given
  working directory path`); and on macOS `/tmp` is silently rewritten to
  `/private/tmp`. Only a path that exists and resolves identically on both
  machines works.

So the honest split is **`ssh host 'pueue add ...'` to submit, forwarded client
to read and control.**

That investigation also surfaced a real bug in this skill, now fixed: pueue's
`result` is a tagged enum and `FailedToSpawn` is dict-shaped
(`{"FailedToSpawn": "<os error>"}`), but `wait.py` matched against an
enumerated list of *bad* variants — so it fell through and **`wait.py` returned
exit 0 for a task that never started**. It now allowlists `Success` and fails
closed on anything else, which also makes it safe against future pueue
variants. See
[the pitfall](https://github.com/daviddwlee84/agent-skills/blob/main/pitfalls/pueue-remote-add-fails-to-spawn-on-client-resolved-cwd.md).
