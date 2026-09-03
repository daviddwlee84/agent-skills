# Bilingual / multi-language docs

How to add a non-English language (typically Traditional Chinese, `zh-TW`) to
a MkDocs Material site bootstrapped by this skill, and how to keep
terminology consistent so future contributors — human or agent — don't
introduce ambiguity.

## TL;DR

```bash
bash skills/local/mkdocs-site-bootstrap/scripts/add-language.sh --lang zh-TW
uv sync --extra docs
uv run python scripts/build-docs-site.py
```

The Material header gains a language switcher. The managed build helper keeps
both passes strict, publishes all locale HTML, and produces root `llms.txt`,
`llms-full.txt`, and `.md` sidecars from the default language only. Translate
the stub bodies when ready.

For local HTML preview, `uv run mkdocs serve` and direct `uv run mkdocs build
--strict` remain safe: the config disables `llmstxt` unless the helper enables
it. Use the helper for every artifact that will be deployed.

## Why `mkdocs-static-i18n` + suffix structure

[Squidfunk's recommended approach](https://github.com/squidfunk/mkdocs-material/discussions/2346)
for content translation is the
[`mkdocs-static-i18n`](https://github.com/ultrabug/mkdocs-static-i18n) plugin.
We use **`docs_structure: suffix`** rather than `folder` because:

- **Zero file moves on retrofit.** Existing `docs/index.md`,
  `docs/getting-started.md`, etc. stay where they are. The `folder` mode
  would force you to move every file into `docs/en/` first.
- **Relative links keep working.** Sibling files share the same directory.
- **Per-page opt-in to translation.** A page is only translated when
  `<page>.<lang>.md` exists; otherwise the plugin falls back to the default
  language (`fallback_to_default: true`).

The trade-off: directory listings get crowded once you have many languages.
For sites that grow to 5+ languages the `folder` structure starts to win on
readability — but you can migrate later.

## Terminology preservation rule (hard requirement)

This is the rule for any non-English page in a project that uses this skill:

> **在 zh-TW 頁面，技術名詞首次出現時，以「中文 (English original)」格式呈現。**
> 例：「依賴注入 (dependency injection)」、「型別檢查 (type checking)」。
> 後續同段內可只用中文。
>
> **不自創翻譯。** 若無公認譯名，直接保留英文（如 `embedding`、`tokenizer`、
> `mkdocs-static-i18n`、`pymdownx.snippets`）。
>
> **代碼、API 名、CLI flag、套件名、檔名一律不翻。**

The reason: Chinese-language tech writing has competing translations for
many terms (e.g. `cache` → 快取 / 緩存 / 暫存; `repository` → 倉庫 / 儲存庫 /
版本庫). Keeping the English original on first mention removes the ambiguity
without forcing readers to guess which translation the author meant. It also
keeps the page grep-able for English search terms.

`add-language.sh` and `add-docs-page.sh` inject this rule as an admonition
at the top of every non-default-language stub so authors see it before they
start translating.

## What `add-language.sh` does, step by step

For users who want to apply pieces by hand or audit what the script touched:

1. **Locates `mkdocs.yml`** by walking up from CWD.
2. **Detects existing i18n state.** `yq` query against `.plugins[]` checks
   for an `i18n:` map.
3. **Inserts or extends `plugins.i18n`.**
   - If absent: prepends a fresh i18n block before `search`, with
     `[default-lang, new-lang]` as the language list.
   - If present and the new locale isn't there: appends to
     `plugins[].i18n.languages`.
   - If the locale is already present: no-op.
4. **Sets `theme.language`** to the default language if not already set
   (`mkdocs-static-i18n` warns when `theme.language` is missing).
5. **Removes `navigation.instant` / `navigation.instant.progress`** from
   `theme.features` (the language switcher's contextual link can't be
   rewritten by instant navigation).
6. **Keeps default-language `mkdocs-llmstxt` output by default.** It adds the
   environment guards and managed `scripts/build-docs-site.py` required to
   isolate llmstxt from the multilingual build. Use `--remove-llmstxt` for an
   explicit opt-out. Legacy `--drop-strict` is a deprecated no-op;
   `--keep-llmstxt` is a deprecated alias for the default behavior.
7. **Walks `docs/`** for `*.md` files (excluding `_snippets/` and `assets/`),
   and for each non-locale-suffixed source page, creates a sibling
   `*.<LANG>.md` from `assets/translation-stub.md.template`.
8. **Updates `.skills/preferences.yaml`** with three keys:
   `mkdocs_site_bootstrap.languages` (ordered list, default first),
   `keep_english_terms: true`, `i18n_structure: suffix`.
9. **Un-comments `mkdocs-static-i18n>=1.2`** in `pyproject.toml`. If the
   line isn't there at all, prints a hint asking you to add it manually.

The script is idempotent: re-running with the same `--lang` is a no-op. Exit
`11` means the locale/stubs were added and the safe migration subset was
applied, but custom downstream files still need the manual actions reported by
`migrate-i18n-llmstxt.sh --json`.

## `theme.language` vs plugin `languages`

These are two different things:

- [`theme.language`](https://squidfunk.github.io/mkdocs-material/setup/changing-the-language/)
  is **Material's UI strings** (search placeholder, "Edit this page", footer
  navigation hints). One value site-wide. Material ships translations for
  ~70 locales out of the box.
- `plugins.i18n.languages` is **content translation**. A list. Each entry
  declares a locale that has translated `*.<lang>.md` files.

You almost always want `theme.language` set to your default content language
so the UI matches when readers land on a default-language page.

## `nav_translations`

To translate section titles in the nav (e.g. `Workflows` → `工作流程`), use
`mkdocs-static-i18n`'s per-language `nav_translations`:

```yaml
plugins:
  - i18n:
      docs_structure: suffix
      languages:
        - locale: en
          name: English
          default: true
        - locale: zh-TW
          name: 繁體中文 (zh-TW)
          nav_translations:
            Workflows: 工作流程
            Reference: 參考資料
```

`add-language.sh` does **not** populate `nav_translations` for you —
section names are project-specific and translating them is a deliberate
authorial choice. Add them by hand once you have section titles to translate.

!!! warning "Don't apply 「中文 (English original)」 to nav labels"
    The terminology rule that governs body prose **does not extend to
    `nav_translations` values.** Nav entries are navigation chrome — short
    labels in a sidebar — and bilingual labels like
    `Reference: 參考資料 (Reference)` are too long, wrap awkwardly, and
    duplicate information the URL slug already preserves.

    For nav labels: pick the most common Chinese term for each section
    and stick with it. Stay consistent across the whole nav. The URL
    slug still uses the English source name (`/zh-TW/reference/...`),
    so search engines and direct-link sharing are unaffected.

    Examples:

    | English heading | Good zh-TW label | Bad zh-TW label |
    |---|---|---|
    | `Reference` | `參考資料` | `參考資料 (Reference)` |
    | `Workflows` | `工作流程` | `工作流程 (Workflows)` |
    | `Skills` | `Skills` (keep — domain term, no canonical translation) | `技能 (Skills)` |
    | `Getting started` | `快速開始` | `快速開始 (Getting started)` |

    The "keep English" exception (third row) is reserved for terms where
    no canonical Chinese translation exists. When in doubt, keep English
    — it matches the body-prose rule's spirit (don't invent) without
    duplicating into the label.

## Interaction with `llmstxt` and `copy-to-llm`

### Why one multilingual build is unsafe

This is not merely a strict-mode compatibility warning, and
`reconfigure_material` is not the root cause:

1. `mkdocs-static-i18n` performs a full MkDocs build for each locale.
2. `mkdocs-llmstxt` resets its collected page state for each build.
3. Every locale writes the same root `llms.txt` and `llms-full.txt` paths.

The last locale therefore overwrites the valid default-language output. With
explicit `sections:` paths, translated source URIs no longer match and the
last files may contain only a heading. With globs, the files may look large but
contain the wrong locale. Strict mode exposes `Page URI ... not found`
warnings; a non-strict build silently ships the corrupted files. Removing
`--strict`, changing plugin order, toggling `reconfigure_material`, or using
globs does not solve the lifecycle collision.

### Canonical two-pass build

Run:

```bash
uv run python scripts/build-docs-site.py
```

For a multilingual site with llmstxt enabled, the helper:

1. Builds a temporary default-language-only source tree with i18n,
   copy-to-llm, and social disabled and llmstxt enabled.
2. Verifies `llms.txt`, the configured full output, every expected section,
   and generated `.md` sidecars.
3. Builds the full multilingual source tree with i18n/copy/social enabled and
   llmstxt disabled.
4. Merges the verified default-language LLM artifacts, rejects non-default
   locale paths, and only then replaces the final `site/` directory.

Both passes are strict. The helper has no non-strict escape hatch. A failed
pass leaves the previous `site/` untouched; use `--keep-temp` only when you
need to inspect the staged trees.

The corresponding `mkdocs.yml` guards are:

```yaml
docs_dir: !ENV [MKDOCS_SITE_BOOTSTRAP_DOCS_DIR, docs]

plugins:
  - i18n:
      enabled: !ENV [MKDOCS_SITE_BOOTSTRAP_I18N_ENABLED, true]
      # ...
  - llmstxt:
      enabled: !ENV [MKDOCS_SITE_BOOTSTRAP_LLMSTXT_ENABLED, false]
      # ...
  - copy-to-llm:
      enabled: !ENV [MKDOCS_SITE_BOOTSTRAP_COPY_TO_LLM_ENABLED, true]
      # ...
  - social:
      enabled: !ENV [MKDOCS_SITE_BOOTSTRAP_SOCIAL_ENABLED, true]
      # ... only when social cards were enabled
```

The default `false` for llmstxt is deliberate: direct `mkdocs serve` and
`mkdocs build --strict` are HTML-only and cannot accidentally overwrite the
canonical LLM artifact. CI and deploy workflows must invoke the helper.

### Output and copy-to-LLM contract

- Root `/llms.txt`, `/llms-full.txt`, and raw `.md` sidecars represent the
  **default language only**. This skill does not generate per-locale llms files.
- Keep Material's `content.action.edit` feature and a valid `repo_url` /
  `edit_uri`. The copy-to-LLM assets use the page's GitHub edit URL to derive
  the correct raw source, including a translated `*.zh-TW.md` sibling, instead
  of guessing from the locale site URL.
- `mkdocs-copy-to-llm` button labels remain English-only on non-English pages.
  This is cosmetic and does not affect the source selected by the button.

To opt out of LLM artifacts entirely:

```bash
bash scripts/add-language.sh --lang zh-TW --remove-llmstxt
```

Do not use `validation.links.not_found: info` or remove strict merely to make a
red build green. Fix source links and use a full deployed URL derived from
`site_url`, such as `https://owner.github.io/project/llms.txt`. A leading
`/llms.txt` is wrong for GitHub project Pages because it drops the repository
subpath.

- **The translation-stub admonition is zh-TW-specific.** The terminology
  rule it injects is written for Traditional Chinese and uses the
  「中文 (English original)」 format. If you add `--lang ja` or another
  language, the admonition still says "Terminology rule (ja pages)" but the
  body is in Chinese. Either edit
  `assets/translation-stub.md.template` to be language-neutral first, or
  hand-edit the stubs after creation.

## Removing a language

To remove `zh-TW` later:

1. Delete the `zh-TW` entry from `plugins[].i18n.languages` in `mkdocs.yml`.
2. (Optional) Delete every `*.zh-TW.md` file under `docs/`.
3. Update `.skills/preferences.yaml`:
   ```bash
   bash scripts/check-preferences.sh \
     --set 'mkdocs_site_bootstrap.languages=["en"]'
   ```
4. If you only had two languages and want to fully remove the plugin, also
   delete the `i18n:` block and re-comment `mkdocs-static-i18n` in
   `pyproject.toml`.

## Reset path

If you want to fully back out of all the i18n decisions and start over:

```bash
bash scripts/check-preferences.sh --reset mkdocs_site_bootstrap
# Then manually revert mkdocs.yml / pyproject.toml as above, and
# re-run init-docs-site.sh or add-language.sh from scratch.
```

The `--reset` clears the recorded decision; the agent will re-interview on
the next invocation.

## Future work — `i18n_structure: folder`

The `i18n_structure` preference key exists, but `add-language.sh` currently
only implements `suffix`. If we add `folder` later, the migration path will
be: walk `docs/`, move every default-language file into `docs/<default>/`,
move every `*.<lang>.md` into `docs/<lang>/<base>.md`, rewrite relative
links. Non-trivial — punted unless someone actually needs it.
