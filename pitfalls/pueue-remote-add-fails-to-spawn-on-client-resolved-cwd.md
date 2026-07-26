# Remote `pueue add` lands as `FailedToSpawn` — and `wait.py` called it success

## Symptom

Driving a remote `pueued` from a local `pueue` client (SSH-forwarded socket),
every submitted task finishes instantly and never produces output:

```console
$ pueue -c remote.yml add --print-task-id -- 'echo hello; hostname'
33
$ pueue -c remote.yml status --json | jq '.tasks["33"].status'
{
  "Done": {
    "start": "2026-07-26T20:37:58.384549016+08:00",
    "end":   "2026-07-26T20:37:58.384549126+08:00",
    "result": {
      "FailedToSpawn": "Failed to spawn child 33 with err: Os { code: 2, kind: NotFound, message: \"No such file or directory\" }"
    }
  }
}
```

`start == end` to the microsecond — it never ran.

Two related symptoms:

```console
$ pueue -c remote.yml add --working-directory /home/remoteuser -- 'echo OK'
Error:
   0: Failed to canonicalize given working directory path
   1: No such file or directory (os error 2)
```

```console
# from macOS — silently rewritten, then fails on the Linux daemon
$ pueue -c remote.yml add --working-directory /tmp -- 'echo OK'
$ pueue -c remote.yml status --json | jq -r '.tasks["34"].path'
/private/tmp
```

And the one that actually costs you: **`wait.py` reported exit `0`** for task
33. An agent waiting on a job that never started was told everything was fine.

## Root cause

**Pueue records a task's working directory at submit time, and the *client*
canonicalizes it against its own filesystem.** The daemon then spawns the child
in that literal path.

So when client and daemon are different machines:

| Case | Result |
|---|---|
| Default (client's cwd, e.g. `/Users/you/proj`) | Path absent on the daemon host → `FailedToSpawn` |
| `--working-directory` with a remote-only path | Client can't canonicalize it → **refuses to submit** |
| `--working-directory /tmp` on macOS | Resolved to `/private/tmp` → absent on Linux → `FailedToSpawn` |
| A path identical on both (`/usr`) | ✅ works |

The silent-success half is a separate bug. `FailedToSpawn` is **dict-shaped** —
`{"FailedToSpawn": "<os error>"}` — while `wait.py` matched results against an
enumerated *bad* list (`{"DependencyFailed", "Killed"}` plus `{"Failed": <int>}`).
`FailedToSpawn` was in neither, so it fell through to "not bad" and the script
returned `0`.

Enumerating failures in a tagged enum means **every variant you didn't think of
reads as success.**

## Workaround

To *submit* to a remote daemon, don't use a remote client — SSH over, so the
cwd is resolved on the machine that will run the job:

```bash
ssh myhost 'cd ~/project && pueue add --label train-seed1 -- ./train.sh'
```

A forwarded client remains the right tool for everything else — `status --json`
piped into local `jq`, `log`, `follow`, `kill`, `pause`, `restart`.

If you must submit from the remote client, the working directory has to exist
**and canonicalize identically on both machines**:

```bash
pueue -c remote.yml add --working-directory /usr -- 'hostname'   # verified working
```

## Prevention

**Never enumerate the failure variants of a tagged enum.** Allowlist the one
good value and fail closed:

```python
TERMINAL_RESULTS_GOOD = {"Success"}

def is_failure(summary):
    return summary["state"] == "Done" and summary["result"] not in TERMINAL_RESULTS_GOOD
```

`wait.py` now does this, so a future pueue release adding a new result variant
degrades to "reported as failure" (noisy, safe) instead of "reported as
success" (silent, wrong). Verified against the real payload above — it now
exits `5` — and against a synthetic unknown variant.

**Invariant:** for any external tool whose status is a tagged union, the
success set is the allowlist. Anything unrecognized is a failure.

## See also

- `skills/local/pueue-job-queue/references/remote-daemon.md` — full remote
  setup, SSH forwarding recipe, and when to just SSH over.
- `skills/local/pueue-job-queue/references/json-schema.md` — the `result`
  variant table.
