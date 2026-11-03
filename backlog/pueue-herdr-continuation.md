# Pueue completion → Herdr / Herdr Core continuation

Evaluated **2026-11-03**. [Discussion #43](https://github.com/daviddwlee84/agent-skills/discussions/43),
[implementation #44](https://github.com/daviddwlee84/agent-skills/issues/44).

## Decision

**Adopt a small optional recipe in `pueue-job-queue`; do not build a general
adapter.** Existing Herdr can wake a verified idle Codex conversation after jobs
finish, or start a fresh conversation with the results. Both were demonstrated
with real model responses. Core offers suitable lower-level primitives for a
new headless workflow, but this evaluation verified its **synthetic PTY
transport**, not real-agent Core continuation.

Keep three separate facts: **jobs finished**, **input submitted**, **recipient
processed it**. The persistent result file is the source of truth; terminal
input is a best-effort continuation route, not a durable/exactly-once inbox.

The shipped recipe is
[`references/agent-continuation.md`](../skills/local/pueue-job-queue/references/agent-continuation.md).
Its completion-gate Python block is executed directly by regression tests so the
published example and tested implementation cannot drift independently.

## Evidence levels and versions

| Component | Version / evidence |
|---|---|
| Pueue / pueued | 4.0.2; isolated daemons, not the user's live queue |
| Herdr | Client and server 0.9.5, protocol 22 |
| Codex | 0.166.0, interactive `--sandbox read-only --no-alt-screen --no-daemon` |
| Core source | `b63ecbd1e6b6a7d63fb7bcf40f268930417723ba` |
| Core binary | Official macOS arm64 `hc 0.1.17`; not globally installed |
| Model budget | Three tiny Codex turns total; no tools/project modifications requested |

Core archive: `https://releases.herdr.dev/core/0.1.17/herdr-core-macos-aarch64.tar.gz`

Manifest-checked SHA-256:
`cedbd4d4d9ba1385588198dd4d3c67d2654478f33add5b6445d4d0eb9da5fcf3`.
The binary's SHA-256 was
`b0ad77ab78ca8d9a8b7fb2ddd02c6f23fcbd1fa6cd2dafd39574adb71e96fc4a`.
The source revision and release version are separate evidence, not a claim that
the release embeds that exact commit.

## What actually ran

### 1. Queue completion and failure behavior — runtime verified

The new automated tests use the existing `pueue_env` fixture and disposable
config/socket/state. They verify:

- all-success dependencies: d's start is at or after every parent's end;
- failure suppression: one failed parent makes a dependent notification job
  `DependencyFailed` and its command never writes the marker;
- all-settled: a separate control-group d waits for all a/b/c IDs, including a
  failed a and slower b/c, with only **one worker slot**;
- a complete result is persisted before the receiver stub ACK;
- a receiver exiting 42 leaves results intact and records only one attempt;
- missing IDs, malformed JSON, duplicate/wrong IDs, incomplete task states,
  non-success observer exit codes and a paused-group timeout do not publish a
  completion artifact.

The all-settled fixture disables automatic pause-on-failure. A manually paused
queue was tested separately; automatic `pause_group_on_failure=true` was not
fault-injected. The documented timeout precaution follows from the observed
paused-queue behavior and the config contract.

The first test run had two fixture mistakes: `reset --force` retains named
groups, and Pueue's Queued variant can contain `enqueued_at`. Unique group names
and enum-aware assertions fixed those. No production queue code changed.

### 2. Pueue → existing real Codex — runtime verified

A no-focus test pane started Codex and received one initial prompt:

```text
Do not call tools, inspect files, or change anything.
Reply exactly READY:pq44 and finish this turn.
```

The actual assistant response was `READY:pq44`. The driver captured that
conversation's native session identity and Herdr terminal/pane route, then
submitted:

| Job | Command | Outcome | Finished at (+08:00) |
|---|---|---|---|
| a / ID 0 | `printf a-ok` | Success | 13:25:31.439432 |
| b / ID 1 | `exit 7` | Failed(7) | 13:25:31.786649 |
| c / ID 2 | `sleep 0.5; printf c-ok` | Success | 13:25:32.454664 |
| d / ID 3 | completion gate, then verified Herdr prompt | Success | 13:25:37.915885 |

D had **no success dependencies**. It started at 13:25:31.136387 in its own
control group and waited without occupying the worker slot. After all three
were Done, it wrote the result file, rechecked the original agent's identity
and idle status, then sent the result with `herdr agent prompt ... --wait`.

The actual assistant response—not an echoed input line—was:

```text
ACK:pq44-existing success=2 failed=1
```

A Python test driver submitted the jobs on behalf of the idle Codex; Codex was
not asked to enqueue them itself. This proves the completion-to-next-turn link,
not an unlimited autonomous agent loop.

### 3. Pueue → fresh real Codex — runtime verified

A fifth demonstration task ran after d, using the already-persisted result. It
created another no-focus shell pane, started Codex normally (no resume/fork),
and submitted only the handoff instructions and result data. It completed at
13:25:50.908799.

```text
ACK:pq44-fresh success=2 failed=1
```

The original native session was
`01a19fda-911a-7a61-a914-500d5e7b7282`; the fresh session was
`01a19fde-cc3e-70d1-9c86-a69485ea63bc`. Different identities plus the normal
startup command and transcript establish a fresh conversation. Normal
system/project instructions were still present: “fresh” does not mean no
instructions or persistent memory.

Both disposable panes were closed successfully. A subsequent `agent get` on
the old test target returned `agent_not_found`. The original Herdr server
remained 0.9.5, running and endpoint-compatible.

### 4. Core PTY, parent notes and templates — runtime verified, synthetic

All Core calls used a unique session and isolated HOME/XDG state, config,
runtime and socket. The archive was checksum-verified and checked for unsafe
archive members before extraction. A local Python receiver emitted OSC 7501,
logged raw input bytes, and ACKed received lines. No real agent was launched.

| Case | Observed result |
|---|---|
| `hc send --if idle` to explicit address | Bracketed paste + CR received, ACK emitted |
| `hc send --if working` | Input and ACK while receiver was working |
| Direct send while blocked | Exit **9**, error kind `blocked`; byte count stayed **141 → 141** |
| External `hc run --parent t1` | Child record had explicit `parent: t1` |
| Child exits with 0 | Parent received an `<hc>... exited (exit 0) ...</hc>` input note |
| Child exits while parent blocked | No new input during the additional 1-second observation; note arrived after controlled return to idle |
| Fresh scripted template | `first_message: {sent:true, started:true, turn:0}`; body and task ACKed, then idle |

The idle receiver successfully ACKed one message while `started:false` because
it deliberately never changed to working. This directly demonstrates why
**delivery and turn-start detection are different**.

The first template failed with exit 127 and `first_message.sent:false` because
the test enclosed the entire `command:` value in quotes. Core 0.1.17 retained
those quotes in its shell command. Removing the outer quotes made it pass;
see [the version-specific pitfall](../pitfalls/hc-template-exited-before-ready.md).
This is not a reason to stop quoting ordinary Agent Skills YAML frontmatter.

Five test terminals (including the failed-template attempt) were removed. The
isolated server stopped, its socket disappeared, and no test processes remained.
No legacy Herdr server was restarted or upgraded.

## Herdr versus Core: recommended boundary

| Need | Recommendation |
|---|---|
| Wake the agent already in a Herdr 0.9.5 pane | Herdr `agent get` + `agent prompt`, explicit endpoint and identity |
| Fresh conversation visible in the current workspace | Herdr `pane split --no-focus` + `agent start` + prompt |
| New headless persistent-terminal workflow | Evaluate Core independently, with OSC-capable programs/templates |
| Reliably preserve completion during session loss | Result artifact regardless of terminal runtime |
| Native thread messaging already available | Prefer it when verified; avoid unnecessary terminal dependency |

Core has its own addresses, registry and socket API. It does not turn an
existing Herdr agent into an hc-managed program merely because `hc` is installed.
Herdr can be an outer viewer for a new Core terminal, but that is different from
controlling the existing pane occupant.

At the inspected Core revision, child notes cover blocked/error/process exit,
not every done agent turn; `wait --children all` means no children working, not
all successful. Pueue tasks also do not automatically become Core children.
`--parent` links a new terminal but does not replace an external caller's
identity or automatically write the desired reply instruction. Children normally
die with the parent; fresh independent handoffs should explicitly avoid that
relationship, or deliberately choose `--outlive-parent`.

## Not verified / not promised

- **Real Codex or Claude under Core**, their OSC integrations, busy-input
  steering/queuing, or a complete Pueue → Core → LLM turn.
- Live Herdr fault injection for busy/blocked/replaced agents or network
  disconnect-after-submit. Those guards are supported by installed help/schema
  and source review, not claimed as live acceptance tests. The local receiver
  exit-42 test is not a real network-failure simulation.
- Automated trust/approval handling, cross-host routing, machine reboot recovery,
  parent-death cascades, or exactly-once delivery/side effects.
- Adversarial prompt-injection resistance. Smoke prompts marked job output as
  data but contained no hostile instruction. This is guidance, not a security
  evaluation of the model.
- Codex native `queue`: 0.166.0 help was inspected, not executed. `--resume` can
  warn and still exit successfully, so acceptance does not prove wake-up.

If Herdr identity is unavailable or has changed, stop automatic delivery.
Even an identity precheck is not atomic with `agent prompt`: the API accepts no
expected-session compare-and-send precondition. Record ambiguous delivery rather
than blindly retrying non-idempotent work.

## Reproduce / evidence pointers

Validation results: **12 new recipe tests passed**, **34 tests passed in the full
Pueue suite**; shell contracts, skill lint (0 errors / 0 warnings), `make validate`
and `git diff --check` passed. The existing description-length note remains
advisory; no trigger-text expansion was needed.

Portable queue tests (no model calls):

```bash
uv run --extra dev pytest skills/local/pueue-job-queue/tests/test_completion_handoff.py -q
uv run --extra dev pytest skills/local/pueue-job-queue/tests/ -q
bash skills/local/pueue-job-queue/tests/test_contracts.sh
```

For an opt-in Herdr smoke, follow the published reference with disposable panes:
first establish an idle test agent, save its identity, run a/b/c and the
completion gate in an isolated Pueue daemon, then call `agent prompt`. Inspect
the actual assistant response before cleanup; repeat with a new pane/session.
Use only synthetic data and bounded timeouts; stop rather than answer startup
approval/trust dialogs.

For Core, first isolate `HC_SESSION`, `HC_SOCKET`, `XDG_STATE_HOME`,
`XDG_CONFIG_HOME`, `XDG_RUNTIME_DIR` and caller identity. Even a listing command
can start a daemon. A receiver can report status with:

```python
os.write(1, b"\x1b]7501;state=idle:app=test\x1b\\")
```

Start it using `hc run --bg --json`, parse its returned address, send with
`--if idle`, then repeat with controlled working/blocked reports. Launch a short
child with explicit `--parent`, observe its exit note before/after unblocking,
and verify a scripted template's `first_message` fields. All comparisons must
use that test endpoint, never the user's normal socket.

Raw local evidence was retained at these **temporary, machine-local paths**;
they are not required by the skill or portable tests and may later expire:

- `/tmp/pueue-herdr-poc.j1PMPw/`: `run_live.py`, `deliver.py`, result/queue JSON,
  original/fresh transcripts and identities, per-call records, cleanup receipts.
- `/tmp/hc-poc-vxqunrgv/`: `scripts/repro.py`, OSC receiver, isolated CLI wrapper,
  `evidence/final-results.json`, command logs, received-byte logs and template retry.

## Sources

- [Herdr Core overview](https://herdr.dev/core/)
- [Pinned Core CLI](https://github.com/herdrdev/herdr-core/blob/b63ecbd1e6b6a7d63fb7bcf40f268930417723ba/docs/commands.md)
- [Core input gates](https://github.com/herdrdev/herdr-core/blob/b63ecbd1e6b6a7d63fb7bcf40f268930417723ba/crates/herdr-core/src/input.rs#L111-L220)
- [Core parent notes](https://github.com/herdrdev/herdr-core/blob/b63ecbd1e6b6a7d63fb7bcf40f268930417723ba/crates/herdr-core/src/notes.rs)
- [Core templates](https://github.com/herdrdev/herdr-core/blob/b63ecbd1e6b6a7d63fb7bcf40f268930417723ba/docs/templates.md)
- [Core isolation/security](https://github.com/herdrdev/herdr-core/blob/b63ecbd1e6b6a7d63fb7bcf40f268930417723ba/docs/security.md)
- [Herdr 0.9.5 API](https://github.com/herdrdev/herdr/blob/v0.9.5/docs/next/website/src/content/docs/socket-api.mdx)
- Installed `herdr` help/schema/status, `pueue add --help`, `codex queue --help`.
