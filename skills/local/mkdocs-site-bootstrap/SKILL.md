---
name: mkdocs-site-bootstrap
description: Bootstrap a MkDocs Material documentation site for a repo and (optionally) deploy it to GitHub Pages — including pinned tooling via uv/PEP 723, a GitHub Actions workflow with paths-filter, llmstxt + copy-to-llm plugins so the site is LLM-friendly, and ongoing helper scripts to add new docs pages with auto-nav. Also handles bilingual / multi-language docs (English + zh-TW or others) via mkdocs-static-i18n with a "preserve English originals" terminology rule. Use whenever the user wants to "set up docs", "publish docs to GitHub Pages", "create a documentation site", "add an mkdocs site", "add Traditional Chinese", "雙語 docs", "i18n", "multilingual docs", "translate the docs", turn their README/markdown notes into a browsable site, or scaffold the same docs stack as this repo into a new project. Records opt-in/opt-out, stack choice, and language list in `.skills/preferences.yaml` so the agent doesn't re-ask on every session, and respects existing `docs/` content (detect + ask, never auto-migrate). For evaluating skill output quality use skill-creator; for authoring new skills use skill-author.
---

# mkdocs-site-bootstrap

Bootstrap and (optionally) deploy a MkDocs Material documentation site for a
repository, then keep helping the user add pages over time.

This skill is **consent-gated**. It records the user's preferences in
`.skills/preferences.yaml` and never repeats destructive actions without
asking. If the user changes their mind, `scripts/check-preferences.sh --reset
mkdocs_site_bootstrap` clears the recorded decision so the next invocation
starts fresh.

## When to trigger

- User asks to "set up docs", "create a docs site", "add a documentation
  site", "publish docs to GitHub Pages"
- User has loose markdown notes / a `docs/` directory and wants it browsable
- User wants the same docs stack as the `daviddwlee84/agent-skills` repo
  applied to a new project
- User says they want an LLM-friendly docs site (llms.txt, copy-to-LLM)
- User asks for "bilingual docs", "雙語 docs", "i18n", "multilingual",
  "add Traditional Chinese", "add zh-TW", "translate the docs", or to add
  any non-English language to an existing site → jump to step 7

## When NOT to trigger

- User just wants to write a single doc file → don't scaffold a whole site
- User explicitly opted out (preferences.yaml says `enabled: false`) → defer
  unless the user is now reversing that decision
- User wants to evaluate or benchmark a skill → use `skill-creator`
- User wants to author a new agent skill → use `skill-author`

## Workflow

### 1. Read preferences first

Before doing anything, check whether this repo already has a recorded
decision:

```bash
bash skills/local/mkdocs-site-bootstrap/scripts/check-preferences.sh \
  --get mkdocs_site_bootstrap
```

Possible states:

| State | Meaning | What to do |
|---|---|---|
| File doesn't exist or key missing | Never asked | Proceed to step 2 (interview) |
| `enabled: true, pages_deployed: true` | Site is live | Skip to step 6 (ongoing helpers) |
| `enabled: true, pages_deployed: false` | Bootstrapped but not deployed | Skip to step 5 (deploy) |
| `enabled: false` | User opted out | Confirm they want to reverse that, then `--reset` and re-run |

### 2. Interview (only if no recorded decision)

Ask the user explicitly:

