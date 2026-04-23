# Agent Skills

A personal collection of [agent skills](https://agentskills.io/home) — both custom-authored and cherry-picked from upstream repos — installable as a single package.

📚 **[Read the docs](https://daviddwlee84.github.io/agent-skills/)** for the full guide, conventions, and skill index.

## Install

<!-- snippet:install (keep in sync with docs/_snippets/install.md) -->
```bash
npx skills@latest add daviddwlee84/agent-skills/skills
```

> **Note**
> The trailing `/skills` matters. Without it, `npx skills` will look in
> `.agents/skills/` of the upstream repo, which contains a different
> layout. The `skills/` suffix points the installer at the
> `skills/local/` and `skills/vendor/` trees.
<!-- /snippet:install -->

## What's in here

- **`skills/local/`** — custom-authored skills.
  - [`project-knowledge-harness`](skills/local/project-knowledge-harness/) — TODO + backlog + pitfalls structure with init / kanban / promote / add-todo / sweep-inbox toolkit. ([docs](https://daviddwlee84.github.io/agent-skills/skills/project-knowledge-harness/))
  - [`quantatitive-factor-researcher`](skills/local/quantatitive-factor-researcher/) — Python quant-research persona. ([docs](https://daviddwlee84.github.io/agent-skills/skills/quantatitive-factor-researcher/))
  - [`skill-author`](skills/local/skill-author/) — Author new skills following [agentskills.io](https://agentskills.io/skill-creation/best-practices) best practices; ships `new-skill.sh` scaffolder and `lint-skill.sh` linter. ([docs](https://daviddwlee84.github.io/agent-skills/skills/skill-author/))
- **`skills/vendor/`** — third-party skills synced from upstream via [`vendor.yaml`](vendor.yaml).
  - [`marimo-notebook`](skills/vendor/marimo-notebook/) — from [marimo-team/skills](https://github.com/marimo-team/skills).

## Repo memory

This repo dogfoods `project-knowledge-harness` on itself:

- [`TODO.md`](TODO.md) — priority/effort-tagged backlog.
- [`backlog/`](backlog/) — research notes for `P?` items (when populated).
- [`backlog/inbox.md`](backlog/) — quick-capture inbox; sweep into `TODO.md` later.
- [`pitfalls/`](pitfalls/) — symptom-grep-able knowledge base of past traps (when populated).

```bash
# Validate TODO.md and render kanban-style board
make kanban

# Quick add structured TODO entry
./scripts/add-todo.sh --priority P3 --effort M --title "..." --description "..."

# Move an active TODO to ## Done in same commit as the implementation
./scripts/promote-todo.sh --title "<substring>" --summary "<shipped summary>"

# Triage backlog/inbox.md interactively
./scripts/sweep-inbox.sh
```

Full workflow: [Project memory](https://daviddwlee84.github.io/agent-skills/workflows/project-memory/).

## Vendor system

```bash
# Add a vendored skill (auto-syncs)
./scripts/add-vendor.sh owner/repo/path/to/skill
# or via Makefile
make add-vendor SOURCE=owner/repo/path/to/skill

# Sync all vendored skills from upstream
make sync

# Check for upstream updates (dry-run)
make sync-check
```

Full workflow: [Adding vendor skills](https://daviddwlee84.github.io/agent-skills/workflows/adding-vendor-skills/).

**Dependencies:** `gh` (GitHub CLI, authenticated) and `yq` (YAML processor).

## Docs site

The docs site is built with MkDocs Material + `mkdocs-llmstxt` + `mkdocs-copy-to-llm`.

```bash
uv sync --extra docs
make docs-serve         # http://127.0.0.1:8000/
make docs-build         # produces ./site/
```

Deployed automatically to GitHub Pages on push to `main` via [`.github/workflows/docs.yml`](.github/workflows/docs.yml).

If you want to apply the same docs stack to your own project, see [Downstream docs stack recipe](https://daviddwlee84.github.io/agent-skills/reference/docs-stack-recipe/).

## Adding a new local skill

Use the bundled scaffolder (recommended — seeds the agentskills.io best-practice template):

```bash
bash skills/local/skill-author/scripts/new-skill.sh <skill-name>
bash skills/local/skill-author/scripts/lint-skill.sh skills/local/<skill-name>
```

Or with the upstream init:

```bash
cd skills/local
npx skills@latest init [skill-name]
```

See [Creating local skills](https://daviddwlee84.github.io/agent-skills/workflows/creating-local-skills/) for the layout rules and authoring guidance.

## Resources

### Skills managers

- [vercel-labs/skills](https://github.com/vercel-labs/skills) — `npx skills` itself
  - [The Agent Skills Directory](https://skills.sh/)
- [Skill.Fish](https://www.skill.fish/) — alternative skill manager
  - [knoxgraeme/skillfish](https://github.com/knoxgraeme/skillfish)

### Curated skill collections

- [vercel-labs/agent-skills](https://github.com/vercel-labs/agent-skills/tree/main)
- [mattpocock/skills](https://github.com/mattpocock/skills)
- [anthropics/skills](https://github.com/anthropics/skills)
- [anthropics/knowledge-work-plugins](https://github.com/anthropics/knowledge-work-plugins/tree/main)
- [marimo-team/skills](https://github.com/marimo-team/skills)
- [streamlit/agent-skills](https://github.com/streamlit/agent-skills)
- [RKiding/Awesome-finance-skills](https://github.com/RKiding/Awesome-finance-skills)
- [Orchestra-Research/AI-Research-SKILLs](https://github.com/Orchestra-Research/AI-research-SKILLs)

### Articles

- [Building Agent Skills with skill-creator](https://medium.com/google-cloud/building-agent-skills-with-skill-creator-855f18e785cf)
- [Introducing: React Best Practices (Vercel)](https://vercel.com/blog/introducing-react-best-practices) — paired with [`react-best-practices`](https://github.com/vercel-labs/agent-skills/tree/main/skills/react-best-practices)
- [Six skills for financial service professionals (Claude)](https://claude.com/resources/tutorials/claude-for-financial-services-skills)

### Skill candidates

- [humanlayer/12-factor-agents](https://github.com/humanlayer/12-factor-agents)
- [The Twelve-Factor App](https://12factor.net/)
- [FrancyJGLisboa/agent-skill-creator](https://github.com/FrancyJGLisboa/agent-skill-creator)
- [find-skills (vercel-labs/skills)](https://skills.sh/vercel-labs/skills/find-skills)
