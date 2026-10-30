# MkDocs 2.0, Zensical, and why this stack pins `mkdocs<2`

Last verified: **2026-10-30** against upstream documentation and release notes.
This replaces the April 2026 assessment. Upstream support below is not a claim
that this skill's sites have been built or migrated with Zensical.

## TL;DR

- **Keep this skill and existing MkDocs sites.** Preserve `mkdocs>=1.6,<2`,
  `mkdocs-material>=9.5,<10`, the lockfile, and the managed build helper.
- **English-first with optional Traditional Chinese is content i18n**, not
  just a translated interface. Continue using MkDocs for that workflow until
  a successor passes the same output checks.
- **Zensical is a viable candidate for a scoped single-language pilot**, not
  an automatic default for every new project. Its `0.x` version alone is
  neither a reason to reject it nor evidence of production readiness.
- **Material maintenance ends on 2027-05-05** for security and critical fixes,
  per its [changelog](https://squidfunk.github.io/mkdocs-material/changelog/).
  Staying on MkDocs is a time-bounded decision, not a promise of years of support.
- A future `zensical-site-bootstrap` should be a **separate skill**. Updating
  this skill must not silently change downstream projects' build engine.

## What changes in MkDocs 2.0

The [MkDocs announcement](https://github.com/mkdocs/mkdocs/discussions/4077)
links to [version 2 pre-release documentation](https://www.encode.io/mkdocs/).
The Material team's [analysis, updated in October 2026](https://squidfunk.github.io/mkdocs-material/blog/2026/02/18/mkdocs-2.0/),
reports removal of the MkDocs 1.x plugin system, a rewritten theme interface,
and TOML configuration. It states that Material is incompatible and that no
release date has been announced. Treat these as pre-release design statements,
not a guarantee that the final design cannot change.

`mkdocs-llmstxt`, `mkdocs-static-i18n`, and `mkdocs-copy-to-llm` depend on the
MkDocs plugin lifecycle. **PyMdown's snippets, superfences, and tabs are Python
Markdown extensions, not MkDocs plugins**; assess Markdown compatibility
separately rather than claiming every extension has the same failure mode.

Do not upgrade this Material-based stack to MkDocs 2.0 without a separately
validated migration. There is no need to adopt a different hosting provider:
GitHub Actions can build the static output before GitHub Pages serves it.

## What Zensical supports now

The latest release at verification was
[0.0.73 (2026-10-26)](https://github.com/zensical/zensical/releases/tag/v0.0.73).
[0.0.67 (2026-09-30)](https://github.com/zensical/zensical/releases/tag/v0.0.67)
added native `llmstxt` and a Copy as Markdown button. The old assessment that
there was no published support for these functions is obsolete.

The [plugin compatibility table](https://zensical.org/docs/compatibility/mkdocs/plugins/)
is the authority for individual settings, not the presence of a plugin name in
`mkdocs.yml`:

| Requirement | Upstream status and limits |
|---|---|
| Existing `mkdocs.yml` / Material look | Supported migration path; `theme.variant: classic` preserves the familiar appearance. Custom template overrides may need changes. |
| Search / Python API reference | Native search and `mkdocstrings` integration are documented. Install the required handler; audit companion plugins separately. |
| `llms.txt`, full output, Markdown counterparts | Native `llmstxt` since 0.0.67. Validate sections, exported content, and project Pages subpaths. Custom Python `preprocess` is ignored. |
| Copy as Markdown | `content.action.copy` works for pages with Markdown counterparts. This is not proof of parity with every `mkdocs-copy-to-llm` button or custom asset. |
| UI language / alternate-language links | Documented, but not proof of suffix content translation, fallback, contextual switching, translated nav, or per-language search. |
| Arbitrary MkDocs plugins / hooks | No MkDocs plugin API; arbitrary plugins cannot run. The migration guide lists `hooks` as unsupported. |
| `gen-files` | Not supported directly; external generation is a separate workflow to evaluate. |

**Unsupported plugin configuration can be silently ignored.** A successful
build is insufficient: inspect the artifacts and user-visible behavior.
Likewise, supported plugins may have ignored settings. Check every setting
used by the target site, not just the package list.

The [migration guide](https://zensical.org/docs/compatibility/mkdocs/migration/)
does not require conversion to `zensical.toml` just to test an existing config.
It also documents CLI and template differences; replacing `mkdocs` with
`zensical` in the managed helper is not a migration strategy.

Do not treat an unverified future release date as an adoption gate. In
particular, the roadmap's November 5 Studio banner is not evidence for a
November 5, 2026 release of the SSG as version 0.1.0.

## English-first with optional Traditional Chinese

Distinguish three layers:

1. **UI localization** translates search labels and navigation controls.
2. **A language selector** links to language-specific destinations; it does
   not generate translated documents.
3. **Content i18n** maps corresponding articles, handles missing translations,
   and builds appropriate navigation and search for each locale.

For this workflow, English is the complete default source for readers and
agents. Add `*.zh-TW.md` only for articles the user wants in Traditional Chinese;
missing translations should fall back to English. Root `llms.txt`,
`llms-full.txt`, and Markdown sidecars remain default-language-only. Enabling
a locale never authorizes automatic translation.

MkDocs' `fallback_to_default: true` supports missing siblings, but an existing
"Translation pending" stub counts as a translation and masks the fallback.
**`add-language.sh --no-stubs` already enables a locale without generating
siblings.** That flag is per-invocation, not a persistent preference:
`add-docs-page.sh` still creates stubs for configured non-default languages.
Read [the i18n guide](i18n-guide.md#english-first-with-selective-translations)
before choosing this workflow; do not invent a persistent on-demand flag.

Zensical's [language settings](https://zensical.org/docs/setup/language/)
document UI localization and alternate links. The [roadmap](https://zensical.org/roadmap/)
still lists broader content-i18n work. Neither establishes parity with this
skill's suffix/fallback workflow. Do not replace it with a hand-built multi-site
pipeline merely to claim that language switching exists.

## Keep the caps; validate migrations separately

Material 9.7.5+ also constrains MkDocs below 2. A resolver intersects that
constraint with the project's direct requirements; the direct MkDocs dependency
is **not** resolved independently. Explicit bounds still document this skill's
own support contract and remain protective if upstream metadata changes.

Keep bounds consistent in the dependency template, optional social extra,
manual recipe, and initializer's existing-`pyproject.toml` hints. Commit a
lockfile in consuming projects and use controlled patch/minor updates with
regression tests. Bounds permit those updates; they do not refresh a lockfile
or supply security fixes automatically.

**Migrating to Zensical does not mean lifting the MkDocs cap.** Change the
builder and dependencies deliberately for each approved migration; retain the
caps wherever the MkDocs/Material stack remains in use.

## Re-evaluation and adoption gates

Review again by **January 2027**, ahead of Material's maintenance deadline,
or sooner after relevant security advisories or new content-i18n support.
This is a review recommendation, not an automatically scheduled task.

Before a pilot becomes a default or an existing site is migrated:

1. Inventory plugins, hooks, extensions, templates, and build-time generators.
   Record unsupported or unknown settings instead of accepting silent omission.
2. Build an isolated, version-locked fixture. Compare navigation, search,
   code blocks/snippets, images, anchors, and project Pages subpath links.
3. Verify `llms.txt` sections, full content, Markdown counterparts, and the
   actual Copy as Markdown behavior, not just file existence or exit status.
4. For content-i18n sites, verify English defaults, selected zh-TW counterparts,
   missing-translation fallback, same-page switching, locale navigation/search,
   correct source links, and default-language-only LLM artifacts.
5. Preserve sources and the last successful output on failure. Document rollback
   and get consent before switching an existing project or deploying anything.

A single-language pilot can validate steps 1–3 without solving i18n, but that
result does **not** make it the default for English-first bilingual projects.
Keep this skill's two-pass build and repair tools until an equivalent migration
has passed all applicable gates; do not copy that MkDocs-specific machinery into
a new Zensical skill.
