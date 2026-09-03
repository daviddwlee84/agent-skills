# Downstream docs stack recipe

> This page is now maintained as part of the `mkdocs-site-bootstrap` skill.
>
> The full recipe lives in the skill's reference file:
> [`skills/local/mkdocs-site-bootstrap/references/docs-stack-recipe.md`](https://github.com/daviddwlee84/agent-skills/blob/main/skills/local/mkdocs-site-bootstrap/references/docs-stack-recipe.md)
>
> The skill also bundles ready-to-copy templates for `mkdocs.yml`,
> `pyproject.toml`, the GitHub Actions workflow, and a docs skeleton — see
> the skill's [`assets/`](https://github.com/daviddwlee84/agent-skills/tree/main/skills/local/mkdocs-site-bootstrap/assets)
> directory.

## Quick start

If your project doesn't yet use `mkdocs-site-bootstrap`, the easiest way to
apply the same docs stack is to invoke the skill in your repo:

```bash
# From your project's repo root
bash <path-to-agent-skills>/skills/local/mkdocs-site-bootstrap/scripts/init-docs-site.sh \
  --site-name "My Project" \
  --repo-slug owner/repo \
  --site-url https://owner.github.io/repo/
```

Then enable GitHub Pages and trigger the first deploy:

```bash
bash <path-to-agent-skills>/skills/local/mkdocs-site-bootstrap/scripts/enable-pages.sh \
  --repo owner/repo
```

Build the deployable artifact with the scaffolded strict helper:

```bash
uv sync --extra docs
uv run python scripts/build-docs-site.py
```

For multilingual sites with llmstxt this keeps the root files
default-language-only and builds locale HTML in a separate strict pass. Direct `mkdocs build
--strict` remains an HTML-only preview.

For details on what the stack actually includes (Material theme +
mkdocs-llmstxt + mkdocs-copy-to-llm + pymdownx.snippets), the linking rules
that strict mode enforces, and how the GitHub Actions workflow is wired,
read the canonical reference linked above.

Existing users should note that updating the installed skill does not migrate
their project. If an older i18n site has empty or wrong-locale llms output, use
the audit-first
[`migration guide`](https://github.com/daviddwlee84/agent-skills/blob/main/skills/local/mkdocs-site-bootstrap/references/i18n-llmstxt-migration.md).

## See also

- [Skill page: mkdocs-site-bootstrap](../skills/mkdocs-site-bootstrap.md) —
  detailed walkthrough of the full skill workflow including consent gates,
  preferences, and existing-docs handling.
- [Conventions](../conventions.md#documentation) — repo-specific rules that
  apply to *this* repo's `docs/` tree.
