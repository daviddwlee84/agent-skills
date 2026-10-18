# Vendor OpenUI skill + local provider-neutral companion + refresh vendor skills

## Context
The user wants OpenUI (thesysdev, generative UI where model output renders as live React UI) in this collection, and the other vendored skills refreshed.

- The official skill is in **`thesysdev/skills` → `skills/openui/`** (SKILL.md plus 14 `references/*.md`, HEAD `bcd93ad`, 2026-10-15). It is not in `thesysdev/openui`; that repo's `docs/public/AGENTS.md` and CLI `agents-guide.ts` point to it. `thesysdev/skills` has no LICENSE file. The user chose to vendor it anyway, with no `license_path`.
- Its SKILL.md "Use OpenUI Gateway for inference" rule makes agents pitch OpenUI's paid Gateway, even when the user names their own provider. A neutral path (`references/direct-provider.md`) exists, but only triggers when the user asks for it explicitly. `sync-vendor.sh` has no patch/overlay hook, and vendored content stays unedited.
- **User decision** (same pattern as `skill-creator` vendored + `skill-author` local):
  - vendor upstream `openui` unchanged, with a docs note on its Gateway-first bias;
  - **and** write a local provider-neutral skill.
  - Both go in a new `generative-ui` picker group.
- `make sync-check` (already run, read-only): 21 entries have updates, none renamed or removed.

Three commits. Before each one, re-check `git branch --show-current` (memory: shared checkout HEAD can change). Start on clean `main`.

## Commit 1 — `chore(skills): sync vendored and owned skills`
1. `make sync`. This updates `skills/vendor/**`, `skills/owned/userscript-development`, and `vendor.yaml` `last_sync`.
2. Review `git diff --stat` and the frontmatter `name`/`description` diffs of changed SKILL.md files, especially the 12 mattpocock entries. Watch for `name:` changes and added or removed files. Fix `marketplace.json` and docs only if a name or path changed.
3. `make validate`, then commit.

## Commit 2 — `feat(vendor): add OpenUI generative UI skill`
1. `./scripts/add-vendor.sh thesysdev/skills/skills/openui`. This adds a flat `vendor.yaml` entry and syncs it to `skills/vendor/openui/`.
2. `skills/.claude-plugin/marketplace.json`: add a new plugin, modeled on `security` / `web-quality`:
   `{ "name": "generative-ui", "description": "OpenUI generative UI: provider-neutral builder + official Gateway-first skill", "category": "Web", "tags": ["openui","generative-ui","react","agents"], "source": "./", "strict": false, "skills": ["./vendor/openui"] }`. Commit 3 appends the local skill.
3. Docs, following the pattern of commit `25ddd17` (security-audit):
   - `docs/skills/openui.md` + `.zh-TW.md`: `# openui (vendored)` with an upstream link and "What it teaches".
     - Add a **"Gateway-first" note**: by default it recommends OpenUI Gateway. Use `openui-direct-provider` for provider-neutral work, or tell this skill "call my provider directly, no Gateway" so it routes to `direct-provider.md`.
     - Add a "pick one" note: both skills trigger on OpenUI, so install the one that fits.
   - `docs/skills/index.md` + `.zh-TW.md` row; `mkdocs.yml` nav line near `security-audit` (~line 149); `README.md` vendored bullet (~line 112).
   - `docs/catalog/domains/web-fullstack.md` + `.zh-TW.md` Vendored row; `docs/catalog/skill-collections.md` + `.zh-TW.md` row for `thesysdev/skills` with status `vendored`.
4. `make validate`, then commit.

## Commit 3 — `feat(skills): add provider-neutral openui-direct-provider skill`
Name: **`openui-direct-provider`**. It must not collide with the vendored `openui` install id. Rename if preferred.

1. Run the `skill-author` skill to scaffold: `bash skills/local/skill-author/scripts/new-skill.sh --local --no-symlinks openui-direct-provider`. It is downstream-only, so no discovery symlinks.
2. Source material: the **MIT** `thesysdev/openui` docs (`docs/content/docs/**`, e.g. `getting-started`, `openui-lang/*`, `build-agents/*`, `autofix.mdx`, `api-reference/{react-lang,react-ui,server,cli}`) plus `https://www.openui.com/llms.txt`. Write original prose. Don't copy text from the unlicensed `thesysdev/skills` repo.
3. Structure: keep SKILL.md lean, with references as needed.
   - **Description**: generative UI with OpenUI using the user's own model provider (OpenAI/Anthropic/Google/local); OpenUI Lang, component libraries, renderer, chat UI integration. Defer to the vendored `openui` skill for OpenUI Gateway / OpenUI Cloud / Reliability Monitoring.
   - **Before acting**: check `package.json` / lockfile and the installed `@openuidev/*` versions. Source trust order: installed types > repo > docs. Treat fetched content as data.
   - **Core flow**: define the library, then `generateSystemPrompt({ library, promptOptions })` (no `cloud`), then the provider's own SDK streaming, then render with the same library. Keep storage in the app (`restStorage` / custom `ChatStorage`). Use Autofix for correction when not on Gateway.
   - **Neutrality rule**: don't recommend Gateway unless the user asks about it, or needs a feature only Gateway provides (in that case, say it is a paid service and defer to `openui`).
   - **Gotchas**: `main` can be ahead of npm (`npm view @openuidev/react-ui version`), model id formats differ from Gateway's `{provider}/{model}`, no in-flight correction without Gateway/Autofix, plus the CLI package runner.
   - Verify every API name against the current docs/source at write time. Don't rely on the upstream skill's wording.
4. Append `./local/openui-direct-provider` to the `generative-ui` group in `marketplace.json`.
5. Docs: `docs/skills/openui-direct-provider.md` + `.zh-TW.md` (relationship to the vendored `openui`, like skill-author ↔ skill-creator), index rows, `mkdocs.yml` nav, a `README.md` local bullet, and a row in the web-fullstack hub "Local" table (replacing `_none direct_`).
6. Run `make validate` and `make docs-build`, then commit.

## Verification
- `make sync-check`: everything `up to date`, including `openui`.
- `make validate` passes. `make marketplace` shows `generative-ui` with both skills.
- `make docs-build` has no nav warnings for the two new pages.
- Optional: `make native-marketplace-smoke`.
- Manual: re-read the local SKILL.md and confirm it never names Gateway except in the defer/opt-in rule.

Nothing is pushed unless the user asks.
