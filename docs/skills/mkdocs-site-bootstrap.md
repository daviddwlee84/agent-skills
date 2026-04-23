# mkdocs-site-bootstrap

Bootstrap a MkDocs Material documentation site for a repo and (optionally)
deploy it to GitHub Pages — including the same stack this very docs site
uses (Material + `mkdocs-llmstxt` + `mkdocs-copy-to-llm` + `pymdownx.snippets`,
GitHub Pages workflow with paths-filter).

This skill is **consent-gated**. It records preferences in
`.skills/preferences.yaml` so it doesn't re-ask on every session, never
auto-migrates a user's existing `docs/` content, and gates the
`gh api -X POST .../pages` call on explicit user confirmation.

## Quick start

```bash
# 1. Scaffold the site files
bash skills/local/mkdocs-site-bootstrap/scripts/init-docs-site.sh \
  --site-name "My Project" \
  --repo-slug owner/repo \
  --site-url https://owner.github.io/repo/

# 2. Verify locally
uv sync --extra docs && uv run mkdocs build --strict

# 3. Enable GitHub Pages and trigger first deploy (consent gate)
bash skills/local/mkdocs-site-bootstrap/scripts/enable-pages.sh \
  --repo owner/repo

# 4. Add new pages over time
bash skills/local/mkdocs-site-bootstrap/scripts/add-docs-page.sh \
  --section Reference --title "API schema"
```

## Bundled scripts

| Script | Purpose |
|---|---|
| `init-docs-site.sh` | Scaffold `mkdocs.yml`, `pyproject.toml`, `docs/`, `.github/workflows/docs.yml` |
| `enable-pages.sh` | Enable Pages via `gh api` and trigger first deploy |
| `add-docs-page.sh` | Create a new `docs/` page and insert it into `mkdocs.yml` nav |
| `check-preferences.sh` | Read/set/reset entries in `.skills/preferences.yaml` |

All scripts support `--help` and `--dry-run`.

## Preferences

The skill writes to `<repo>/.skills/preferences.yaml`:

```yaml
mkdocs_site_bootstrap:
  enabled: true
  decided_at: "2026-04-23"
  stack: mkdocs-material
  auto_deploy: true
  pages_deployed: true
  existing_docs_decision: skipped
  site_url: https://owner.github.io/repo/
  repo_slug: owner/repo
```

To change your mind:

```bash
# Reset (returns to "never asked" state)
bash skills/local/mkdocs-site-bootstrap/scripts/check-preferences.sh \
  --reset mkdocs_site_bootstrap

# Or explicitly opt out so the agent stops asking
bash skills/local/mkdocs-site-bootstrap/scripts/check-preferences.sh \
  --set mkdocs_site_bootstrap.enabled=false
```

See [`references/preferences-schema.md`](https://github.com/daviddwlee84/agent-skills/blob/main/skills/local/mkdocs-site-bootstrap/references/preferences-schema.md)
for the full schema and conventions for cross-skill preference use.

## Existing `docs/` content

The skill detects pre-existing `docs/` content and asks before doing
anything. It will **never** auto-migrate, rename, or rewrite user files.
Three consent options:

- **skip** — leave docs alone, just create `mkdocs.yml` with empty nav (auto)
- **wrap** — same, but populate `nav:` from existing files alphabetically
- **manual** — bail out, user reorganizes first then re-runs

See [`references/existing-docs-handling.md`](https://github.com/daviddwlee84/agent-skills/blob/main/skills/local/mkdocs-site-bootstrap/references/existing-docs-handling.md)
for the full decision tree.

## Why a skill, not a one-shot script?

Because docs sites are not a one-shot setup — they evolve. The skill exists
to:

1. Get the initial scaffold right (consent-gated, idempotent).
2. Keep helping with `add-docs-page.sh` over time.
3. Remember what the user already decided so future sessions don't pester.
4. Provide a place to encode the gotchas (linking rules, snippets dir,
   `pages: write` permission, etc.) so they don't get re-discovered every
   project.

The bundled `references/docs-stack-recipe.md` documents what the stack
actually is, so a user who wants to apply pieces manually has the recipe
without invoking the skill.

## Canonical SKILL.md

See [skills/local/mkdocs-site-bootstrap/SKILL.md](https://github.com/daviddwlee84/agent-skills/blob/main/skills/local/mkdocs-site-bootstrap/SKILL.md)
for the full triggering description, workflow, and gotchas.