1. "Do you want a MkDocs Material documentation site for this project?
   (yes / no / I'll think about it)"
2. If yes: "Should it auto-deploy to GitHub Pages on push to main?
   (yes / no — I'll deploy manually)"

Record both answers immediately so an interrupted session doesn't lose them:

```bash
bash skills/local/mkdocs-site-bootstrap/scripts/check-preferences.sh \
  --set mkdocs_site_bootstrap.enabled=true \
  --set mkdocs_site_bootstrap.stack=mkdocs-material \
  --set mkdocs_site_bootstrap.auto_deploy=true
```

If the user said no, record `enabled: false` and stop. Don't pester on
future invocations.

### 3. Detect existing docs (consent gate)

Before scaffolding, scan the target repo. Read
`references/existing-docs-handling.md` for the full decision tree, but
the short version:

- If `mkdocs.yml` already exists → report "looks like an mkdocs site already
  exists at <path>; not overwriting" and stop.
- If `docs/` exists and is non-empty → list the files, ask the user one of:
  (a) skip — leave my docs alone, just create `mkdocs.yml` pointing at them;
  (b) wrap — create `mkdocs.yml` with my files included as-is in the nav;
  (c) manual — let me reorganize first, then re-run.
- If neither exists → safe to scaffold from scratch.

Record the decision under `mkdocs_site_bootstrap.existing_docs_decision`.

### 4. Scaffold

Run `init-docs-site.sh`. It writes (or refuses to overwrite) `mkdocs.yml`,
`pyproject.toml` (with `[project.optional-dependencies] docs = […]`), the
`docs/` skeleton, `.github/workflows/docs.yml`, and stub assets for
copy-to-llm.

```bash
bash skills/local/mkdocs-site-bootstrap/scripts/init-docs-site.sh \
  --site-name "My Project" \
  --repo-slug owner/repo \
  --site-url https://owner.github.io/repo/
```

Use `--dry-run` first to preview. The script always preserves any existing
files unless `--force` is passed.

After scaffolding, run a local strict build to catch obvious issues:

```bash
uv sync --extra docs
uv run mkdocs build --strict
```

### 5. Enable Pages and trigger first deploy (consent gate)

This calls the GitHub API (`gh api -X POST .../pages -f build_type=workflow`)
and then triggers the workflow. **Always confirm with the user first** —
say exactly which API call you're about to make and which repo it'll affect.
Only proceed on explicit yes.

```bash
bash skills/local/mkdocs-site-bootstrap/scripts/enable-pages.sh \
  --repo owner/repo
```

Flags:
- `--dry-run` — print the `gh` calls without running them
- `--no-trigger` — enable Pages but don't run the workflow yet

After success, set `pages_deployed=true` and `pages_enabled_at=$(date +%F)`
in preferences.

### 6. Ongoing: add docs pages

For each new doc the user wants, use the helper instead of hand-editing
`mkdocs.yml`:

```bash
bash skills/local/mkdocs-site-bootstrap/scripts/add-docs-page.sh \
  --section workflows \
  --title "My new workflow" \
  --slug my-new-workflow
```

It creates `docs/<section>/<slug>.md` from the page template and inserts a
nav entry into `mkdocs.yml` under the matching section heading. Idempotent
— re-running with the same slug is a no-op.

If the project has additional languages configured in
`.skills/preferences.yaml` (`mkdocs_site_bootstrap.languages`), `add-docs-page.sh`
also generates `*.<LANG>.md` stubs for every non-default language, with the
terminology-rule admonition pre-injected. Use `--lang LANG` to add only the
translation for one specific language without re-creating the default.

### 7. Optional: add a non-English language

The skill supports bilingual / multi-language sites via the
`mkdocs-static-i18n` plugin (suffix layout: `index.md` + `index.zh-TW.md`).
This step is opt-in and decoupled from initial bootstrap.

Trigger: user asks for "bilingual docs", "雙語 docs", "add zh-TW", "i18n",
"add Traditional Chinese", "translate the docs", or similar.

Read `references/i18n-guide.md` first — it covers the **terminology
preservation rule** ("中文 (English original)" format on first mention; no
invented translations) which authors must follow on non-English pages.

Then run:

```bash
bash skills/local/mkdocs-site-bootstrap/scripts/add-language.sh --lang zh-TW
```

This inserts the i18n plugin into `mkdocs.yml`, creates `*.zh-TW.md` stub
siblings of every existing page (with the terminology admonition
pre-injected), uncomments `mkdocs-static-i18n` in `pyproject.toml`, and
records the choice in `.skills/preferences.yaml`. Idempotent — re-running
with the same `--lang` is a no-op.

After it runs, re-sync deps and rebuild:

```bash
uv sync --extra docs
uv run mkdocs build --strict
```

## Available scripts

- **`scripts/check-preferences.sh`** — Read, set, or reset
  `.skills/preferences.yaml`. Always-safe to run.
  - Flags: `--get KEY`, `--set KEY=VALUE` (repeatable), `--reset NAMESPACE`,
    `--list`, `--dry-run`, `--json`.
- **`scripts/init-docs-site.sh`** — Scaffold the site files.
  - Flags: `--site-name`, `--repo-slug`, `--site-url`, `--existing skip|wrap`,
    `--no-workflow`, `--dry-run`, `--force`.
- **`scripts/enable-pages.sh`** — Enable Pages and trigger first deploy via
  `gh api`. Requires `gh auth status` to pass first.
  - Flags: `--repo OWNER/REPO`, `--no-trigger`, `--dry-run`.
- **`scripts/add-docs-page.sh`** — Create a new page and insert it into
  `mkdocs.yml`'s nav. If multiple languages are configured, also writes
  `*.<LANG>.md` stubs for every non-default language.
  - Flags: `--section`, `--title`, `--slug`, `--template PATH`, `--lang LANG`
    (single-language stub only), `--dry-run`, `--force`.
- **`scripts/add-language.sh`** — Retrofit a non-default language into an
  existing site. Inserts `plugins.i18n`, creates `*.<LANG>.md` stubs with
  the terminology admonition, updates preferences, uncomments the static-i18n
  dep. Idempotent.
  - Flags: `--lang LANG` (required), `--name NAME`, `--default-lang LANG`,
    `--target-dir DIR`, `--no-stubs`, `--dry-run`, `--force`.

## Reference files

- `references/preferences-schema.md` — Schema for
  `.skills/preferences.yaml` and conventions for cross-skill use. Read this
  whenever you're touching a preferences key for the first time.
- `references/existing-docs-handling.md` — Full decision tree for handling
  user's pre-existing `docs/` content without surprises. Read this **before
  step 3** of every fresh bootstrap.
- `references/docs-stack-recipe.md` — Verbatim stack recipe (mkdocs.yml,
  pyproject.toml, workflow, linking rules). Useful when the user asks "what
  exactly is this stack?" or wants to apply pieces manually.
- `references/i18n-guide.md` — Bilingual / multi-language docs setup using
  `mkdocs-static-i18n`. Read this **before** running `add-language.sh`. Includes
  the verbatim "preserve English originals" terminology rule for zh-TW pages.

## Bundled assets

Templates the scripts copy from. Edit them here, not in the user's repo.

- `assets/mkdocs.yml.template` — Material theme + llmstxt + copy-to-llm
  plugins + pymdownx.snippets, parameterized with `{{SITE_NAME}}`,
  `{{REPO_SLUG}}`, `{{SITE_URL}}`.
- `assets/pyproject.toml.template` — Minimal `[project]` block + the docs
  optional-deps group.
- `assets/docs-workflow.yml.template` — `.github/workflows/docs.yml` with
  paths filter, uv setup, strict build, Pages deploy.
- `assets/docs-skeleton/` — `index.md`, `getting-started.md`, `_snippets/`
  examples, `assets/copy-to-llm/` JS+CSS files copied from this repo.
- `assets/page.md.template` — Used by `add-docs-page.sh`.
- `assets/translation-stub.md.template` — Stub used for non-default-language
  pages by `add-language.sh` and `add-docs-page.sh`. Contains the verbatim
  terminology-rule admonition.
- `assets/i18n-plugin.yml.snippet` — Reference YAML block for the
  `mkdocs-static-i18n` plugin (used by `references/i18n-guide.md`; the script
  builds the equivalent block via `yq`).

## Gotchas

- **MkDocs strict mode rejects relative `.md` links pointing outside
  `docs/`.** Inside `docs/` → relative is fine. Outside `docs/` for
  `.md` files (e.g., linking to repo `TODO.md`) → use absolute GitHub URL.
  Outside `docs/` for directories or non-`.md` (`backlog/`, `pyproject.toml`)
  → relative is downgraded to INFO and tolerated. Templates already do this
  right; don't "fix" the absolute URLs.
- **`pymdownx.snippets` requires `_snippets/` in `not_in_nav:`** or strict
  mode complains about pages-not-in-nav. Template handles it.
- **`gh api -X POST .../pages` is idempotent for `build_type=workflow`** but
  errors on `404 Not Found` if the repo isn't pushed to GitHub yet. Check
  `gh repo view` succeeds before running `enable-pages.sh`.
- **The Pages deploy workflow needs `permissions: pages: write,
  id-token: write`** at the workflow level. Template has it; if you copy
  pieces into an existing workflow, don't lose this.
- **`copy-to-llm` plugin's `repo_url` is the SITE URL, not the GitHub URL.**
  Counter-intuitive name.
- **Don't auto-migrate existing user docs.** Always ask. Migrating someone's
  hand-curated `docs/` into a new structure is a high-trust action that
  should be the user's explicit decision, not the agent's default.
- **`.skills/preferences.yaml` is per-repo, not global.** Don't write it to
  `~/.skills/` or `~/.config/`. Each repo has its own decisions.
- **`mkdocs-static-i18n` requires `theme.language` set to the *default*
  language code.** The plugin warns when it's missing. `add-language.sh`
  sets it on first run; if you copy pieces by hand, don't forget.
- **`docs_structure: suffix` only.** `add-language.sh` writes the suffix
  layout (`index.md` + `index.zh-TW.md` siblings); the `i18n_structure: folder`
  preference key is reserved but not implemented. Don't paste a `folder`
  config into `mkdocs.yml` and expect the script to keep it consistent.
- **`mkdocs-llmstxt` is incompatible with `mkdocs-static-i18n` under
  `--strict`.** llmstxt's `sections:` source-path lookups break after
  `reconfigure_material` remaps the page index. `add-language.sh` removes
  the entire llmstxt plugin entry from `mkdocs.yml` by default; pass
  `--keep-llmstxt` to preserve it (and drop `--strict` from CI). The dep
  stays in `pyproject.toml` either way.
- **`add-language.sh` removes `navigation.instant`** from `theme.features`
  because the language switcher's contextual link is incompatible with
  instant navigation. Material's plugin emits the warning itself; the script
  is just acting on it.
- **Don't translate technical terms in zh-TW pages without the English
  original.** The terminology rule (kept English in parens on first mention,
  no invented translations) is non-negotiable; the stub template injects
  the rule as an admonition so authors see it before they start.

## Updating an existing site (not bootstrapping)

If `mkdocs.yml` already exists, this skill mostly defers — only
`add-docs-page.sh` and `check-preferences.sh` are useful. Don't try to
"upgrade" the user's mkdocs.yml without an explicit ask; their config may
have customizations the templates don't know about.
