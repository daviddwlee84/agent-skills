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

Keep strict link validation and use the final deployed URL for generated
artifacts that have no source file:

```markdown
- [`llms.txt`](https://owner.github.io/project/llms.txt)
- [`llms-full.txt`](https://owner.github.io/project/llms-full.txt)
- [`getting-started/index.md`](https://owner.github.io/project/getting-started/index.md)
```

Derive the prefix from `site_url`. On GitHub project Pages, do **not** use
`/llms.txt`: the leading slash resolves at `https://owner.github.io/` and drops
the `/project/` subpath.

Do not set `validation.links.not_found: info` for this. That setting demotes
every missing source-link warning, including real typos, and makes strict mode
unable to protect the rest of the docs. `validation.links.unrecognized_links`
also does not apply: build-output links are classified as `not_found`, not as
already-INFO unrecognized links.

If the site is multilingual, produce the deployable artifact with the managed
two-pass helper rather than a direct MkDocs build:

```bash
uv run python scripts/build-docs-site.py
```

That solves the separate `mkdocs-static-i18n` / `mkdocs-llmstxt` overwrite bug;
it does not change MkDocs' source-link validation rule.

## Prevention

- Use relative links for real source files inside `docs/`.
- Use full `site_url`-based URLs only for build-time-generated artifacts that
  cannot have a source counterpart.
- Keep `--strict` enabled and do not broadly demote `not_found`; a broken
  `*.md → *.md` link must still fail the build.
- For i18n sites, keep llmstxt disabled in direct builds and use
  `scripts/build-docs-site.py` for the complete strict artifact.

## Where this was hit

Commit `14a57a2` added a "For AI assistants" section to
`docs/index.md` linking to generated `/llms.txt`, `/llms-full.txt`, and raw
Markdown endpoints. The first attempted workaround demoted `not_found`, which
made the build green at the cost of masking unrelated broken links. The durable
fix is a full `site_url`-based link plus strict validation; the later i18n issue
also requires the separate two-pass build documented in
`mkdocs-i18n-llms-files-are-empty.md`.
