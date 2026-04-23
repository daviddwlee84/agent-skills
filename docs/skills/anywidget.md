# anywidget (anywidget-generator)

Vendored from
[marimo-team/skills/skills/anywidget](https://github.com/marimo-team/skills/tree/main/skills/anywidget).
Synced via [`make sync`](https://github.com/daviddwlee84/agent-skills/blob/main/Makefile);
do not edit
[`skills/vendor/anywidget/SKILL.md`](https://github.com/daviddwlee84/agent-skills/blob/main/skills/vendor/anywidget/SKILL.md)
locally — changes will be clobbered on the next sync.

> **Note on the runtime name:** the SKILL.md frontmatter declares
> `name: anywidget-generator`. Skill discovery uses the frontmatter name,
> not the directory name. The directory is kept as `anywidget/` to mirror
> the upstream path.

## What it teaches

Generating [anywidget](https://anywidget.dev/) components for marimo
notebooks:

- Vanilla JavaScript in `_esm` with a `render({ model, el })` function.
- `_css` styling that works in both light and dark mode (via
  `@media (prefers-color-scheme: dark)`).
- The `model.get` / `model.set` / `model.save_changes` pattern for
  syncing state between Python (`traitlets.Int(0).tag(sync=True)`) and JS.
- Wrapping for marimo display: `widget = mo.ui.anywidget(MyWidget())`.
- Reading `_esm` / `_css` from external files via `pathlib` when the
  widget grows large.

## Quick example

```python
import anywidget
import traitlets
import marimo as mo

class CounterWidget(anywidget.AnyWidget):
    _esm = """
    function render({ model, el }) {
      let count = () => model.get("number");
      let btn = document.createElement("button");
      btn.innerHTML = `count is ${count()}`;
      btn.addEventListener("click", () => {
        model.set("number", count() + 1);
        model.save_changes();
      });
      model.on("change:number", () => {
        btn.innerHTML = `count is ${count()}`;
      });
      el.appendChild(btn);
    }
    export default { render };
    """
    _css = "button { font-size: 14px; }"
    number = traitlets.Int(0).tag(sync=True)

widget = mo.ui.anywidget(CounterWidget())
widget
```

Then from another cell, `widget.value["number"]` gives you the current count.

## Related skills

- [`marimo-notebook`](https://github.com/daviddwlee84/agent-skills/blob/main/skills/vendor/marimo-notebook/SKILL.md)
  — general marimo authoring (vendored from marimo-team).
- [`marimo-batch-mlflow`](marimo-batch-mlflow.md) — uses `mlflow-widgets`
  (an anywidget-based MLflow component library) for live training charts;
  this skill is what you'd reach for if you needed to build a custom
  variant.

## Canonical SKILL.md

See
[skills/vendor/anywidget/SKILL.md](https://github.com/daviddwlee84/agent-skills/blob/main/skills/vendor/anywidget/SKILL.md)
for the full triggering description and best-practices section.
