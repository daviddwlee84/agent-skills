# Zensical says "No issues found" but llms.txt contains only headings

## Symptom

With Zensical 0.0.73, `zensical build --strict` prints:

```text
Build started
No issues found
Build finished in 0.45s
```

But `llms.txt` contains only the site and section headings, and root source
pages have no exported Markdown counterparts or Copy as Markdown buttons.

Still reproduces with Zensical 0.1.2 (rechecked 2026-11-20): with only
`**/*.md`, root `index.md` is missing from `llms.txt` while nested pages appear.

## Root cause

The native llmstxt section used only `Documentation = ["**/*.md"]`.
In the tested release, that pattern did not select `docs/index.md` or other
root-level pages. A strict build does not reject an empty matched section.

## Workaround

Cover both root and nested source paths:

```toml
[project.plugins.llmstxt.sections]
Documentation = ["*.md", "**/*.md"]
```

Explicit source paths are also appropriate for a curated section.

## Prevention

Compare the llms index with the intended source inventory; validate exported
Markdown, full output, and copy-button URLs. A successful build and the mere
existence of `llms.txt` are not sufficient. Recheck these patterns when updating
Zensical rather than assuming another tool's glob semantics apply.
