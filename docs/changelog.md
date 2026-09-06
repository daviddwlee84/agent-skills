# Changelog

This page summarizes notable changes. Day-to-day commit history lives in
[git log](https://github.com/daviddwlee84/agent-skills/commits/main); this
file curates the milestones.

## Unreleased

- Released `agent-history-hygiene` hook v2.0.1: scoped the upstream
  `sourcegraph-access-token` bare-40-hex false positive to agent artifacts while
  preserving real `sgp_...` detection, and advanced fresh bootstrap to gitleaks
  v8.30.1 so global `[[allowlists]]` / `targetRules` are actually applied.
- Bootstrapped a [MkDocs Material](https://squidfunk.github.io/mkdocs-material/)
  documentation site with `mkdocs-llmstxt` and `mkdocs-copy-to-llm`,
  deployable to GitHub Pages.
- Fixed `mkdocs-static-i18n` + `mkdocs-llmstxt` builds that could silently
  overwrite root llms files with an empty or wrong-locale final pass. New
  scaffolds use a strict two-pass `scripts/build-docs-site.py`; existing sites
  get an audit-first, idempotent migration tool. Updating the skill alone does
  not modify downstream projects.
- Added `scripts/add-todo.sh` for structured TODO inserts and
  `scripts/sweep-inbox.sh` for triaging loose captures from
  `backlog/inbox.md`. See [Project memory workflow](workflows/project-memory.md).
- Added [Downstream docs stack recipe](reference/docs-stack-recipe.md) so
  projects consuming our skills can mirror the same docs setup.

## 2026-04 — `project-knowledge-harness` restructure

- Loosened `scripts/todo-kanban.sh` validator to ignore prose,
  blockquotes, HTML comments, `---` rules, and indented sub-bullets.
  Added `--validate-only` and `--json` flags. Allowed extra `## ...`
  headings after `## Done`.
- Added `scripts/init.sh` for one-shot setup of `TODO.md` + `backlog/` +
  `pitfalls/` + agent-guidance + README snippet in any target repo.
- Added `scripts/promote-todo.sh` for atomic active-→-Done moves with
  re-validation and dry-run support.
- Slimmed `SKILL.md` (~350 → ~170 lines) and pushed detail into
  `references/{tag-schema,when-to-add-docs,anti-patterns,deployment-exclusion}.md`
  for [progressive disclosure](https://agentskills.io/specification#progressive-disclosure).

## 2026-03 and earlier

- Initial vendor system (`vendor.yaml`, `scripts/add-vendor.sh`,
  `scripts/sync-vendor.sh`, `make sync` / `make sync-check`).
- Initial `project-knowledge-harness` skill (formerly `backlog-harness`).
- `quantatitive-factor-researcher` persona skill.
