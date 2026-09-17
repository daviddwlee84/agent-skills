# Importing vectorbt raises an invalid `scattermapbox` template property

Observed on 2026-09-17 while testing the VectorBT skill in an isolated Python
3.12 environment with `vectorbt==1.1.0` and `plotly==7.1.0`.

## Symptom

`import vectorbt` fails during plotting template registration, before any
strategy or data loading executes. The exception identifies
`plotly.graph_objs.layout.template.Data` and ends with:

```text
Bad property path:
scattermapbox
^^^^^^^^^^^^^
```

## Cause

This OSS release registers a Plotly template containing `scattermapbox`, which
Plotly 7.1.0 no longer accepts. Its open-ended Plotly dependency allowed that
combination to resolve even though importing the package failed.

## Workaround verified here

In the isolated test environment, selecting `plotly==5.24.1` allowed OSS 1.1.0
to import and pass a deterministic two-order backtest on Python 3.12. Do not
apply this constraint to unrelated projects or future versions automatically;
check the installed versions and upstream changes first.

## Prevention

Run an actual import and a small simulation when preparing a library environment,
then record the compatible dependencies in that project's lockfile. Successful
dependency resolution is not proof of runtime compatibility. Classify this as
an environment issue instead of proposing an OSS-to-PRO migration to fix it.
