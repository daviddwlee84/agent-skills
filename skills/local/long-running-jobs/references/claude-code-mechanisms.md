# Claude Code mechanisms for waiting

Which Claude Code tool implements each tier of the ladder, and which ones do
*not* do what their name suggests.

> Verified against Claude Code **2.1.220** (model-facing strings extracted from
> the shipped binary) plus a live experiment. Tool availability varies by
> version and deployment, so check what your session actually exposes before
> relying on any of this.

## The short version

| Tier | Claude Code mechanism |
|---|---|
| 0 — scheduler owns the chain | Nothing Claude-specific. `sbatch --dependency`, `pueue --after`. Best precisely *because* the harness is not involved. |
| 1 — one blocking wait | **`Bash` with `run_in_background: true`** |
| 2 — stream filtered events | **`Monitor`** (when exposed) |
| 3 — scheduled check-in | `CronCreate` / `ScheduleWakeup` |

## Tier 1: `run_in_background` wakes you on exit

This is the load-bearing fact for the whole skill:

> **A backgrounded Bash command notifies the agent when the process exits.**

The tool result says so explicitly — *"You will be notified when it completes"*
— and a completion notification arrives carrying the exit code and an output
file path. Verified by experiment, not inference.

So the correct shape for "wait until this finishes" is a **single** background
call on a command that blocks:

```bash
sbatch --wait phase_a.sbatch
```

Not a loop, not a poll, not a scheduled re-check. You are woken once, when it
is actually done.

The harness's own guidance agrees, and is explicit that this — not `Monitor` —
is the completion-waiting tool:

> "Use the Monitor tool to stream events from a background process (each stdout
> line is a notification). For one-shot \"wait until done,\" use Bash with
> `run_in_background` instead."

**Beware stale advice.** Public documentation summaries have claimed the agent
must poll `/tasks` or read the output file to discover completion. That is not
the behaviour of current builds. If in doubt, test it: background a
`sleep 30; echo done` and see whether a notification arrives.

Related behaviour worth knowing:

- A foreground command that hits its timeout is **auto-backgrounded** rather
  than killed — except commands starting with `sleep`.
- The command keeps running across turns.

## Foreground `sleep` is blocked

Do not try to "wait a bit" with a plain `sleep` in a normal Bash call. The
harness blocks it and tells you what to do instead:

> "To wait for a condition, use Monitor with an until-loop (e.g.
> `until <check>; do sleep 2; done`). To wait for a command you started, use
> `run_in_background: true`. **Do not chain shorter sleeps to work around this
> block.**"

Note that `sleep` *inside* an `until` loop, or inside a backgrounded script, is
fine — the block is on burning a foreground turn doing nothing.

## Tier 2: `Monitor`

`Monitor` runs a background source and turns **each output line into an
event**, so you can react mid-run. Sources are a command, and (newer builds) a
WebSocket URL.

Use it when you need to know about things *during* the run — early stopping, a
CUDA OOM, a metric threshold — not merely that it ended.

Two rules:

1. **Filter at the shell, not in context.** Pipe through
   `stdbuf -oL grep --line-buffered -E '<milestones>'`. A bare `tail -F` on a
   training log makes every epoch line an event, which is worse than the poll
   you were trying to replace.
2. **Handle its absence.** `Monitor` exists in the 2.1.220 binary but is *not
   exposed in every session's toolset*, and it is unavailable on some
   deployments (Bedrock / Vertex-style backends) and when telemetry is
   disabled. If you cannot see it, fall back to Tier 1 with a filtering wrapper
   that exits on the first milestone.

Whether a `Monitor` command is *event-driven* or *polling* is entirely up to
the command you give it. `until kill -0 "$PID"; do sleep 60; done` is a poll —
a cheap one, outside your context, which is the whole point. `python train.py`
blocking on its own child is genuinely event-driven.

## Tier 3: `CronCreate` / `ScheduleWakeup`

The mechanism the rest of this skill is trying to talk you out of, for the
usual case. Real limits:

- **Session-scoped.** Tasks only fire while the session is running and idle.
  Close the terminal and nothing fires. This alone disqualifies cron as the
  guardian of a Phase A → Phase B chain.
- **Recurring tasks auto-expire after 7 days.**
- **Each tick costs a full context read.** In a 400k-token session that is the
  most expensive possible way to learn "still training".
- Tasks fire between turns, never interrupting a response.

Legitimate remaining uses: a job on a machine you hold no blocking handle to; a
genuinely periodic duty (a nightly report) rather than a wait; a long fallback
heartbeat *behind* a Tier 0/1 mechanism, in case the primary signal never
arrives.

If you must use it, make the tick cheap — check one thing, say one line — and
delete the task once the real signal lands.

## Plugin-armed monitors

A plugin can ship persistent monitors so the host arms them without the model
having to. Declared in `monitors/monitors.json` at the plugin root (or a path
given in the manifest), each entry has:

| Field | Meaning |
|---|---|
| `name` | *"Identifier for this monitor, unique within the plugin. Used to dedupe so re-arming (plugin reload, repeat skill invoke) does not spawn duplicates."* |
| `description` | *"Short human-readable description of what is being monitored (shown in task panel and notification summary)."* |
| `trigger` | *"`always` arms at session start and on plugin reload. `on-skill-invoke:<skill>` arms the first time that skill is dispatched."* |

These run **unsandboxed, at the same trust tier as hooks**, so treat them with
hook-level caution. They also *"cannot safely reference `${user_config.*}`"* —
have the monitor script read config from a file instead.

Worth it for a watch that should exist for every session in a project. Overkill
for one training run.

## Push instead of pull: Channels

Channels invert the direction — an external system pushes an event *into* a
running session, rather than the session reaching out. A completed Slurm job
could POST a webhook that surfaces in your session.

Constraints as of this writing: research preview, MCP-based, requires the
session to be open with channels enabled, and unavailable on some deployments.
Worth knowing about; not something to build a training pipeline on today.

## What none of these do

**No Claude Code mechanism keeps your pipeline alive when the session ends.**
Hooks fire on session lifecycle events, not on external job completion. Cron
tasks stop with the session. Channels need a live session to receive into.

That is the entire argument for Tier 0 and for the durable-marker invariant:
the scheduler and the filesystem outlive the agent, so put the chain and the
completion record there.
