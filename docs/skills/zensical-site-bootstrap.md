# zensical-site-bootstrap

An English-only Zensical documentation pilot with safe initialization, locked
uv documentation dependencies, native LLM exports, and build-only CI.

[Canonical skill and helpers](https://github.com/daviddwlee84/agent-skills/tree/main/skills/local/zensical-site-bootstrap)

## What it provides

- Explicit-target dry runs and refusal to overwrite existing site configurations.
- Optional preservation of a reviewed `docs/` tree, without reorganizing content.
- Zensical 0.0.73 in a docs dependency group, not application runtime dependencies.
- Native `llms.txt`, `llms-full.txt`, Markdown exports, and Copy as Markdown.
- Mermaid fences and preview commands with configurable host/port.
- A project-owned checker for content coverage, copy targets, and Pages subpaths.
- Optional GitHub Actions build checks with no deployment permissions.

The first dogfood project is [ferry](https://github.com/daviddwlee84/ferry).
Generated files belong to the consuming project and do not depend on a checkout
of this skills repository.

## Scope limits

This is not a MkDocs migration tool or a multilingual fallback solution. For
English plus selected Traditional Chinese with missing-translation fallback,
continue using [mkdocs-site-bootstrap](mkdocs-site-bootstrap.md) until the
Zensical content-i18n contract has been verified. A language dropdown alone does
not implement it. Publishing to GitHub Pages requires separate approval.

## Installation

After the skill is available in the published catalog:

```bash
npx skills@latest add daviddwlee84/agent-skills/skills --skill zensical-site-bootstrap
```

Installing or updating the skill does not overwrite the consuming project's
docs, config, checker, or workflow. Review those changes explicitly when adopting
new template or builder versions.
