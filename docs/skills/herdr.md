# herdr (vendored)

Vendored from the official
[`herdrdev/herdr/skills/herdr`](https://github.com/herdrdev/herdr/tree/master/skills/herdr)
skill under Apache-2.0. It is synchronized through `vendor.yaml`; do not edit
the vendored files locally because `make sync` replaces them.

## What it teaches

The skill gives an agent the safe operating model for Herdr's session,
workspace, tab, pane, and recognized-agent APIs. It emphasizes explicit IDs,
JSON responses, `--current`, non-destructive background panes, lifecycle-aware
waiting, and the difference between raw pane control and agent control.

It intentionally triggers only when the user explicitly asks to use Herdr and
requires `HERDR_ENV=1` before controlling a live session.

## Version alignment

This vendored copy is suitable for catalog discovery and generic installs. A
machine that also installs the Herdr binary should prefer the exact skill
emitted by that binary:

```bash
herdr --skill > ~/.agents/skills/herdr/SKILL.md
```

That keeps CLI syntax and skill guidance on the same release, including preview
builds. The accompanying dotfiles implement this automatically.

## Canonical SKILL.md

See
[`skills/vendor/herdr/SKILL.md`](https://github.com/daviddwlee84/agent-skills/blob/main/skills/vendor/herdr/SKILL.md)
for the full instructions.
