# Plan: `pueue-job-queue` agent skill

## Context

The user wants a Claude Code agent skill that lets an LLM drive
[Nukesor/pueue](https://github.com/Nukesor/pueue) for queued, parallel,
scheduled, and lightly-DAG'd shell jobs. They previously wrote
[PueueWrapper](https://github.com/daviddwlee84/PueueWrapper) — a thin Python
bridge over pueue's CLI — and want the agent to be able to do similar
things directly from a session: submit batches, cap parallelism per group,
chain `task B starts after task A succeeds`, poll for completion, retrieve
logs, and retry. Pueue's `--json` flag on `status` / `log` is the
agent-friendly surface.

Pueue 4.0.2 is already installed locally (`/opt/homebrew/bin/pueue`,
`pueued`), so the implementer can verify the empirical JSON shape directly
rather than guess from docs. The skill is a CLI bridge — *not* a custom
scheduler. `--after` is AND-only and success-only; that maps cleanly to a
declarative DAG submitter and not much beyond.

User decisions captured during planning:

- **Name:** `pueue-job-queue` (avoids the "orchestrator" overpromise).
- **Scope:** Standard + tests — 4 scripts, 4 references, 2 assets, plus a
  pytest + bash contract test suite mirroring
  `skills/local/agent-history-hygiene/tests/`.

## Skill layout

```
skills/local/pueue-job-queue/
  SKILL.md
  scripts/
    check-daemon.sh         # bash; daemon health + install hint
    submit.sh               # bash; submit one task → JSON
    wait.py                 # PEP 723 uv-script; block until terminal
    submit-dag.py           # PEP 723 uv-script; declarative DAG submit
  references/
    cli-cheatsheet.md       # un-wrapped commands the scripts deliberately don't bridge
    json-schema.md          # observed shape of `pueue status --json` (4.0.2) + jq recipes
    dag-patterns.md         # fan-out/fan-in/mixed; AND-only success-only limits
    daemon-and-config.md    # pueued setup per OS, config knobs, log paths
  assets/
    dag.example.yaml        # 5-task fan-out/fan-in fixture, doubles as smoke
    pueue.yml.example       # config with `pause_group_on_failure: true`
  tests/
    conftest.py             # isolated pueued fixture, skip if pueue absent
    test_submit.py          # submit→status→Done assertion
    test_dag.py             # submit-dag → topo invariant assertion
    test_wait.py            # success exit 0, failure exit 5, timeout exit 6
    test_contracts.sh       # bash exit-code contract for check-daemon + submit
    fixtures/
      simple-dag.yaml       # tiny graph used by test_dag.py
```

## SKILL.md frontmatter (draft)

```yaml
---
name: pueue-job-queue
description: >
  Drive Nukesor/pueue (https://github.com/Nukesor/pueue) for queued, parallel,
  scheduled, and lightly-DAG'd shell jobs — wraps `pueue add --after`, `pueue
  status --json`, `pueue log --json`, group-level parallelism, and `pueued`
  daemon health. Use when the user wants to background long-running shell
  commands across reboots, queue dozens of jobs with capped parallelism, run a
  fan-out / fan-in pipeline of shell steps, says "pueue", "pueued", "pueue
  add", "pueue queue", "pueue group", "task queue for shell", or asks how to
  schedule/parallelize CLI work without a real orchestrator
  (Airflow/Prefect/Dagster).
---
```

## SKILL.md body outline (~220 lines)

1. Mental model paragraph — pueue = persistent shell job queue, daemon-backed,
   group = parallelism unit, `--after` = success-only AND deps.
2. **When to use** — long shell jobs, capped parallelism, fan-out/fan-in shell
   pipelines, "wait then run" sequencing, scheduled (`--delay`) / stashed jobs.
3. **When NOT to use** — cross-host scheduling → real orchestrator;
   OR/conditional/retry-on-fail deps → not pueue; typed task IO/artifacts →
   DVC or Prefect.
4. **Authoritative sources** — repo, wiki, `pueue --help`, `man pueue`.
5. **Setup quickstart** — `bash scripts/check-daemon.sh --start`; macOS launchd
   hint deferred to `references/daemon-and-config.md`.
6. **Mental model table** — task / group / daemon / config.
7. **Workflow A — submit one** (`scripts/submit.sh`).
8. **Workflow B — batch with shared group + capped parallelism**
   (`pueue group add ml`, `pueue parallel 4 --group ml`, then loop `submit.sh`).
9. **Workflow C — linear DAG** (`scripts/submit-dag.py dag.yaml`).
10. **Workflow D — wait** (`scripts/wait.py --ids 1,2,3` or `--label-prefix ...`).
11. **Workflow E — logs / retry / kill** — points at
    `pueue log --json`, `pueue restart --in-place`, `pueue kill && pueue remove`.
12. **Available scripts** — bullet list (3-line summary each).
13. **Reference files** — bullet list with "read when ..." trigger.
14. **Bundled assets** — `dag.example.yaml`, `pueue.yml.example`.
15. **Gotchas** (≥8) — see "Gotchas to surface" below.

## Scripts — concrete specs

All scripts are chmod 0755, support `--help`, write **structured data to
stdout, prose to stderr**.

### `scripts/check-daemon.sh` (bash 3.2)

- **Purpose:** single-shot daemon health check + actionable hint.
- **Flags:** `--start` (auto-launch `pueued -d` if missing), `--json` (default
  on), `--help`.
- **Stdout JSON:**
  `{"daemon_running": bool, "pueue_version": "4.0.2", "client_version": "4.0.2",
    "default_group": {"parallel_tasks": N, "status": "Running"},
    "platform": "darwin", "log_dir": "/Users/.../Library/Application Support/pueue/logs"}`
- **Stderr:** prose hints (`pueued not running — try: pueued -d`).
- **Exit codes:** `0` healthy, `2` `pueue` not installed, `3` daemon
  unreachable, `4` client/daemon version mismatch.

### `scripts/submit.sh` (bash 3.2)

- **Purpose:** submit ONE task, return clean JSON. Wraps `pueue add --print-id`.
- **Flags:** `--label TXT`, `--group G`, `--after ID` (repeatable),
  `--immediate`, `--stashed`, `--delay STR`, `--priority N`, `--working-dir
  PATH`, `--escape`, `--dry-run`, `--help`. After `--`, the command.
- **Stdout JSON:**
  `{"task_id": 17, "label": "...", "group": "ml", "after": [12,14],
    "immediate": false, "stashed": false}`
- **Stderr:** `submitted task 17 (group=ml, after=[12,14])`.
- **Exit codes:** `0` ok, `1` bad args, `2` pueue not installed, `3` `pueue
  add` failed, `4` daemon unreachable.
- **Defensive parse:** capture trailing integer with `grep -oE '[0-9]+$'` from
  `pueue add --print-id` output; fall back to `pueue status --json | jq` lookup
  by label if regex misses.
- **Group autocreate:** if `--group X` and `pueue group | grep -q X` fails,
  call `pueue group add X` first (idempotent — verify in step 0).

### `scripts/wait.py` (PEP 723 uv-script, stdlib only)

- **Purpose:** block until a set of tasks reaches terminal status. Polls
  `pueue status --json`.
- **Selectors (one required):** `--ids 1,2,3`, `--label LABEL` (exact,
  repeatable), `--label-prefix STR`, `--group G`.
- **Flags:** `--poll-seconds 2.0`, `--timeout-seconds 0` (0 = no timeout),
  `--fail-fast`, `--quiet`, `--help`.
- **Stdout (terminal):**
  ```json
  {"summary": {"total": 4, "success": 3, "failed": 1, "killed": 0, "dependency_failed": 0},
   "tasks": [{"id": 17, "label": "...", "status": "Done", "exit_code": 0,
              "start": "...", "end": "...", "group": "ml"}],
   "elapsed_seconds": 42.3}
  ```
- **Stderr:** one line per poll tick (`tick 12: 2 running, 1 queued, 1 done`).
- **Exit codes:** `0` all `Done`+`exit_code==0`; `1` arg error; `5` ≥1
  failed/killed/dependency_failed; `6` timeout; `4` daemon unreachable.

### `scripts/submit-dag.py` (PEP 723 uv-script, deps: `pyyaml>=6`)

- **Purpose:** submit a linear DAG (success-only deps). Topo-sorts, submits in
  order, wires `--after` from name→id map.
- **Spec source:** positional path arg, OR `-` for stdin (heredoc-friendly).
  Format auto-detected (`{`/`[` → JSON; else YAML).
- **Flags:** `--format yaml|json|auto` (default `auto`), `--default-group G`,
  `--label-prefix STR` (prepended to each task's `name`), `--dry-run`,
  `--print-graph`, `--help`.
- **Spec schema (YAML):**
  ```yaml
  version: 1
  default_group: ml
  tasks:
    fetch:        { cmd: ./fetch.sh, group: io }
    featurize:    { cmd: python feat.py, after: [fetch] }
    train_a:      { cmd: python train.py --seed 1, after: [featurize] }
    train_b:      { cmd: python train.py --seed 2, after: [featurize] }
    evaluate:     { cmd: python eval.py, after: [train_a, train_b] }
  ```
- **Validation (pre-submit):** unknown `after:` name, cycle, empty `tasks:`,
  missing `cmd:` → fail with exit `1` and the offending key. **No partial
  submits** — pre-validate fully before any `pueue add`.
- **Stdout:**
  `{"tasks": {"fetch": 17, ...}, "topo_order": [...], "default_group": "ml"}`
- **Stderr:** per-task submit prose (`fetch -> 17`, `featurize -> 18 (after=[17])`).
- **Exit codes:** `0` all submitted; `1` schema/cycle/unknown ref;
  `2` pueue not installed; `3` mid-run pueue failure (stdout still emits the
  IDs that DID submit, so the agent can clean up).

**Why 4 scripts, not more:** retry / kill / log-tail are one-line `pueue`
calls — documenting them in `references/cli-cheatsheet.md` beats wrapping. A
wrapper earns its keep only when it (a) reshapes output to JSON, (b) hides
multi-step orchestration (DAG submit), or (c) blocks (wait).

## Reference docs

- **`cli-cheatsheet.md`** — un-wrapped commands the scripts deliberately don't
  bridge: `pueue follow`, `pueue log [--json]`, `pueue restart [--in-place
  --start-immediately]`, `pueue kill`, `pueue remove`, `pueue clean
  [--successful-only]`, `pueue group add/remove`, `pueue parallel N --group G`,
  `pueue pause/start [--group G]`, `pueue reset`, `pueue edit`, `pueue env`.
  One-line description + when to use.
- **`json-schema.md`** — **observed** shape of `pueue status --json` and
  `pueue log --json` on pueue 4.0.2. Begins with: *"Run this once on your
  version (`pueue --version`) and diff:"* followed by `pueue status --json |
  jq 'keys, .tasks | (keys | first as $k | .[$k])'`. Ships useful jq
  one-liners: get all running ids, failed tasks with stderr path, group→
  pending count, dependents of task X.
- **`dag-patterns.md`** — fan-out / fan-in / mixed examples (matching
  `dag.example.yaml`); explicit limitations: AND-only, success-only, no OR, no
  conditional, no retry-on-fail; "when to fall back": >1 host, OR/conditional
  deps, typed artifacts, retry-with-backoff → use Prefect/Dagster/Airflow;
  mention DVC's `dvc exp run --queue` for ML-sweep workloads.
- **`daemon-and-config.md`** — `pueued -d` per OS, log/config paths
  (Linux/macOS/Windows), key config knobs (`pause_group_on_failure: true`,
  `default_parallel_tasks`, `groups:` block), how to launch `pueued` under
  launchd / systemd-user; warn "do NOT run `pueued` from inside `pueue add` —
  races".

## Bundled assets

- **`assets/dag.example.yaml`** — 5-task fan-out/fan-in
  (`fetch → featurize → {train_a, train_b} → evaluate`). Doubles as the smoke
  fixture and the `tests/fixtures/simple-dag.yaml` source.
- **`assets/pueue.yml.example`** — config snippet with comments:
  `pause_group_on_failure: true`, `default_parallel_tasks: 1`, sample groups
  block (`groups: { ml: 4, io: 2 }`). Header comment names the
  platform-specific destinations.

## Gotchas to surface in SKILL.md (≥8)

1. `--after` is AND-only and success-only — failed parent → `DependencyFailed`,
   never runs.
2. Daemon must be running; `pueued -d` is opaque-failure if it's already up.
3. Default group always exists; new groups need `pueue parallel N --group X`
   or workers stay at 1 (or 0 — verify in step 0).
4. `pause_group_on_failure` is config-only, no CLI flag.
5. `pueue restart` (default) creates a NEW task id; `--in-place` keeps the
   slot. Choose deliberately.
6. Logs live in platform-specific dirs (Linux `~/.local/share/pueue/logs/`,
   macOS `~/Library/Application Support/pueue/logs/`, Windows
   `%APPDATA%\pueue\logs\`). `tail -f` won't find them in CWD.
7. `pueue clean` permanently removes done tasks; `--successful-only` is a
   flag, not the default.
8. `pueue add --print-id` output format is unverified across versions —
   `submit.sh` parses defensively (regex grep for digits).
9. `pueue status --json` may return tagged enums (e.g. `{"status": {"Done":
   {"exit_code": 0, "result": "Success"}}}`) — `wait.py` handles both flat
   and nested shapes.

## Critical files to be created

- `/Volumes/Data/Program/Personal/agent-skills/skills/local/pueue-job-queue/SKILL.md`
- `/Volumes/Data/Program/Personal/agent-skills/skills/local/pueue-job-queue/scripts/check-daemon.sh`
- `/Volumes/Data/Program/Personal/agent-skills/skills/local/pueue-job-queue/scripts/submit.sh`
- `/Volumes/Data/Program/Personal/agent-skills/skills/local/pueue-job-queue/scripts/wait.py`
- `/Volumes/Data/Program/Personal/agent-skills/skills/local/pueue-job-queue/scripts/submit-dag.py`
- `/Volumes/Data/Program/Personal/agent-skills/skills/local/pueue-job-queue/references/{cli-cheatsheet,json-schema,dag-patterns,daemon-and-config}.md`
- `/Volumes/Data/Program/Personal/agent-skills/skills/local/pueue-job-queue/assets/{dag.example.yaml,pueue.yml.example}`
- `/Volumes/Data/Program/Personal/agent-skills/skills/local/pueue-job-queue/tests/{conftest.py,test_submit.py,test_dag.py,test_wait.py,test_contracts.sh,fixtures/simple-dag.yaml}`

## Existing patterns to reuse

- **Skill scaffold:** `bash skills/local/skill-author/scripts/new-skill.sh
  pueue-job-queue` produces the directory layout from
  `skills/local/skill-author/assets/SKILL.md.template`.
- **Bash script template:** `skills/local/skill-author/assets/script-bash.template`
  (already enforces `set -euo pipefail`, `--help`/`--dry-run`, stdout-data /
  stderr-prose split, bash 3.2 compat).
- **PEP 723 Python pattern:** mirror
  `skills/local/mlflow-tracking/scripts/tail-runs.sh` (despite the `.sh`
  extension it's actually a `#!/usr/bin/env -S uv run --script` Python file
  with inline `# /// script` deps).
- **Subcommand JSON-output style:** mirror
  `skills/local/dvc-ml-workflow/scripts/queue-helper.sh` (one JSON object per
  task on stdout, designed for LLM callers).
- **Test layout:** mirror `skills/local/agent-history-hygiene/tests/`
  (conftest.py + pytest + bash contract test + fixtures/ subdir).
- **Linter:** `bash skills/local/skill-author/scripts/lint-skill.sh
  skills/local/pueue-job-queue` — must pass before merge.

## Step 0 — verification checklist (run BEFORE finalizing scripts)

Pueue 4.0.2 is installed locally. Run all of these, paste real output into a
scratch file, code against what you actually see:

1. **`--print-id` format** — `pueued -d; pueue add --print-id -- echo hi`.
   Plain int? JSON? Prose? Decides `submit.sh` parse strategy.
2. **`status --json` keys for deps** — `pueue add -- sleep 5 && pueue add
   --after 1 -- echo hi && pueue status --json | jq '.tasks | to_entries[1].value
   | keys'`. Confirm: `dependencies` vs `dependency_ids` vs nested under
   `original_command`.
3. **Failed-dep status string** — kill task 1, check task 2's `.status`. Is it
   the string `"DependencyFailed"`, the object `{"DependencyFailed": ...}`, or
   nested under `Failed`? `wait.py`'s exit-code logic depends on this.
4. **`exit_code` location** — top-level on the task, or nested under `result` /
   `status`? Pueue uses serde tagged enums — likely `{"status": {"Done":
   {"exit_code": 0, "result": "Success"}}}`. Confirm.
5. **macOS `pueued -d` daemonization** — does it fork cleanly off the
   terminal? If not, `check-daemon.sh --start` needs `nohup pueued -d
   </dev/null >/dev/null 2>&1 &`.
6. **Group autocreate** — does `pueue add --group new_name` auto-create the
   group, or fail? If fail, `submit.sh` must `pueue group add X` first.
7. **Label dedup** — does pueue dedupe by label or allow duplicates? Affects
   whether `wait.py --label X` can match >1 task.

Pin the observed behavior in `references/json-schema.md` along with the
`pueue --version` it was captured against.

## End-to-end verification

### Lint

```bash
bash skills/local/skill-author/scripts/lint-skill.sh skills/local/pueue-job-queue
```

Must pass before commit. `--strict` to catch warnings too.

### Manual smoke (≈10 min, after step 0)

```bash
pueued -d  # if not running
bash skills/local/pueue-job-queue/scripts/check-daemon.sh --json | jq

ID1=$(bash skills/local/pueue-job-queue/scripts/submit.sh \
        --label hello -- echo hello | jq -r .task_id)
bash skills/local/pueue-job-queue/scripts/submit.sh \
        --label after1 --after $ID1 -- echo done

skills/local/pueue-job-queue/scripts/submit-dag.py \
        skills/local/pueue-job-queue/assets/dag.example.yaml \
        --label-prefix smoke- --default-group default --print-graph

skills/local/pueue-job-queue/scripts/wait.py \
        --label-prefix smoke- --timeout-seconds 60
```

Each command should emit valid JSON to stdout and a one-line prose summary to
stderr.

### Automated tests (`tests/`)

- `conftest.py` — pytest fixture `pueue_daemon` that runs
  `subprocess.Popen(['pueued', '--config', tmpdir+'/pueue.yml'])` against an
  isolated config + log dir, yields, then `pueue shutdown`. Skip the whole
  module if `pueue` not on `PATH`.
- `test_submit.py` — submits `sleep 0`, asserts `submit.sh` JSON has integer
  `task_id`, polls `pueue status --json` until `Done`.
- `test_dag.py` — feeds `tests/fixtures/simple-dag.yaml` to `submit-dag.py`,
  parses name→id map, polls until all done, asserts topo invariant (later
  task's start_time ≥ all-deps end_time).
- `test_wait.py` — submits `sleep 0.5`, calls `wait.py --ids N
  --timeout-seconds 5`, asserts exit 0 + JSON shape; submits `false`, asserts
  exit 5; sleeps forever case asserts exit 6 with `--timeout-seconds 1`.
- `test_contracts.sh` — bash exit-code contract for `check-daemon.sh` (0 / 2 /
  3) and `submit.sh` (0 / 1 / 4 with daemon down).

Wire into the existing `make test-skill` target if present (re-check during
implementation — `agent-history-hygiene/tests/README.md` mentions one).

### Optional follow-up

After lint passes and manual smoke is clean, consider handing off to
`skill-creator` for quantitative trigger / output evaluation against real
prompts (per `skill-author`'s workflow §6).
