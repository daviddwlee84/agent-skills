# Migrate an existing i18n + llmstxt site

Use this guide when a site created by an older `mkdocs-site-bootstrap` release
has both `mkdocs-static-i18n` and `mkdocs-llmstxt`, especially when:

- `llms.txt` / `llms-full.txt` is almost empty after adding a language;
- the files contain only the final locale;
- strict builds report `Page URI ... not found`; or
- CI removed `--strict` to make the build pass.

The safe target is a strict two-pass build: multilingual HTML in one pass,
default-language LLM artifacts in another, then validation and an atomic merge.

## Updating the skill is not the migration

From the downstream project's root, first download the current tooling:

```bash
npx skills@latest update mkdocs-site-bootstrap --project --yes
```

This updates the installed skill under `.agents/skills/`. It deliberately does
**not** edit the project's `mkdocs.yml`, workflow, Makefile, or scripts. Run the
migration tool separately and review its findings.

## Audit, preview, apply, verify

### 1. Audit without writing

```bash
bash .agents/skills/mkdocs-site-bootstrap/scripts/migrate-i18n-llmstxt.sh \
  --target-dir . --json
```

Audit is the default. Exit `10` is an expected result: it means the legacy
affected shape was found. Read `changes[]` and `manual_actions[]` in the JSON
before proceeding.

### 2. Preview the conservative patch

```bash
bash .agents/skills/mkdocs-site-bootstrap/scripts/migrate-i18n-llmstxt.sh \
  --target-dir . --apply --dry-run --json
```

`--apply --dry-run` computes the same patch as a real apply but writes nothing.
If a proposed change would replace intentional customization, stop and perform
that item manually.

### 3. Apply and run strict verification

```bash
bash .agents/skills/mkdocs-site-bootstrap/scripts/migrate-i18n-llmstxt.sh \
  --target-dir . --apply --verify --json
```

On a fully recognized old scaffold this:

- adds `docs_dir` and plugin environment guards to `mkdocs.yml`;
- rewrites the exact legacy snippets base path (`.`, `docs`,
  `docs/_snippets`) to follow the guarded docs directory;
- adds Material's `content.action.edit` feature;
- installs or refreshes the marker-owned `scripts/build-docs-site.py`;
- changes the exact scaffolded workflow/Makefile build command to invoke the
  helper; and
- adds the helper to the workflow path filter.

It also audits non-default `*.LOCALE.md` / `*.LOCALE.markdown` sources for
relative links to `llms.txt`, `llms-full.txt`, or generated `*/index.md`
sidecars. Each unsafe link is reported as a manual action; the tool does not
guess the deployment URL or rewrite prose automatically.

The tool stages and validates every candidate before replacing project files,
and the migration is idempotent. A second identical run reports `status: safe`
and `changed: false`. Verification invokes the helper (using
`uv run --extra docs` when the project declares that optional dependency
group), so both the default-language LLM pass and full multilingual HTML pass
remain strict.

## Exit codes and JSON

| Exit | Meaning |
|---:|---|
| `0` | Already safe, or migrated and verified with no manual work remaining |
| `10` | Audit/dry-run found an affected legacy configuration; no files changed |
| `11` | Safe apply completed, but `manual_actions[]` still requires work |
| `12` | The strict two-pass verification failed |
| `1` | Invalid arguments or incompatible flag use |
| `2` | Target/config file is missing |
| `4` | Required `yq`/config parsing or migration staging failed |

With `--json`, stdout is one object suitable for an agent or CI wrapper:

```json
{
  "status": "affected",
  "affected": true,
  "changed": false,
  "dry_run": false,
  "verified": null,
  "changes": [],
  "manual_actions": []
}
```

Diagnostics and build logs go to stderr. Do not treat exit `10` as a generic
tool crash; it is the audit signal that a migration is needed. `verified` is
`null` when verification was not requested, `true` after a successful helper
run, and `false` on exit `12`.

## Automatic patch boundary

The tool only edits shapes it can identify without guessing:

- absent `docs_dir`, or literal `docs_dir: docs`;
- the exact legacy `pymdownx.snippets.base_path` list `[., docs,
  docs/_snippets]`;
- map-form `i18n`, `llmstxt`, `copy-to-llm`, and optional `social` plugin
  entries whose `enabled` values are not already customized;
- a missing helper, or a helper carrying the exact
  `# mkdocs-site-bootstrap-managed: two-pass-build-v1` marker;
- the exact build line from the scaffolded GitHub workflow; and
- the exact scaffolded `docs-build` Makefile command.

It refuses to overwrite or infer around:

- a custom/out-of-repo `docs_dir` or symlinked source tree;
- top-level MkDocs `INHERIT` or a custom snippets `base_path` shape;
- custom plugin `enabled` expressions or non-map plugin shapes;
- a same-named helper without the managed marker;
- custom CI, deployment, or Makefile build logic;
- folder-layout i18n or an ambiguous default locale; and
- relative generated-artifact links inside localized sources.

Those cases are returned in `manual_actions[]`; exit `11` keeps them visible.
Do not use `--force` or copy over a foreign helper. Adapt the manual recipe
below to the project's existing conventions.

## Manual recipe for customized sites

Preserve the project's values while introducing these invariants:

```yaml
docs_dir: !ENV [MKDOCS_SITE_BOOTSTRAP_DOCS_DIR, docs]

theme:
  features:
    - content.action.edit

plugins:
  - i18n:
      enabled: !ENV [MKDOCS_SITE_BOOTSTRAP_I18N_ENABLED, true]
      # preserve the existing i18n settings
  - llmstxt:
      enabled: !ENV [MKDOCS_SITE_BOOTSTRAP_LLMSTXT_ENABLED, false]
      # preserve full_output and sections
  - copy-to-llm:
      enabled: !ENV [MKDOCS_SITE_BOOTSTRAP_COPY_TO_LLM_ENABLED, true]
      # preserve the existing settings

markdown_extensions:
  - pymdownx.snippets:
      base_path:
        - .
        - !ENV [MKDOCS_SITE_BOOTSTRAP_DOCS_DIR, docs]
      check_paths: true
```

If `social` exists, give it
`enabled: !ENV [MKDOCS_SITE_BOOTSTRAP_SOCIAL_ENABLED, true]` as well. Copy the
current canonical helper only when it will not overwrite a project-owned
script, then change production build entry points to:

```bash
uv run python scripts/build-docs-site.py
```

Keep direct `mkdocs serve` / `mkdocs build --strict` for HTML-only preview.
Root `/llms.txt`, `/llms-full.txt`, and `.md` sidecars intentionally represent
the default language only; do not create or link to guessed locale-relative
paths such as `/zh-TW/llms.txt`.

Replace reported generated-artifact links with full URLs derived from the
project's `site_url`, including any GitHub Pages repository subpath. For
example, use `https://owner.github.io/project/llms.txt`, not `/llms.txt`.

Finally, run the helper and inspect at least one default-language sidecar, one
translated HTML page, and both root llms files. Removing `--strict` or demoting
link warnings is not a migration: it can make CI green while leaving the LLM
artifacts corrupted.
