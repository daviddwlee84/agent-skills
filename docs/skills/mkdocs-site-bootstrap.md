# mkdocs-site-bootstrap

Bootstrap a MkDocs Material documentation site for a repo and (optionally)
deploy it to GitHub Pages — including the same stack this very docs site
uses (Material + `mkdocs-llmstxt` + `mkdocs-copy-to-llm` + `pymdownx.snippets`,
GitHub Pages workflow with paths-filter). Multilingual sites use a strict
two-pass build so root llms files remain complete and default-language-only.

This skill is **consent-gated**. It records preferences in
`.skills/preferences.yaml` so it doesn't re-ask on every session, never
auto-migrates a user's existing `docs/` content, and gates the
`gh api -X POST .../pages` call on explicit user confirmation.

!!! warning "Already using an older version of this skill?"
    Updating the installed skill only downloads the fixed build and migration
    tools; it does **not** change your project. If i18n made `llms.txt` nearly
    empty, switched it to the final locale, or forced CI to drop strict, follow
    [Migrate an existing site](#migrate-an-existing-site) below.

## Quick start

```bash
# 1. Scaffold the site files
bash skills/local/mkdocs-site-bootstrap/scripts/init-docs-site.sh \
  --site-name "My Project" \
  --repo-slug owner/repo \
  --site-url https://owner.github.io/repo/

# 2. Build the complete strict artifact (HTML + default-language llms)
uv sync --extra docs
uv run python scripts/build-docs-site.py

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
| `init-docs-site.sh` | Scaffold config, docs, workflow, and the managed production build helper |
| `build-docs-site.py` | Strict production build; isolates multilingual HTML from default-language llms output |
| `enable-pages.sh` | Enable Pages via `gh api` and trigger first deploy |
| `add-docs-page.sh` | Create a new `docs/` page and insert it into `mkdocs.yml` nav |
| `check-preferences.sh` | Read/set/reset entries in `.skills/preferences.yaml` |
| `add-language.sh` | Add a suffix-layout non-default language and translation stubs |
| `migrate-i18n-llmstxt.sh` | Audit or conservatively migrate an older i18n + llmstxt scaffold |

All scripts support `--help` and `--dry-run`.

## Production build vs preview

Use this for anything you deploy:

```bash
uv run python scripts/build-docs-site.py
```

On a multilingual site with llmstxt, the helper runs a strict default-language
llmstxt pass, a separate strict multilingual HTML pass, validates both, merges the root
artifacts, and only then replaces `site/`. `/llms.txt`, `/llms-full.txt`, and
the raw `.md` sidecars intentionally represent the default language only.

Direct `uv run mkdocs build --strict` and `uv run mkdocs serve` are safe
HTML-only previews because the scaffold disables llmstxt unless the helper
enables it. Do not deploy a direct multilingual build if llms output is part of
the site's contract.

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

## Bilingual / multilingual docs

Add a suffix-layout locale such as zh-TW without moving existing pages:

```bash
bash skills/local/mkdocs-site-bootstrap/scripts/add-language.sh --lang zh-TW
uv sync --extra docs
uv run python scripts/build-docs-site.py
```

The script creates `*.zh-TW.md` stubs, adds/configures
`mkdocs-static-i18n`, and preserves strict plus default-language llms output.
`--remove-llmstxt` is the explicit opt-out. The legacy `--drop-strict` flag is
a deprecated no-op because dropping strict hid warnings without fixing the
corrupted files; `--keep-llmstxt` is a deprecated alias for the default.
Exit `11` means the language was added but custom downstream build files still
need the migration tool's reported manual actions.

See the
[`i18n guide`](https://github.com/daviddwlee84/agent-skills/blob/main/skills/local/mkdocs-site-bootstrap/references/i18n-guide.md)
for the terminology rule, plugin guards, output contract, and build details.

## Migrate an existing site

Run the migration audit from the downstream project root:

```bash
npx skills@latest update mkdocs-site-bootstrap --project --yes

bash .agents/skills/mkdocs-site-bootstrap/scripts/migrate-i18n-llmstxt.sh \
  --target-dir . --json
```

Exit `10` means the affected legacy shape was found and nothing was changed.
Preview, then apply and verify:

```bash
bash .agents/skills/mkdocs-site-bootstrap/scripts/migrate-i18n-llmstxt.sh \
  --target-dir . --apply --dry-run --json

bash .agents/skills/mkdocs-site-bootstrap/scripts/migrate-i18n-llmstxt.sh \
  --target-dir . --apply --verify --json
```

The tool only patches recognizable scaffold-owned config, workflow, Makefile,
and managed-helper shapes. Custom values or a foreign same-named helper are
reported in `manual_actions[]` and left untouched; exit `11` keeps that work
visible. It also reports unsafe relative llms/sidecar links in localized source
pages for manual replacement with full `site_url`-based URLs. See the full
[`migration guide`](https://github.com/daviddwlee84/agent-skills/blob/main/skills/local/mkdocs-site-bootstrap/references/i18n-llmstxt-migration.md).

## Why a skill, not a one-shot script?

Because docs sites are not a one-shot setup — they evolve. The skill exists
to:

1. Get the initial scaffold right (consent-gated, idempotent).
2. Keep helping with `add-docs-page.sh` over time.
3. Remember what the user already decided so future sessions don't pester.
4. Provide a place to encode the gotchas (linking rules, snippets dir,
   `pages: write` permission, i18n/llmstxt lifecycle isolation, etc.) so they
   don't get re-discovered every project.

The bundled `references/docs-stack-recipe.md` documents what the stack
actually is, so a user who wants to apply pieces manually has the recipe
without invoking the skill.

## Canonical SKILL.md

See [skills/local/mkdocs-site-bootstrap/SKILL.md](https://github.com/daviddwlee84/agent-skills/blob/main/skills/local/mkdocs-site-bootstrap/SKILL.md)
for the full triggering description, workflow, and gotchas.
