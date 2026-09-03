# `llms.txt` becomes nearly empty or switches locale after enabling MkDocs i18n

**Symptoms**: `Page URI 'index.md' not found in the generated pages`,
`Aborted with N warnings in strict mode!`, nearly empty root `llms.txt`, or
root links unexpectedly pointing at the final locale
**First seen**: 2026-09
**Affects**: `mkdocs-llmstxt` 0.5.0 with `mkdocs-static-i18n` 1.3.1
**Status**: workaround implemented in `mkdocs-site-bootstrap` two-pass build v1

## Symptom

A site builds correctly before adding `mkdocs-static-i18n`. After adding a
second locale, `site/llms.txt` and `site/llms-full.txt` shrink to a heading or
contain only the translated locale.

With explicit llmstxt section paths, a strict build also reports messages such
as:

```text
Page URI 'index.md' not found in the generated pages. Skipping.
Page URI 'getting-started.md' not found in the generated pages. Skipping.
Aborted with 2 warnings in strict mode!
```

Removing `--strict` makes the command exit successfully, but the generated
files remain wrong. A glob-heavy configuration can hide the size change while
silently leaving the final locale in the root llms output.

## Root cause

`mkdocs-static-i18n` performs a complete MkDocs build for each configured
locale. `mkdocs-llmstxt` treats each invocation as a fresh build: it clears its
collected page state, resolves `sections:` against that locale's source URIs,
and writes the same root `llms.txt` / `llms-full.txt` paths.

The last locale therefore overwrites the valid default-language artifacts.
Translated suffixes such as `index.zh-TW.md` no longer match an explicit
`index.md` lookup; globs may match translated pages instead. Plugin order and
`reconfigure_material` do not change the shared state/output-path collision.

## Workaround

For a site scaffolded by the current `mkdocs-site-bootstrap`, build the
deployable artifact with the managed helper:

```bash
uv run python scripts/build-docs-site.py
```

It runs a strict default-language-only llmstxt pass and a separate strict
multilingual HTML pass, validates and merges the outputs, then replaces `site/`
only after both succeed. Root llms files and `.md` sidecars intentionally
represent the default language; translated HTML remains under its locale URL.

For an older downstream scaffold, update the skill and run the audit-first
migration:

```bash
npx skills@latest update mkdocs-site-bootstrap --project --yes
bash .agents/skills/mkdocs-site-bootstrap/scripts/migrate-i18n-llmstxt.sh \
  --target-dir . --json
bash .agents/skills/mkdocs-site-bootstrap/scripts/migrate-i18n-llmstxt.sh \
  --target-dir . --apply --verify --json
```

Exit `10` from the first command means the affected legacy shape was detected;
it is not a generic script failure.

## Prevention

- Keep llmstxt disabled by default in direct MkDocs builds. Only the helper
  enables it inside the isolated default-language pass.
- Use the helper in CI, release, and deploy entry points. Direct `mkdocs serve`
  or `mkdocs build --strict` is an HTML-only preview.
- Keep strict enabled in both passes and assert that llms sections/sidecars are
  non-empty and contain no translated-locale URLs.
- Never treat `--drop-strict`, plugin reordering, or globbing as a fix. They can
  hide the warning without repairing the artifact.
- Keep root `/llms.txt`, `/llms-full.txt`, and raw `.md` endpoint links scoped
  to the default language; do not invent `/zh-TW/llms.txt` unless a separate
  locale-aware generator is deliberately implemented.

## Where this was hit

The issue was reproduced on 2026-09-02 against `mkdocs-llmstxt` 0.5.0 and a
suffix-layout `mkdocs-static-i18n` site. The two-page starter scaffold's
`llms-full.txt` fell from roughly 1.5 KB to about 70 bytes after adding zh-TW;
the larger dogfood site retained a substantial file but its root links all
pointed at the final locale. Existing tests missed it because their only i18n
fixture removed llmstxt before building.
