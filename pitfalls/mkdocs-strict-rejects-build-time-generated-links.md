# MkDocs strict mode rejects links to build-time-generated files

## Symptom

```
WARNING -  Doc file 'index.md' contains a link 'llms.txt', but the
target is not found among documentation files.
WARNING -  Doc file 'index.md' contains a link 'getting-started/index.md',
but the target is not found among documentation files.
...
Aborted with 3 warnings in strict mode!
```

The link works when you visit the deployed site (the file *does* exist
in `site/` after build) but `mkdocs build --strict` refuses to ship it.

## Root cause

MkDocs validates relative links during the build by checking each
target against `docs/` source files, **not** against what the build
will produce. So:

- `mkdocs-llmstxt` plugin generates `site/llms.txt` and
  `site/llms-full.txt` at build time → links to `llms.txt` from a
  `docs/` page have no source-file counterpart.
- `use_directory_urls: true` rewrites `docs/getting-started.md` →
  `site/getting-started/index.md` → links written as
  `getting-started/index.md` (the post-build directory URL form, used
  by the [llmstxt.org spec](https://llmstxt.org/) for raw-markdown
  endpoints) similarly have no `docs/getting-started/index.md` source.

Both produce `WARNING` (not `INFO`), and `--strict` promotes warnings
to errors → build fails.

## Workaround

Two options. **Prefer relative links + `validation.links.not_found:
info`** so future agent-readable URLs stay portable:

```yaml
# mkdocs.yml
validation:
  links:
    not_found: info
```

```markdown
- [`llms.txt`](llms.txt)
- [`llms-full.txt`](llms-full.txt)
- [`getting-started/index.md`](getting-started/index.md)
```

Strict mode now passes; the link still works in the deployed site.

The fallback is to use absolute `https://...` URLs, but those couple
the docs source to a specific deploy URL and break local preview from
a different `site_url`. Avoid unless there's no alternative.

`validation.links.unrecognized_links` (the obvious-looking config key)
**does not work for this case** — it only demotes already-INFO-level
"unrecognized relative link" messages (like links to `../scripts/`
outside `docs/`). The build-output-link case is `not_found` severity.

## Prevention

- **Default to relative links** in `docs/` so the source can move
  between sites without rewriting URLs.
- When linking to a build-time-generated file (anything from
  `mkdocs-llmstxt`, `mkdocs-gen-files`, `mkdocstrings`, etc.), also
  set `validation.links.not_found: info` in `mkdocs.yml`.
- Keep `--strict` enabled in the deploy workflow — `info`-level
  messages don't fail the build, but real broken `*.md → *.md` links
  still do (because those would be `not_found` for a *different*
  reason: the source file truly doesn't exist).
- The `mkdocs-site-bootstrap` skill's
  `assets/mkdocs.yml.template` should ship with this validation
  override pre-set so downstream sites don't rediscover this.

## Where this was hit

Commit `14a57a2` added a "For AI assistants" section to
`docs/index.md` linking to `/llms.txt`, `/llms-full.txt`, and
`/getting-started/index.md`. Tried `validation.links.unrecognized_links:
info` first — wrong key (still failed). Then used absolute URLs as a
quick fix. Final commit (this one) reverted to relative URLs with
`validation.links.not_found: info`, matching the
"prefer relative links" repo convention.
