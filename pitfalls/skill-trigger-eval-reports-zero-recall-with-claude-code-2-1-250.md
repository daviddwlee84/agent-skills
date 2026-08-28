# Trigger eval reports 0% recall for every positive skill query

## Symptom

With Claude Code 2.1.250, the vendored `skill-creator` description optimizer
reported results like:

```text
precision=100% recall=0% accuracy=50%
rate=0/3 expected=True
```

All positive queries appeared not to trigger, while every negative query passed.
Changing the description could make an entire batch report `0/3` again. Bulk
tests also silently treated API timeouts as non-trigger decisions.

## Root cause

`skills/vendor/skill-creator/scripts/run_eval.py` creates temporary files under
`.claude/commands/` and then watches for a `Skill` or `Read` tool call. That does
not exercise the same discovery surface as a real Agent Skill installed under
`.claude/skills/` in Claude Code 2.1.250. The runner also returns `False` for
timeouts and subprocess errors, conflating "no routing decision" with "the model
decided not to use the skill."

## Workaround

1. Copy the complete skill into an isolated temporary project's
   `.claude/skills/<skill-name>/` directory.
2. Run `claude -p` from that project and restrict available tools to
   `Skill,Read` so the routing decision terminates quickly.
3. Record `trigger`, `no_trigger`, `other_tool`, `timeout`, and `error` as
   separate outcomes.
4. Exclude undecided timeout/error runs from accuracy instead of counting them
   as negative decisions.
5. Reduce concurrency when the CLI/API starts returning whole batches of
   timeouts. If the external router remains unstable, use multiple independent,
   label-blind router judgments and disclose that fallback in the benchmark.

## Prevention

The hard invariant is: **a trigger benchmark must exercise the same skill
discovery path users install, and only completed routing decisions may affect
precision/recall.** A command-file proxy or an undecided timeout is not evidence
that a skill should not trigger.
