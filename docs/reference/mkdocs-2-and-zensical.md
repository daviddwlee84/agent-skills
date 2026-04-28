# MkDocs 2.0, Zensical, and the `mkdocs<2` cap

> This page is now maintained as part of the `mkdocs-site-bootstrap` skill.
>
> The full rationale and re-evaluation criteria live in the skill's
> reference file:
> [`skills/local/mkdocs-site-bootstrap/references/mkdocs-2-and-zensical.md`](https://github.com/daviddwlee84/agent-skills/blob/main/skills/local/mkdocs-site-bootstrap/references/mkdocs-2-and-zensical.md)

## Why this exists

This repo's [`pyproject.toml`](https://github.com/daviddwlee84/agent-skills/blob/main/pyproject.toml)
caps `mkdocs<2` and `mkdocs-material<10`. So does the `pyproject.toml.template`
that `mkdocs-site-bootstrap` writes into downstream projects. That cap is
deliberate, not bit-rot.

In one paragraph: MkDocs 2.0 removes the entire plugin system, so every
plugin in this docs stack (`mkdocs-llmstxt`, `mkdocs-static-i18n`,
`mkdocs-copy-to-llm`) stops working under 2.x. The Material for MkDocs
team has refused to follow MkDocs 2.0 and is shipping a separate
replacement called Zensical, positioned as a drop-in for **1.x**, not 2.0.
Until Zensical reaches stable release with i18n + LLM-friendly output, the
realistic answer is "stay on MkDocs 1.x." The canonical reference linked
above documents the exact re-evaluation criteria.

## See also

- [Downstream docs stack recipe](docs-stack-recipe.md) — full stack
  description (what the cap is protecting).
- [Skill page: mkdocs-site-bootstrap](../skills/mkdocs-site-bootstrap.md) —
  the skill that owns the templates and references.
