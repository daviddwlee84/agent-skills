# Core template: "it exited before it was ready" with exit 127

Observed with **Herdr Core 0.1.17**, 2026-11-03, in an isolated scripted-template
smoke test. See [the evaluation](../backlog/pueue-herdr-continuation.md).

## Symptom

`hc run --bg --json ... <template> <task>` reports `first_message.sent: false`
with reason:

```text
it exited before it was ready
```

`hc get <returned-address>` shows `exit_code: 127`. Its argv includes a shell
command whose **entire executable-plus-arguments string remains quoted**:

```json
["sh", "-c", "\"/absolute/python3 -I /absolute/receiver.py --label template\""]
```

## Root cause

The template's command field was written as:

```text
command: "/absolute/python3 -I /absolute/receiver.py --label template"
```

In this Core release, the template parser preserved the enclosing quotes in the
command string. The shell interpreted the whole line as one executable name,
not an executable followed by arguments. It exited before readiness could be
reported; this was not an OSC readiness timeout.

## Workaround

Remove the quotes around the **whole command**:

```text
command: /absolute/python3 -I /absolute/receiver.py --label template
```

Still shell-quote individual arguments/paths where necessary. The corrected
scripted template reported `first_message.sent: true`, `started: true`, and its
receiver ACKed the body and task.

## Prevention

- Follow the installed `hc --skill` and template format, not assumptions that
  all frontmatter-looking formats have full YAML scalar decoding.
- Inspect the returned terminal's argv and exit code before retrying or changing
  readiness settings. `--bg` success alone does not prove initial delivery.
- Do not use `ready: quiet` to hide an executable/quoting failure.
- This is version-specific to Core templates, **not ordinary Agent Skills
  `SKILL.md` YAML**. Keep following this repository's frontmatter quoting rules.
- Recheck behavior after a Core upgrade; do not generalize the workaround to
  future parsers without verifying the installed binary.
