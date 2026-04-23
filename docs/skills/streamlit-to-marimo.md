# streamlit-to-marimo (vendored)

Vendored from
[marimo-team/skills/skills/streamlit-to-marimo](https://github.com/marimo-team/skills/tree/main/skills/streamlit-to-marimo).
Synced via [`make sync`](https://github.com/daviddwlee84/agent-skills/blob/main/Makefile);
do not edit
[`skills/vendor/streamlit-to-marimo/SKILL.md`](https://github.com/daviddwlee84/agent-skills/blob/main/skills/vendor/streamlit-to-marimo/SKILL.md)
locally — changes will be clobbered on the next sync.

## Upstream frontmatter description

> Convert a Streamlit app to a marimo notebook.

## What it teaches

Migration patterns from Streamlit's imperative, re-run-the-whole-script
model to marimo's reactive DAG. Covers how `st.session_state`,
`st.cache_data`, and Streamlit widgets map to marimo equivalents —
typically `mo.state`, `@functools.cache` or cell-level reactivity, and
`mo.ui.*`.

## Related local skills

- [`marimo-batch-mlflow`](marimo-batch-mlflow.md) — if the Streamlit app
  was being used as both an interactive UI and a script, the converted
  marimo notebook can adopt the dual-mode pattern.

## Canonical SKILL.md

See
[skills/vendor/streamlit-to-marimo/SKILL.md](https://github.com/daviddwlee84/agent-skills/blob/main/skills/vendor/streamlit-to-marimo/SKILL.md)
for the full migration checklist. Upstream source:
[marimo-team/skills](https://github.com/marimo-team/skills).
