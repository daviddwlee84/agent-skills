# Getting started

## Local development

```bash
# Install docs dependencies
uv sync --extra docs

# Serve at http://127.0.0.1:8000/
uv run mkdocs serve

# Strict HTML preview (llms.txt is intentionally disabled here)
uv run mkdocs build --strict

# Complete strict artifact build (CI runs this)
uv run python scripts/build-docs-site.py
```

## Deploying

The [`docs.yml`](https://github.com/{{REPO_SLUG}}/blob/main/.github/workflows/docs.yml)
workflow auto-deploys to GitHub Pages on every push to `main` that touches
`docs/**`, `mkdocs.yml`, `pyproject.toml`, `uv.lock`, or the managed build
helper.

To deploy manually: trigger the **Docs** workflow from the Actions tab.

## Adding a new page

1. Create the markdown file under `docs/` in the appropriate section.
2. Add it to the `nav:` block in `mkdocs.yml`.
3. Run `uv run python scripts/build-docs-site.py` to verify all artifacts.
4. Commit + push.
