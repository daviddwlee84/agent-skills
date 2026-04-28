# Plan — Bilingual docs (zh-TW) support for `mkdocs-site-bootstrap`

## Context

**Why this change.** The `mkdocs-site-bootstrap` skill currently scaffolds a
mono-lingual MkDocs Material site. The user (a zh-TW speaker working primarily in
English) wants to be able to publish the same docs in Traditional Chinese, but
keep the choice opt-in: most projects start English-only, and a language can be
added later without re-scaffolding. There is also a hard preference about
**terminology** in Chinese pages: technical terms must keep their English
originals (no invented translations), so future writers — human or agent —
don't introduce ambiguity.

**Reference upstream.** Material for MkDocs covers two concerns separately:
[`theme.language`](https://squidfunk.github.io/mkdocs-material/setup/changing-the-language/)
configures UI strings (single value), while content translation is handled by
the [`mkdocs-static-i18n`](https://github.com/squidfunk/mkdocs-material/discussions/2346)
plugin. We use both.

**Decisions already made (this session):**

- **Approach A — retrofit, not bake-in.** `init-docs-site.sh` stays English-only.
  A new `add-language.sh` does the i18n retrofit. Trade-off: bilingual users run
  one extra script. Win: base template, base CI, base `llms.txt` config stay
  unchanged for the 90% of users who only want English.
- **`docs_structure: suffix`** — translated files are siblings (`index.md` +
  `index.zh-TW.md`), not parallel trees. Retrofit needs **zero file moves** to
  existing English content; relative links inside `docs/` keep working.
- **Default language code: `en`.** Matches Material's own examples and
  `mkdocs-static-i18n` defaults.

**Intended outcome.** After this change, a user can:

1. Run `init-docs-site.sh` and get an English-only site (unchanged behaviour).
2. Later run `add-language.sh --lang zh-TW` to retrofit i18n: the script
   inserts the `i18n` plugin block into `mkdocs.yml`, creates stub
   `*.zh-TW.md` siblings of every existing default-language page, and records
   the choice in `.skills/preferences.yaml`.
3. Run `add-docs-page.sh --section X --title Y` and — if any non-default
   languages are configured — get parallel stubs with the terminology-rule
   admonition pre-injected at the top of each non-default-language stub.

## Approach summary (Approach A)

Add a single new script (`add-language.sh`), one new reference doc
(`references/i18n-guide.md`), three small `assets/` template additions, two
new preference keys, and minor edits to `add-docs-page.sh` + SKILL.md. The
existing `init-docs-site.sh`, `mkdocs.yml.template`, and
`docs-workflow.yml.template` are **not** modified — keeping the
English-only path byte-for-byte unchanged.

## Files to create

### 1. `skills/local/mkdocs-site-bootstrap/scripts/add-language.sh` (new)

Idempotent retrofit script. Bash 3.2 compatible. Same conventions as the other
scripts in `scripts/` (set -euo pipefail, `--dry-run`, `--help`, structured JSON
on success, `log()`/`die()` helpers).

**CLI surface:**

```text
add-language.sh --lang LANG [OPTIONS]

Required:
  --lang LANG          Language code to add (e.g. zh-TW, ja, fr).

Options:
  --name NAME          Display name (default: derived from LANG, e.g. zh-TW → "繁體中文 (zh-TW)").
  --default-lang LANG  Override default language (default: en, must already be the existing site's language).
  --target-dir DIR     Repo root (default: walk up from CWD looking for mkdocs.yml).
  --no-stubs           Skip creating *.LANG.md sibling stubs for existing pages.
  --dry-run            Print actions without writing.
  --force              Overwrite existing stubs (default: skip existing).
  --help, -h
```

**What it does (in order, all idempotent):**

1. **Locate `mkdocs.yml`** by walking up from CWD (mirror logic in
   `add-docs-page.sh:77-84`). Fail fast if missing.
2. **Detect existing i18n state.** If `.plugins[].i18n` already exists, read
   the current `languages:` list and merge the new lang in (no-op if already
   present). Otherwise insert a fresh `plugins.i18n` block before `plugins.search`.
3. **Set `theme.language`** to the default language if not already set
   (`mkdocs-static-i18n` requires this).
4. **Insert `pymdownx.snippets` `not_in_nav` entry** for `*.<LANG>.md` if
   needed — actually not needed with `suffix` structure; `mkdocs-static-i18n`
   handles nav routing per language. Document this in the i18n guide.
5. **Create stub `*.<LANG>.md` siblings** for every existing markdown file
   under `docs/` (excluding `_snippets/` and `assets/`). Each stub:
   - Copies title from the source page (`# <Title>` first line).
   - Prepends the **terminology-rule admonition** (if `LANG != default`).
   - Contains a `!!! warning "Translation pending"` body so it's obviously a
     stub at render time.
6. **Update preferences:**
   ```bash
   check-preferences.sh \
     --set "mkdocs_site_bootstrap.languages=[en, zh-TW]" \
     --set "mkdocs_site_bootstrap.keep_english_terms=true" \
     --set "mkdocs_site_bootstrap.i18n_structure=suffix"
   ```
7. **Print structured success JSON:**
   `{"lang":"zh-TW","stubs_created":N,"existing":M,"languages":["en","zh-TW"]}`.

**Exit codes:** 0 success, 1 invalid args, 2 mkdocs.yml not found, 3 refusing
to overwrite, 4 yq error.

**Reuses:**
- `yq` invocation pattern from `add-docs-page.sh:137-150` (same atomic `.tmp.$$`
  → `mv` write).
- `check-preferences.sh` for the preference writes (already supports nested
  arrays per Explore-agent finding: `--set "key=[en, zh-TW]"`).
- `log()`/`die()` helpers — copy verbatim from `add-language.sh` siblings.

### 2. `skills/local/mkdocs-site-bootstrap/references/i18n-guide.md` (new)

~150 lines. Sections:

1. **TL;DR** — `add-language.sh --lang zh-TW`, what it touches, where to write
   the actual translation.
2. **Why `mkdocs-static-i18n` + suffix structure** — what we picked and why
   (no file moves for retrofit; relative links still work; per-page opt-in to
   translation).
3. **Terminology preservation rule (hard requirement).** Verbatim:
   > 在 zh-TW 頁面，技術名詞**首次出現時**以「中文 (English original)」格式呈現，
   > 例如：「依賴注入 (dependency injection)」；後續同段內可僅用中文。
   > **不自創翻譯**——若無公認譯名，直接保留英文（如 `embedding`、`tokenizer`、
   > `mkdocs-static-i18n`）。代碼、API 名、CLI flag、套件名、檔名一律不翻。
4. **What `add-language.sh` does** — step-by-step mirror of the script flow,
   for users who want to do it by hand.
5. **`theme.language` vs plugin `languages`** — the two are different; show
   both.
6. **`nav_translations`** — how to translate section titles (lives under the
   plugin's per-language config).
7. **Interaction with `llmstxt` and `copy-to-llm`:** explicit notes —
   - `llmstxt` will pick up all `.md` files including `*.zh-TW.md`. If you want
     per-language `llms.txt`, drop `llmstxt` for zh-TW (the plugin doesn't
     support per-language sections out of the box) — document as a known limit.
   - `copy-to-llm` button text is currently English-only; translation requires
     a separate config and is out of scope for this retrofit.
8. **Removing a language** — `mkdocs-static-i18n` graceful-removal recipe
   (delete the plugin entry, optionally delete the `*.<LANG>.md` files).
9. **Reset path** — `check-preferences.sh --reset mkdocs_site_bootstrap` if the
   user wants to start over.

### 3. `skills/local/mkdocs-site-bootstrap/assets/translation-stub.md.template` (new)

Used by `add-language.sh` step 5 when generating stub siblings. Body:

```markdown
# {{PAGE_TITLE}}

!!! note "Terminology rule (zh-TW pages)"
    技術名詞首次出現以「中文 (English original)」格式呈現，例：依賴注入
    (dependency injection)。**不自創翻譯**；代碼/API/CLI/套件名一律不翻。
    完整規則：see [i18n guide]({{I18N_GUIDE_URL}}).

!!! warning "Translation pending"
    這個頁面尚未翻譯。原文：[{{PAGE_TITLE}}]({{SOURCE_PAGE}})
```

The admonition only renders for non-default languages — the script knows
because it's only invoked for non-default-language stubs.

### 4. `skills/local/mkdocs-site-bootstrap/assets/i18n-plugin.yml.snippet` (new)

The exact YAML block to inject into `mkdocs.yml` under `plugins:`. Used by
`add-language.sh` step 2. Stored as a snippet rather than inlined in the script
so it's diff-friendly and reusable from `references/i18n-guide.md` via
`pymdownx.snippets`.

```yaml
- i18n:
    docs_structure: suffix
    fallback_to_default: true
    reconfigure_material: true
    reconfigure_search: true
    languages:
      - locale: en
        name: English
        default: true
      - locale: zh-TW
        name: 繁體中文 (zh-TW)
```

## Files to modify

### 5. `skills/local/mkdocs-site-bootstrap/scripts/add-docs-page.sh`

Two small additions:

- **Read `languages` preference at start.** If >1 language configured, after
  creating the default-language page, also create `*.<LANG>.md` siblings for
  each non-default language using `assets/translation-stub.md.template`.
- **New flag `--lang LANG`** to create only one specific language's page (used
  when an author has just finished translating one specific page and wants to
  add a *new* page in zh-TW only — rare but cheap to support). Default
  behaviour: create the default-language page + stubs for all configured
  non-default languages.
- **Idempotency check** already greps for `$REL_PATH`
  (line 127) — extend to also check the language-suffixed paths.

No change to nav-insertion logic: `mkdocs-static-i18n` reuses the single nav
across languages; the `*.zh-TW.md` siblings are auto-discovered by the plugin
without nav entries.

### 6. `skills/local/mkdocs-site-bootstrap/SKILL.md`

- Add **trigger phrases** to the workflow: "add Traditional Chinese",
  "雙語 docs", "i18n", "multilingual", "zh-TW", "translate the docs".
- Add a new section **"Adding a non-English language"** after section 6
  ("Ongoing: add docs pages") covering the `add-language.sh` flow at the same
  level of detail as the existing sections.
- Reference the new `references/i18n-guide.md` in the "Reference files" list.
- Add `add-language.sh` to the "Available scripts" list with its full flag
  surface.
- One **gotcha** entry:
  > **`mkdocs-static-i18n` requires `theme.language` set to the *default*
  > language code.** The plugin will warn if it's missing. `add-language.sh`
  > sets it; if you copy pieces by hand, don't forget.

### 7. `skills/local/mkdocs-site-bootstrap/references/preferences-schema.md`

Document the three new keys under `mkdocs_site_bootstrap`:

```yaml
languages: [en, zh-TW]          # ordered list; first is default
keep_english_terms: true         # injects terminology admonition into non-default stubs
i18n_structure: suffix           # suffix | folder (currently only suffix supported)
```

Note that `i18n_structure: folder` is **reserved but not implemented** — record
in schema doc so future work doesn't conflict.

### 8. `skills/local/mkdocs-site-bootstrap/assets/pyproject.toml.template`

Add `mkdocs-static-i18n>=1.2` to the `docs` optional-deps group, but commented
out by default:

```toml
docs = [
  "mkdocs>=1.6",
  "mkdocs-material>=9.5",
  # Uncomment when you add a non-default language via add-language.sh:
  # "mkdocs-static-i18n>=1.2",
  "mkdocs-llmstxt>=0.2",
  "mkdocs-copy-to-llm>=0.1",
  "pymdown-extensions>=10.7",
]
```

`add-language.sh` un-comments the line on first run (idempotent grep + sed).

## Files explicitly NOT modified

- `scripts/init-docs-site.sh` — bilingual is a separate step, not part of init.
- `assets/mkdocs.yml.template` — base template stays English-only.
- `assets/docs-workflow.yml.template` — `docs/**` paths filter already covers
  `*.zh-TW.md` siblings; no CI change needed.
- `assets/docs-skeleton/index.md`, `getting-started.md` — only become bilingual
  if `add-language.sh` is run; the skeleton itself stays English-only.
- `references/existing-docs-handling.md` — i18n retrofit is a separate decision
  tree, lives in `i18n-guide.md`.

## Critical files (paths quick-reference)

| Path | Action |
|---|---|
| `skills/local/mkdocs-site-bootstrap/scripts/add-language.sh` | **CREATE** |
| `skills/local/mkdocs-site-bootstrap/scripts/add-docs-page.sh` | EDIT (multilang stubs) |
| `skills/local/mkdocs-site-bootstrap/references/i18n-guide.md` | **CREATE** |
| `skills/local/mkdocs-site-bootstrap/references/preferences-schema.md` | EDIT (3 new keys) |
| `skills/local/mkdocs-site-bootstrap/assets/translation-stub.md.template` | **CREATE** |
| `skills/local/mkdocs-site-bootstrap/assets/i18n-plugin.yml.snippet` | **CREATE** |
| `skills/local/mkdocs-site-bootstrap/assets/pyproject.toml.template` | EDIT (commented dep) |
| `skills/local/mkdocs-site-bootstrap/SKILL.md` | EDIT (trigger phrases, new section, gotcha) |

## Verification

End-to-end smoke test in a throwaway directory:

```bash
# 1. Bootstrap an English-only site (regression: should behave as before).
mkdir /tmp/i18n-smoke && cd /tmp/i18n-smoke && git init
bash skills/local/mkdocs-site-bootstrap/scripts/init-docs-site.sh \
  --site-name "Smoke" --site-url "https://x.io/" --repo-slug a/b
uv sync --extra docs
uv run mkdocs build --strict   # should pass — base template untouched

# 2. Retrofit zh-TW.
bash skills/local/mkdocs-site-bootstrap/scripts/add-language.sh \
  --lang zh-TW --dry-run        # preview
bash skills/local/mkdocs-site-bootstrap/scripts/add-language.sh --lang zh-TW
# Expect: mkdocs.yml gains plugins.i18n block, *.zh-TW.md stubs appear,
# pyproject.toml uncomments mkdocs-static-i18n, preferences.yaml updated.

# 3. Re-sync deps and rebuild — must still pass --strict.
uv sync --extra docs
uv run mkdocs build --strict

# 4. Idempotency.
bash skills/local/mkdocs-site-bootstrap/scripts/add-language.sh --lang zh-TW
# Expect: "language already configured; 0 stubs created"

# 5. add-docs-page now creates parallel stubs.
bash skills/local/mkdocs-site-bootstrap/scripts/add-docs-page.sh \
  --section _root --title "About" --slug about
ls docs/about.md docs/about.zh-TW.md   # both exist
grep "Terminology rule" docs/about.zh-TW.md   # admonition injected

# 6. Local serve and eyeball language switcher.
uv run mkdocs serve   # check the language toggle in the Material header
```

Plus three quick checks against the skill itself:

- Run `bash scripts/add-language.sh --help` and confirm the help text matches
  the documented flags.
- `grep -n "mkdocs-static-i18n" skills/local/mkdocs-site-bootstrap/` returns hits
  in `i18n-guide.md`, `add-language.sh`, `pyproject.toml.template`, and
  `preferences-schema.md`.
- The repo's own `make docs-build` still works (sanity: we didn't accidentally
  break the agent-skills repo's own docs by touching shared assets).

## Known limitations / explicit non-goals

- **`folder` structure not implemented.** Only `suffix`. Schema reserves the
  key for future work. Document this in `i18n-guide.md`.
- **No automatic translation.** Stubs contain a "Translation pending" warning
  admonition. Authors fill them in by hand.
- **`llmstxt` per-language not solved.** Documented as a known limit; for
  zh-TW pages, the per-page copy-to-LLM still works but `/llms.txt` will be
  English-centric. Acceptable for v1.
- **`copy-to-llm` button text not localised.** Out of scope.
- **UI strings beyond `theme.language`** (e.g. site footer, search
  placeholder) come from Material's translations. We rely on upstream's zh-TW
  catalog being adequate; if the user finds gaps, that's a Material upstream
  issue, not this skill's.
